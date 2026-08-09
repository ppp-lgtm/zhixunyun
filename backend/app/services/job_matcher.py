"""
知训云 · 岗位匹配核心算法（计划书 2.1.4 规格）

纯函数模块，不依赖 DB Session，方便直接单元测试。
如需接入数据库，请在 router 层先把 ORM 对象转换成 dict/list，
再调用本模块函数。

使用示例：
    from app.services.job_matcher import calculate_job_match, get_student_weighted_avg

    # 1. 算学生加权历史均分（维度级）
    dim_scores = get_student_weighted_avg(student_eval_list, last_n=5, decay=0.8)
    # → {"代码质量": 87.0, "功能完整性": 82.0, ...}

    # 2. 算某个学生-岗位的匹配分
    result = calculate_job_match(
        student_scores=dim_scores,
        skill_requirements=[{"name":"代码质量","weight":30,"threshold":70,"must":True}, ...],
    )
    # → {"match_score": 86.5, "highlights": [...], "gaps": [...],
    #    "radar": {...}, "dimension_breakdown": [...]}
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Iterable, Any


# ============================================================
# 辅助函数
# ============================================================

def _to_float(v, default=0.0) -> float:
    try:
        if v is None:
            return float(default)
        return float(v)
    except (TypeError, ValueError):
        return float(default)


def _evaluations_sort_key(ev: Any):
    """按 created_at 倒排（支持 dict / ORM 对象两种形式）。None 排在最后。"""
    t = None
    if isinstance(ev, dict):
        t = ev.get("created_at")
    else:
        t = getattr(ev, "created_at", None)
    if t is None:
        return (0, 0)
    # datetime / ISO string 都能比较
    try:
        return (1, t.timestamp()) if hasattr(t, "timestamp") else (1, str(t))
    except Exception:
        return (1, str(t))


# ============================================================
# 核心 1：get_student_weighted_avg
# ============================================================

def get_student_weighted_avg(
    evaluations: Iterable[Any],
    last_n: int = 5,
    decay: float = 0.8,
    prefer_evaluator: str = "teacher",
) -> Dict[str, float]:
    """
    取学生最近 last_n 条评价，按时间倒排加权平均（越新越重，首条 1.0, 次条 decay, 再次 decay²…）

    - evaluations：学生的历史评价列表（每个元素是 Evaluations 表 ORM 或 dict）。
        dimension_scores 支持两种格式：
          1) JSON 对象（旧格式）：{"代码质量": 85, "功能完整性": 72}
          2) JSON 数组（新格式 A3）：[{"name":"代码质量","score":85}, ...]
    - prefer_evaluator：首选 evaluator_type（默认 teacher → 无则回退 ai）。
        同一次 submission 若同时存在 teacher 和 ai 评价，只取首选那条。
    - 返回：{维度名: 加权均分 0-100}（缺失维度不会出现，避免 0 分拉低）
    """
    if not evaluations:
        return {}

    # Step 1：按 submission_id 去重 → 同一 submission 挑优先级高的 evaluator
    per_submission: Dict[int, Any] = {}
    fallback_evaluator = "ai" if prefer_evaluator == "teacher" else "teacher"
    for ev in evaluations:
        if isinstance(ev, dict):
            sid = ev.get("submission_id")
            etype = ev.get("evaluator_type")
        else:
            sid = getattr(ev, "submission_id", None)
            etype = getattr(ev, "evaluator_type", None)
        if sid is None or etype not in ("ai", "teacher"):
            continue
        existing = per_submission.get(sid)
        if existing is None:
            per_submission[sid] = ev
            continue
        # 优先级：prefer > fallback > 其他
        def rank(e):
            tp = e.get("evaluator_type") if isinstance(e, dict) else getattr(e, "evaluator_type", None)
            if tp == prefer_evaluator:
                return 2
            if tp == fallback_evaluator:
                return 1
            return 0
        if rank(ev) > rank(existing):
            per_submission[sid] = ev

    # Step 2：按 created_at 倒排，取最近 last_n
    picked = sorted(per_submission.values(), key=_evaluations_sort_key, reverse=True)[: max(1, int(last_n))]

    # Step 3：指数衰减加权
    dim_weighted_sum: Dict[str, float] = {}
    dim_weight_total: Dict[str, float] = {}
    for idx, ev in enumerate(picked):
        w = math.pow(float(decay), idx)
        ds = ev.get("dimension_scores") if isinstance(ev, dict) else getattr(ev, "dimension_scores", None)
        if not ds:
            continue
        # 兼容 JSON 对象 & JSON 数组
        pairs: List[tuple] = []
        if isinstance(ds, dict):
            pairs = [(str(k), _to_float(v)) for k, v in ds.items()]
        elif isinstance(ds, list):
            for d in ds:
                if isinstance(d, dict):
                    name = d.get("name") or d.get("dimension")
                    score = _to_float(d.get("score", d.get("value")))
                    if name is not None:
                        pairs.append((str(name), score))
                else:
                    # ORM 维度对象兜底
                    name = getattr(d, "name", None) or getattr(d, "dimension", None)
                    if name is not None:
                        score = _to_float(getattr(d, "score", getattr(d, "value", 0.0)))
                        pairs.append((str(name), score))
        for name, score in pairs:
            if not name:
                continue
            dim_weighted_sum[name] = dim_weighted_sum.get(name, 0.0) + score * w
            dim_weight_total[name] = dim_weight_total.get(name, 0.0) + w

    result: Dict[str, float] = {}
    for name in dim_weighted_sum:
        wt = dim_weight_total.get(name, 0.0)
        if wt > 0:
            result[name] = round(dim_weighted_sum[name] / wt, 2)
    return result


# ============================================================
# 核心 2：calculate_job_match  （5 步算法，完全按 2.1.4 规格）
# ============================================================

@dataclass
class MatchDimensionBreakdown:
    name: str
    student_score: float
    threshold: float
    weight: float
    contribution: float
    ratio: float   # min(学生/门槛, 1.2)
    passed: bool
    must: bool


def calculate_job_match(
    student_scores: Dict[str, float],
    skill_requirements: List[Dict[str, Any]],
    highlight_delta: float = 5.0,
    minor_gap_max: float = 15.0,
    cap_ratio: float = 1.2,
) -> Dict[str, Any]:
    """
    按计划书 2.1.4 规格的 5 步算法：

        输入: student_scores = {维度名: 0-100 均分}
              skill_requirements = [{name, weight, threshold, must?}]
        步骤:
          1. (已在函数外完成) 取岗位技能要求
          2. (已在函数外完成) 取学生加权历史均分
          3. 逐维度: contribution = min(学生/门槛, cap_ratio) × weight
          4. 归一化: match_score = Σcontribution / (cap_ratio × Σweight) × 100 → [0,100]
          5. 输出: highlights / gaps(level=minor|major) / radar

    返回:
        {
          "match_score": 0-100 浮点数,
          "dimension_breakdown": [MatchDimensionBreakdown 的 dict 形式…],
          "highlights": [{"name":"代码质量","student_score":95,"threshold":80,"delta":+15}…],
          "gaps":       [{"name":"代码质量","student_score":60,"threshold":75,"delta":-15,
                          "level":"minor|major","must":true}…],
          "radar": {
            "axis_labels": ["代码质量", "功能完整性"…],   # 维度顺序（前后端一致使用）
            "job_thresholds": [70.0, 75.0, …],            # 蓝虚线：岗位门槛
            "student_scores":  [87.0, 82.0, …],           # 红实线：学生能力
            "weights":        [30.0, 25.0, …],            # 归一化前原始权重
          }
        }
    """
    if not student_scores:
        student_scores = {}
    if not skill_requirements:
        return {
            "match_score": 0.0,
            "dimension_breakdown": [],
            "highlights": [],
            "gaps": [],
            "radar": {"axis_labels": [], "job_thresholds": [], "student_scores": [], "weights": []},
        }

    # 规范化 skill_requirements：支持 Pydantic 对象 / dict / 字符串（旧 A2 兼容）
    normalized_reqs: List[Dict[str, Any]] = []
    for s in skill_requirements or []:
        if isinstance(s, str):
            normalized_reqs.append({"name": s, "weight": 1.0, "threshold": 60.0, "must": False})
        elif isinstance(s, dict):
            normalized_reqs.append({
                "name": str(s.get("name", "")).strip(),
                "weight": _to_float(s.get("weight", 1.0)),
                "threshold": _to_float(s.get("threshold", 60.0)),
                "must": bool(s.get("must", False)),
            })
        else:
            normalized_reqs.append({
                "name": str(getattr(s, "name", "") or "").strip(),
                "weight": _to_float(getattr(s, "weight", 1.0)),
                "threshold": _to_float(getattr(s, "threshold", 60.0)),
                "must": bool(getattr(s, "must", False)),
            })
    normalized_reqs = [r for r in normalized_reqs if r["name"]]

    if not normalized_reqs:
        return {
            "match_score": 0.0,
            "dimension_breakdown": [],
            "highlights": [],
            "gaps": [],
            "radar": {"axis_labels": [], "job_thresholds": [], "student_scores": [], "weights": []},
        }

    total_weight = sum(max(0.0, r["weight"]) for r in normalized_reqs)
    if total_weight <= 0:
        total_weight = float(len(normalized_reqs))  # 全 0 权重 → 退化为等权

    breakdown: List[MatchDimensionBreakdown] = []
    sum_contrib = 0.0

    highlights: List[Dict[str, Any]] = []
    gaps: List[Dict[str, Any]] = []

    for req in normalized_reqs:
        name = req["name"]
        threshold = req["threshold"] or 60.0
        weight = req["weight"]
        if weight <= 0:
            weight = total_weight / len(normalized_reqs)  # 保底
        student_score = student_scores.get(name)
        if student_score is None:
            # 学生没有该维度成绩：按 0 分处理（不是 NULL）。对 must=True 会直接重大缺口
            student_score = 0.0
            ratio = 0.0
        else:
            student_score = _to_float(student_score)
            if threshold > 0:
                ratio = min(student_score / threshold, cap_ratio)
            else:
                ratio = cap_ratio if student_score > 0 else 0.0
        contribution = ratio * weight
        sum_contrib += contribution
        passed = student_score >= threshold
        breakdown.append(MatchDimensionBreakdown(
            name=name,
            student_score=round(student_score, 2),
            threshold=round(threshold, 2),
            weight=round(weight, 2),
            contribution=round(contribution, 4),
            ratio=round(ratio, 4),
            passed=passed,
            must=bool(req["must"]),
        ))

        delta = round(student_score - threshold, 2)
        if delta >= highlight_delta:
            highlights.append({
                "name": name, "student_score": round(student_score, 2),
                "threshold": round(threshold, 2), "delta": delta,
            })
        elif delta < 0:
            abs_delta = abs(delta)
            level = "minor" if abs_delta <= minor_gap_max else "major"
            gaps.append({
                "name": name, "student_score": round(student_score, 2),
                "threshold": round(threshold, 2), "delta": delta,
                "level": level, "must": bool(req["must"]),
            })

    denom = cap_ratio * total_weight
    match_score = 0.0 if denom <= 0 else round((sum_contrib / denom) * 100, 2)
    if match_score < 0:
        match_score = 0.0
    if match_score > 100:
        match_score = 100.0

    # must=True 任何一个没过 → 直接额外扣 10 分（底线要求，计划书没写但企业招聘场景合理附加规则，可关掉：将下面 2 行注释）
    must_failed = [b for b in breakdown if b.must and not b.passed]
    if must_failed:
        match_score = round(max(0.0, match_score - 10.0), 2)

    axis = [b.name for b in breakdown]
    radar = {
        "axis_labels": axis,
        "job_thresholds": [round(b.threshold, 2) for b in breakdown],
        "student_scores":  [round(b.student_score, 2) for b in breakdown],
        "weights":         [round(b.weight, 2) for b in breakdown],
    }

    return {
        "match_score": match_score,
        "dimension_breakdown": [b.__dict__ for b in breakdown],
        "highlights": sorted(highlights, key=lambda h: -h["delta"]),
        "gaps": sorted(gaps, key=lambda g: g["delta"]),
        "radar": radar,
        "must_failed_count": len(must_failed),
    }


# ============================================================
# 辅助 3：批量匹配全班 → 返回 TOP N
# ============================================================

def batch_match_class(
    students_scores: Dict[int, Dict[str, float]],
    student_basics: Dict[int, Dict[str, Any]],
    skill_requirements: List[Dict[str, Any]],
    top_n: Optional[int] = None,
    min_score: float = 0.0,
) -> List[Dict[str, Any]]:
    """
    students_scores: {student_id: {维度名: 均分}}
    student_basics:  {student_id: {id, real_name, user_number, class_name, email...}}
    返回: 按 match_score 倒排的列表，每项含基础信息 + calculate_job_match() 结果
    """
    rows = []
    for sid, dim_scores in (students_scores or {}).items():
        info = (student_basics or {}).get(sid, {"id": sid})
        m = calculate_job_match(dim_scores, skill_requirements)
        if m["match_score"] < min_score:
            continue
        row = {"student_id": sid}
        if isinstance(info, dict):
            row.update({k: v for k, v in info.items() if k != "id"})
        row.update(m)
        rows.append(row)
    rows.sort(key=lambda r: -r["match_score"])
    if top_n and top_n > 0:
        rows = rows[: int(top_n)]
    return rows


# ============================================================
# 辅助 4：单学生 → 对全部岗位做 TOP 榜（student TOP 5 岗位）
# ============================================================

def batch_match_student_to_jobs(
    student_scores: Dict[str, float],
    jobs: List[Dict[str, Any]],
    top_n: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """
    jobs: [{id, title, job_type, enterprise_id, enterprise_name?, skill_requirements, ...}]
    """
    out = []
    for j in jobs or []:
        sks = j.get("skill_requirements", []) if isinstance(j, dict) else getattr(j, "skill_requirements", [])
        m = calculate_job_match(student_scores, sks)
        row = {"job_id": j.get("id") if isinstance(j, dict) else getattr(j, "id", None)}
        for k in ("title", "job_type", "level", "city", "salary_range", "enterprise_id", "enterprise_name"):
            v = j.get(k) if isinstance(j, dict) else getattr(j, k, None)
            if v is not None:
                row[k] = v
        row.update(m)
        out.append(row)
    out.sort(key=lambda r: -r["match_score"])
    if top_n and top_n > 0:
        out = out[: int(top_n)]
    return out
