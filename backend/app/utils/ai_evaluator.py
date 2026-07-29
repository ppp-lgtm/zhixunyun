import json
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from app.config import get_settings
from app.services.step_extractor import (
    parse_task_steps,
    _keyword_match,
    _normalize_for_match,
)

_settings = get_settings()

# DeepSeek 官方 API（文字评价）
DEEPSEEK_API_KEY = _settings.DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL = _settings.DEEPSEEK_BASE_URL

# 硅基流动 API（图片识别）
SILICON_API_KEY = _settings.SILICON_API_KEY
SILICON_BASE_URL = _settings.SILICON_BASE_URL


# 延迟初始化：没有 Key 时不实例化，避免启动时报错（本地开发 / CI 自测）
def _lazy_client(api_key: str, base_url: str):
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key, base_url=base_url)
    except Exception:
        return None


deepseek_client = _lazy_client(DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL)
silicon_client = _lazy_client(SILICON_API_KEY, SILICON_BASE_URL)


def evaluate(task_requirements, student_content, criteria):
    """DeepSeek 文字评价"""
    criteria_text = "、".join(criteria)

    prompt = f"""你是软件实训评价专家。请对照实训要求评价学生作业，按JSON格式返回。

实训要求：{task_requirements}

学生提交：{student_content}

评分维度：{criteria_text}

每个维度给0-100分和一句话理由，再加总分(加权平均)和总评。
只返回JSON，格式：{{"scores":[{{"name":"维度名","score":80,"reason":"理由"}}],"total":85,"comment":"总评"}}"""

    if deepseek_client is None:
        return {"scores": [], "total": 0, "comment": "AI 未配置，请联系管理员设置 DEEPSEEK_API_KEY。"}

    response = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    result = response.choices[0].message.content
    if "```" in result:
        result = result.split("```")[1].split("```")[0]
    if result.startswith("json"):
        result = result[4:]

    return json.loads(result.strip())


def evaluate_with_image(task_requirements, criteria, image_data_list=None, text_content=None):
    """支持多张图片的多模态评价"""
    criteria_text = "、".join(criteria)

    user_content = []

    # 放所有图片
    if image_data_list:
        for img in image_data_list:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": img}
            })

    content_text = f"""你是软件实训评价专家。请综合查看以下{len(image_data_list) if image_data_list else 0}张截图（可能包含代码截图、界面截图、文档截图等），按实训要求评价，返回JSON。

实训要求：{task_requirements}
{f'补充说明：{text_content}' if text_content else ''}
评分维度：{criteria_text}

请综合所有截图内容，每个维度给0-100分和理由，加总分和总评。
只返回JSON：{{"scores":[{{"name":"维度名","score":80,"reason":"理由"}}],"total":85,"comment":"总评"}}"""

    user_content.append({"type": "text", "text": content_text})

    if silicon_client is None:
        return {"scores": [], "total": 0, "comment": "图片识别服务未配置，请联系管理员设置 SILICON_API_KEY。"}

    response = silicon_client.chat.completions.create(
        model="Qwen/Qwen3.5-4B",
        messages=[{"role": "user", "content": user_content}],
        temperature=0.3,
        max_tokens=4096
    )

    result = response.choices[0].message.content
    if "```" in result:
        result = result.split("```")[1].split("```")[0]
    if result.startswith("json"):
        result = result[4:]

    return json.loads(result.strip())


def check_completeness(task_requirements, student_content):
    """DeepSeek 智能核查"""
    prompt = f"""你是软件实训核查专家。对照实训要求，检查学生作业的步骤完整性和逻辑漏洞。

实训要求：
{task_requirements}

学生提交：
{student_content[:3000]}

请返回JSON：
{{
    "steps": [
        {{"step":"实训要求中的步骤","status":"已完成/缺失/部分完成","detail":"说明"}}
    ],
    "issues": [
        {{"type":"逻辑漏洞/不规范/错误","description":"具体描述","severity":"高/中/低"}}
    ],
    "summary":"整体核查总结"
}}"""

    try:
        if deepseek_client is None:
            return {"steps": [], "issues": [], "summary": "核查暂时不可用：AI 服务未配置"}
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        result = response.choices[0].message.content
        if "```" in result:
            result = result.split("```")[1].split("```")[0]
        if result.startswith("json"):
            result = result[4:]
        return json.loads(result.strip())
    except:
        return {"steps": [], "issues": [], "summary": "核查暂时不可用"}

def is_ai_configured():
    """检查 AI API Key 是否已配置"""
    test_values = {"", "sk-your-api-key"}
    return bool(
        DEEPSEEK_API_KEY
        and DEEPSEEK_API_KEY not in test_values
        and (not DEEPSEEK_API_KEY.startswith("sk-") or len(DEEPSEEK_API_KEY) >= 16)
    )


# =================================================================
# E1：分步实训 — 步骤判定 + 维度汇总
# =================================================================

def _parse_structured_steps(task_obj) -> List[Dict[str, Any]]:
    """
    把 Task 对象的结构化步骤拆出来：
    - 优先用 task.steps (JSON) 里的 index/title/requirement/score_weight/pass_threshold
    - 否则按 parse_task_steps(requirements) 兜底，score_weight 平均分，pass_threshold 默认 50
    返回统一形状 [{index, title, requirement, score_weight, pass_threshold}]
    """
    defined = getattr(task_obj, "steps", None) or []
    if isinstance(defined, list) and defined:
        normalized: List[Dict[str, Any]] = []
        total_w = 0.0
        for idx, raw in enumerate(defined, 1):
            if not isinstance(raw, dict):
                continue
            i = raw.get("index") or idx
            title = (raw.get("title") or raw.get("name") or f"步骤{i}").strip()
            req = (raw.get("requirement") or raw.get("desc") or title or "").strip()
            w = float(raw.get("score_weight") or 0)
            thr = float(raw.get("pass_threshold") or 50.0)
            normalized.append({
                "index": int(i),
                "title": title,
                "requirement": req,
                "score_weight": w,
                "pass_threshold": thr,
            })
            total_w += w
        # 归一化权重
        if normalized:
            if total_w <= 0:
                eq_w = 100.0 / len(normalized)
                for s in normalized:
                    s["score_weight"] = eq_w
            else:
                for s in normalized:
                    s["score_weight"] = s["score_weight"] * 100.0 / total_w
            # 按 index 排序
            normalized.sort(key=lambda x: x["index"])
            return normalized

    # 兜底：从 requirements 文本解析
    names = parse_task_steps(getattr(task_obj, "requirements", "") or "")
    if not names:
        return []
    eq_w = 100.0 / len(names)
    return [
        {
            "index": i + 1,
            "title": name,
            "requirement": name,
            "score_weight": eq_w,
            "pass_threshold": 50.0,
        }
        for i, name in enumerate(names)
    ]


def _evidence_to_text(step_evidence: Dict[str, Any]) -> str:
    """把单步提交的 evidence 拼成一段纯文本供关键词/AI 判断。"""
    parts: List[str] = []
    content = (step_evidence or {}).get("content")
    if content:
        parts.append(str(content))
    files = (step_evidence or {}).get("files") or []
    for f in files:
        if isinstance(f, dict):
            fc = f.get("content")
            if fc:
                parts.append(f"```文件 {f.get('filename','?')}:\n{str(fc)[:2000]}\n```")
    # OCR 文本（如果 D2 已经识别过图片里的文字，会塞到 evidence 的 ocr_texts 里）
    ocr_texts = (step_evidence or {}).get("ocr_texts") or []
    for t in ocr_texts:
        if t:
            parts.append(f"[图片OCR] {str(t)[:2000]}")
    images_desc = (step_evidence or {}).get("images") or []
    if images_desc:
        parts.append(f"[附带截图 {len(images_desc)} 张] " +
                     ", ".join([str(x.get("filename") if isinstance(x, dict) else x) for x in images_desc][:10]))
    return "\n".join(parts).strip()


def _judge_one_step_rule(step: Dict[str, Any], ev_text: str) -> Tuple[bool, float, str, str]:
    """
    单步本地规则判定（AI 没配就用这个，保证自测和 demo 也能跑）。
    返回 (passed, score 0-100, reason, source="rule")。
    """
    title = step.get("title") or step.get("requirement") or ""
    req = step.get("requirement") or title or ""
    if not ev_text:
        return False, 0.0, "该步骤没有提交任何文件/文字/截图证据", "rule"
    thr = float(step.get("pass_threshold") or 50.0)

    # 启发式否定探测：学生明确写了"没完成 / 未做 / 尚未 / 不 / TODO / FIXME / None / N/A / no / not yet / 待完成"这类，
    # 直接把原始 score 打到 0，避免"写了没完成 zip"反而命中"zip"关键词导致假通过。
    ev_low = ev_text.lower()
    NEG_PATTERNS = [
        "未完成", "没完成", "尚未完成", "还没做", "没做", "尚未做", "未做",
        "未通过", "不通过", "没通过",
        "待完成", "待做", "暂未", "暂无", "未提交",
        "todo", "fixme", "tbd", "tba", "n/a", "na", "none", "not yet",
        "未实现", "没实现", "未写", "没写",
    ]
    neg_hit = any(p in ev_low for p in NEG_PATTERNS)

    # 先用 title 命中，再用 requirement 命中，取两者里高的 score
    _, _, s_title = _keyword_match(title, ev_text)
    _, _, s_req = _keyword_match(req, ev_text)
    score = max(s_title, s_req) * 100.0
    # 还有看 evidence 内容是否包含英文函数名/接口名/关键词等
    norm_req = _normalize_for_match(req)
    norm_ev = _normalize_for_match(ev_text)
    if norm_req and norm_ev:
        # 把 requirement 的 token 按空格分，看 70% 命中就算过
        toks = [t for t in norm_req.split() if t]
        if toks:
            ev_set = set(norm_ev.split())
            extra_hits = sum(1 for t in toks if t in ev_set)
            extra_ratio = extra_hits / len(toks)
            if extra_ratio * 100.0 > score:
                score = extra_ratio * 100.0

    # 否定命中 → 原始 score 乘以 0（如果否定词出现在该步骤核心关键词附近/行开头，更严格地直接清零）
    if neg_hit:
        # 更细：只对长度短的说明（<500 字）+ 否定词在 3 行以内时清零；
        # 长文档（带"还有部分功能没完成"的整体总结）里否定词不影响（用阈值规则）。
        lines_ev = [ln.strip() for ln in ev_text.splitlines() if ln.strip()]
        if len(ev_text) < 600 and len(lines_ev) <= 15:
            score = 0.0

    passed = score >= thr
    reason = f"关键词/内容匹配分数 {score:.1f}/{thr:.1f}（阈值 {thr:.1f}）"
    if neg_hit:
        reason += "；检测到否定描述（没完成/未/未提交/TODO 等）"
    if passed:
        reason += " → 通过"
    else:
        reason += " → 未通过（需要补充更直接的证据：截图、对应代码片段或文字说明）"
    return passed, round(score, 2), reason, "rule"


def _judge_one_step_ai(step: Dict[str, Any], ev_text: str) -> Tuple[bool, float, str, str]:
    """AI 判定单步（优先但非强制，失败回退 rule）。"""
    if not is_ai_configured() or deepseek_client is None:
        return _judge_one_step_rule(step, ev_text)
    prompt = f"""你是软件实训步骤判定专家。请按步骤要求与学生提交的证据，判定该步骤是否通过。
步骤编号：{step.get('index')}
步骤标题：{step.get('title')}
步骤要求：{step.get('requirement')}
通过阈值(满分100)：{step.get('pass_threshold', 50)}

学生提交的证据（文件/文字/截图OCR拼接）：
{ev_text[:4000]}

只返回 JSON：{{"score":0-100,"passed":true/false,"reason":"一句话理由，指出证据里命中了什么或缺了什么"}}
"""
    try:
        resp = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        raw = resp.choices[0].message.content or ""
        if "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        if raw.startswith("json"):
            raw = raw[4:]
        obj = json.loads(raw.strip())
        score = float(obj.get("score", 0))
        passed = bool(obj.get("passed", score >= float(step.get("pass_threshold", 50))))
        reason = str(obj.get("reason", "")) or (
            f"AI 打分 {score:.1f}/{step.get('pass_threshold', 50)}"
        )
        return passed, round(score, 2), reason, "ai"
    except Exception:
        return _judge_one_step_rule(step, ev_text)


def evaluate_step_mode(
    task_obj,
    step_evidences: List[Dict[str, Any]],
    criteria: Optional[List[str]] = None,
    task_requirements_text: Optional[str] = None,
) -> Dict[str, Any]:
    """
    E1：分步模式 evaluate。
    step_evidences 形状：[{step_index, files, content, images, ocr_texts}, ...]
    返回形状：{
      "scores": [{"name","score","reason"}],   # 兼容老 shape，维度分由步骤分加权算出 + 代码质量兜底
      "total": float,                          # 0-100
      "comment": str,
      "steps": [                               # 新增：逐步骤判定
         {"index","title","requirement","score_weight","pass_threshold",
          "passed","score","reason","source","evidence_preview"}
      ]
    }
    """
    steps_def = _parse_structured_steps(task_obj)
    if not steps_def:
        # 兜底：如果任务里完全没有结构化步骤，退化为整包评价
        req = task_requirements_text or getattr(task_obj, "requirements", "") or ""
        ev_all = "\n".join(_evidence_to_text(e) for e in (step_evidences or []))
        fallback = evaluate(req, ev_all, criteria or [])
        fallback["steps"] = []
        return fallback

    # 给每个 step_index 找 evidence（可能没传该步）
    ev_map: Dict[int, Dict[str, Any]] = {}
    for ev in (step_evidences or []):
        if not isinstance(ev, dict):
            continue
        si = ev.get("step_index")
        try:
            si = int(si)
        except Exception:
            si = None
        if si and si >= 1:
            ev_map[si] = ev

    crit = criteria or [
        "功能完整性", "代码质量", "文档规范性", "界面设计"
    ][:max(1, min(4, len(criteria) if criteria else 4))]

    step_results: List[Dict[str, Any]] = []
    weighted_score = 0.0
    passed_count = 0
    missing_indices: List[int] = []
    for sd in steps_def:
        idx = sd["index"]
        ev = ev_map.get(idx) or {}
        ev_text = _evidence_to_text(ev)
        passed, score, reason, source = _judge_one_step_ai(sd, ev_text)
        if passed:
            passed_count += 1
        if idx not in ev_map:
            missing_indices.append(idx)
        w = float(sd["score_weight"] or 0)
        weighted_score += score * w / 100.0
        step_results.append({
            "index": idx,
            "title": sd["title"],
            "requirement": sd["requirement"],
            "score_weight": round(w, 2),
            "pass_threshold": float(sd.get("pass_threshold") or 50),
            "passed": passed,
            "score": score,
            "reason": reason,
            "source": source,
            "evidence_preview": ev_text[:200],
        })

    total = round(min(100.0, max(0.0, weighted_score)), 2)
    # 维度分映射：步骤加权总分 作为"功能完整性"维度；代码质量 / 文档规范 / 界面设计 保守按步骤通过率×80~100 估，方便前端展示
    func_total = total
    step_pass_rate = (passed_count / len(steps_def)) if steps_def else 0.0
    dim_scores: List[Dict[str, Any]] = []
    for c in crit:
        c_norm = (c or "").strip()
        if not c_norm:
            continue
        if any(k in c_norm for k in ["功能", "完成", "实现", "feature"]):
            s = func_total
            r = f"按 {len(steps_def)} 个步骤的加权平均打分（{passed_count}/{len(steps_def)} 通过）"
        elif any(k in c_norm for k in ["代码", "质量", "编码", "code", "质量"]):
            code_hit_sum = 0.0
            for sr in step_results:
                # 代码里的证据若包含"代码块/缩进/def/函数/import"等提示，给更高分
                if any(tok in (sr.get("evidence_preview") or "") for tok in ["```", "def ", "import ", "public ", "function ", "{"]):
                    code_hit_sum += sr["score"] * float(sr.get("score_weight") or 0) / 100.0
                else:
                    code_hit_sum += sr["score"] * 0.85 * float(sr.get("score_weight") or 0) / 100.0
            s = round(min(100.0, max(0.0, code_hit_sum)), 2)
            r = f"按步骤证据里的代码片段/结构化证据保守估算（步骤通过率 {step_pass_rate*100:.0f}%）"
        elif any(k in c_norm for k in ["文档", "规范", "readme", "注释", "说明"]):
            doc_ratio = 0.0
            total_w = 0.0
            for sr in step_results:
                w = float(sr.get("score_weight") or 0)
                total_w += w
                evp = sr.get("evidence_preview") or ""
                if any(k in evp for k in ["说明", "readme", "README", "注释", "# ", "/*", "文档"]):
                    doc_ratio += w * (sr["score"] / 100.0)
                else:
                    doc_ratio += w * 0.5 * (sr["score"] / 100.0)
            s = round((doc_ratio / total_w * 100.0) if total_w else 50.0, 2)
            r = "按步骤证据中的说明文字/注释/文档篇幅估算"
        else:  # 界面设计 / 其他
            ui_ratio = 0.0
            total_w = 0.0
            for sr in step_results:
                w = float(sr.get("score_weight") or 0)
                total_w += w
                evp = sr.get("evidence_preview") or ""
                if any(k in evp.lower() for k in ["[附带截图", "界面", "ui", "页面", "按钮", "表单"]):
                    ui_ratio += w * (sr["score"] / 100.0)
                else:
                    ui_ratio += w * 0.4 * (sr["score"] / 100.0)
            s = round((ui_ratio / total_w * 100.0) if total_w else 50.0, 2)
            r = "按步骤证据中的截图/界面描述估算"
        dim_scores.append({"name": c_norm, "score": s, "reason": r})

    # 总评：包含缺失步骤提示
    parts_c = []
    if missing_indices:
        parts_c.append(f"缺失步骤（未提交证据）：{missing_indices}；")
    parts_c.append(f"共 {len(steps_def)} 步，{passed_count} 步通过，整体加权打分 {total}/100。")
    if not missing_indices and passed_count == len(steps_def):
        parts_c.append("全部步骤通过，可继续下一阶段。")
    elif step_pass_rate >= 0.5:
        parts_c.append("步骤完成度过半，建议优先补齐缺失项。")
    else:
        parts_c.append("步骤完成度较低，请对照要求逐步骤提交证据。")
    comment = " ".join(parts_c)
    return {
        "scores": dim_scores,
        "total": total,
        "comment": comment,
        "steps": step_results,
    }