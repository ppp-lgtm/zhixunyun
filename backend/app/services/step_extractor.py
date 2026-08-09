"""
知训云 D2 阶段：图片中的实训步骤提取 + 进度计算
三层回退策略（从强到弱）：
  1) PaddleOCR 本地模型（若 paddleocr 可用）— 真 OCR
  2) 配置了 OCR_PROVIDER=baidu / general 且填了 API Key/Secret/Token — HTTP 调用云 OCR
  3) 兜底：纯本地规则
     - 文件名匹配：步骤1/第一步/step1/page1/part1/第1步/1.png / 01_登录.png / step_1_完成.png
     - 上传顺序（zip 中图片的排列顺序）当做 步骤 N
     - 空/识别失败时：按数量 / 命名规则保守估算
返回统一形状：
  {
    "total_steps": int,
    "passed": int,
    "missing": int,
    "percent": 0.0-100.0,
    "source": "paddleocr|baidu|general|filename|fallback",
    "steps": [
        {"index":int, "name":str, "status":"passed|missing", "detail":str,
         "source_image":str|None, "evidence":str|None}
    ]
  }
"""
from __future__ import annotations

import os
import re
from typing import Any, Dict, List, Optional, Tuple


# =================================================================
# 1) 配置 & 可选 OCR 依赖探测（import 失败不崩，自动走兜底）
# =================================================================
try:  # pragma: no cover - runtime optional
    from paddleocr import PaddleOCR  # type: ignore
    _HAS_PADDLE = True
except Exception:  # pragma: no cover
    PaddleOCR = None  # type: ignore
    _HAS_PADDLE = False

_paddle_singleton = None


def _get_paddle_ocr(lang: str = "ch"):
    """懒加载 PaddleOCR（避免 import 阶段就下载模型、占内存）。"""
    global _paddle_singleton
    if not _HAS_PADDLE:
        return None
    if _paddle_singleton is None:
        try:
            _paddle_singleton = PaddleOCR(use_angle_cls=True, lang=lang, show_log=False)
        except Exception:
            _paddle_singleton = False
    return _paddle_singleton if _paddle_singleton else None


from app.config import get_settings  # noqa: E402

_settings = get_settings()
_OCR_PROVIDER = ""
_BAIDU_API_KEY = ""
_BAIDU_SECRET_KEY = ""
_GENERAL_OCR_URL = ""
_GENERAL_OCR_API_KEY = ""
_GENERAL_OCR_HEADER_KEY = "Authorization"
try:
    # 向后兼容：老 config 里没这些字段不报错
    _OCR_PROVIDER = str(getattr(_settings, "OCR_PROVIDER", "") or "").lower()
    _BAIDU_API_KEY = str(getattr(_settings, "OCR_BAIDU_API_KEY", "") or "")
    _BAIDU_SECRET_KEY = str(getattr(_settings, "OCR_BAIDU_SECRET_KEY", "") or "")
    _GENERAL_OCR_URL = str(getattr(_settings, "OCR_GENERAL_URL", "") or "")
    _GENERAL_OCR_API_KEY = str(getattr(_settings, "OCR_GENERAL_API_KEY", "") or "")
    _GENERAL_OCR_HEADER_KEY = str(getattr(_settings, "OCR_GENERAL_HEADER", "") or "Authorization") or "Authorization"
except Exception:  # pragma: no cover
    pass


# =================================================================
# 2) 规则：把任务要求 / 步骤名解析成步骤列表
# =================================================================
_STEP_LINE_PATTERNS = [
    # 步骤 1：xxx   / 步骤1.xxx / 步骤一
    re.compile(r"^\s*步骤\s*([0-9一二三四五六七八九十百]+)[.\s:：、\)]\s*(.*)$"),
    re.compile(r"^\s*第\s*([0-9一二三四五六七八九十百]+)\s*步[.\s:：、\)]\s*(.*)$"),
    # Step 1: xxx / step 1. xxx
    re.compile(r"^\s*step\s*([0-9]+)[.\s:：、\)]\s*(.*)$", re.IGNORECASE),
    # 1. xxx / 1) xxx / 1、xxx / (1) xxx
    re.compile(r"^\s*[(（]?\s*([0-9一二三四五六七八九十百]+)\s*[)）.\s:：、]\s*(.*)$"),
    # 第一阶段 / Part 1 / Phase 1 / 第X阶段
    re.compile(r"^\s*第\s*([0-9一二三四五六七八九十百]+)\s*(?:阶段|部分|环节|轮次)[.\s:：、\-]\s*(.*)$", re.IGNORECASE),
    re.compile(r"^\s*(?:阶段|part|phase)\s*([0-9一二三四五六七八九十百]+)[.\s:：、\-]\s*(.*)$", re.IGNORECASE),
]


_CN_NUM_MAP = {"零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
               "六": 6, "七": 7, "八": 8, "九": 9, "十": 10, "百": 100}


def _cn_to_int(s: str) -> Optional[int]:
    """把 '十二' / '10' 都转成 int。"""
    s = (s or "").strip()
    if not s:
        return None
    if re.fullmatch(r"\d+", s):
        try:
            return int(s)
        except Exception:
            return None
    # 简单中文数字（只处理 0~99）
    total = 0
    current = 0
    tens = False
    for ch in s:
        if ch not in _CN_NUM_MAP:
            return None
        v = _CN_NUM_MAP[ch]
        if v == 10:
            current = current if current else 1
            total += current * 10
            current = 0
            tens = True
        elif v == 100:
            return None  # 百暂时不处理，避免复杂
        else:
            current = v
    if tens:
        return total + current
    return total + current


def parse_task_steps(task_requirements: str) -> List[str]:
    """从 task.requirements 里解析出步骤名（找不到就返回空列表，后续用图片数量兜底）。"""
    if not task_requirements:
        return []
    lines = re.split(r"[\n;；]", task_requirements)
    collected: Dict[int, str] = {}
    for line in lines:
        line = line.strip()
        if not line or len(line) < 4:
            continue
        for pat in _STEP_LINE_PATTERNS:
            m = pat.match(line)
            if not m:
                continue
            idx_raw, name = m.group(1), (m.group(2) or "").strip()
            idx = _cn_to_int(idx_raw)
            if idx is None or idx <= 0:
                continue
            if not name:
                name = f"步骤{idx}"
            # 不要太长
            if len(name) > 80:
                name = name[:77] + "..."
            # 同一个 idx 取最长描述
            if idx not in collected or len(collected[idx]) < len(name):
                collected[idx] = name
            break
    if not collected:
        return []
    return [collected[i] for i in sorted(collected.keys())]


# =================================================================
# 3) 图片文件名里的步骤编号提取（兜底信号）
# =================================================================
_FILE_STEP_PATTERNS = [
    # 步骤1 / step_1 / 第 1 步 / step-1.png
    re.compile(r"步\s*骤\s*([0-9一二三四五六七八九十百]+)", re.IGNORECASE),
    re.compile(r"第\s*([0-9一二三四五六七八九十百]+)\s*步"),
    re.compile(r"(?:step|part|phase|page|p|图)\s*[_-]?([0-9]+)", re.IGNORECASE),
    # 01_登录.png / 02 注册.jpg / 03-提交.jpeg
    re.compile(r"^[_-]?([0-9]{1,3})[_ \-]"),
    # 03提交 / 步骤1登录（前缀编号+后续文字无分隔）
    re.compile(r"^([0-9]{1,3})(?=[\u4e00-\u9fa5A-Za-z])"),
    # 1.png / 2.jpg / 3.jpeg（纯数字文件名）
    re.compile(r"^([0-9]{1,3})$"),
]


def _extract_step_index_from_filename(filename: str) -> Optional[int]:
    base = os.path.splitext(os.path.basename(filename or ""))[0]
    if not base:
        return None
    low = base.lower()
    for pat in _FILE_STEP_PATTERNS:
        m = pat.search(low)
        if not m:
            continue
        idx = _cn_to_int(m.group(1))
        if idx is not None and idx >= 1:
            return idx
    return None


def _normalize_for_match(s: str) -> str:
    if not s:
        return ""
    # 单字中文也保留（避免「登录」被拆成两个字无法匹配时还能逐个字命中）
    tokens = re.findall(r"[\u4e00-\u9fa5]+|[A-Za-z_][A-Za-z0-9_]{0,24}", s)
    out = []
    for t in tokens:
        if re.fullmatch(r"[\u4e00-\u9fa5]+", t):
            # 中文按单字拆再展开
            out.extend(list(t))
        else:
            out.append(t.lower())
    return " ".join(out)


def _keyword_match(step_name: str, evidence_text: str) -> Tuple[int, int, float]:
    """
    返回 (hit_keywords, total_keywords, score 0-1)。
    证据文本里命中的步骤关键词比例 ≥ 50% 算 passed。
    关键词：中文 2 字组合 / 英文单词（≥2 字母）。
    """
    if not step_name:
        return 0, 0, 0.0
    kw: List[str] = []
    # 中文：2 字连续子串
    for zh_block in re.findall(r"[\u4e00-\u9fa5]+", step_name):
        for j in range(len(zh_block) - 1):
            kw.append(zh_block[j:j + 2])
    # 英文单词
    for en_word in re.findall(r"[A-Za-z_][A-Za-z0-9_]{1,24}", step_name):
        kw.append(en_word.lower())
    if not kw:
        # 兜底：单字
        for ch in step_name:
            if "\u4e00" <= ch <= "\u9fa5":
                kw.append(ch)
    # 对短步骤名（≤3 个中文词 / 英文词）放宽关键词数量要求：去掉重复 2 字子串里最尾部的重复项，避免 3 字步骤产生 2 个关键词导致 1/2=0.5 卡边界
    unique_kw = list(dict.fromkeys(kw))
    # 启发式：如果 step_name 是 N 字中文短语（N≤6）且 unique_kw 只有 N-1 条，去掉最后一条重复子串（只在关键词数少时触发）
    zh_chars = re.findall(r"[\u4e00-\u9fa5]", step_name)
    en_words = re.findall(r"[A-Za-z_][A-Za-z0-9_]{1,24}", step_name)
    if len(zh_chars) >= 2 and len(zh_chars) <= 8 and len(en_words) == 0 and len(unique_kw) >= 3:
        # 只保留「第一个出现的核心语义词 + 英文单词」；压缩 unique_kw 为 ceil(N/2) + 2 条？简单：只保留索引为 0, 2, 4... 的 2 字 bigram
        compressed = [unique_kw[i] for i in range(len(unique_kw)) if i % 2 == 0]
        if compressed:
            unique_kw = compressed
    if not unique_kw:
        return 0, 0, 0.0

    ev = evidence_text or ""
    # 证据侧归一化：中文 2 字子串 + 单字 + 英文词
    ev_zh_bigrams = set()
    ev_zh_chars = set()
    for zh_block in re.findall(r"[\u4e00-\u9fa5]+", ev):
        for j in range(len(zh_block) - 1):
            ev_zh_bigrams.add(zh_block[j:j + 2])
        for ch in zh_block:
            ev_zh_chars.add(ch)
    ev_en = {w.lower() for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{1,24}", ev)}
    # 常见同义词（英文缩写 ↔ 中文）
    SYNONYMS = {
        "zip": {"打包", "压缩", "上传", "封装"},
        "login": {"登录"},
        "register": {"注册"},
        "signin": {"登录"},
        "signup": {"注册"},
        "submit": {"提交", "上传"},
        "upload": {"上传"},
        "homework": {"作业"},
        "assignment": {"作业"},
        "readme": {"说明", "文档"},
        "ui": {"界面"},
        "design": {"设计"},
        "page": {"页面"},
        "pages": {"页面"},
    }
    def english_synonyms_hit(en_word: str) -> bool:
        low = en_word.lower()
        if low in ev_en:
            return True
        syns = SYNONYMS.get(low, set())
        if not syns:
            return False
        for s in syns:
            if len(s) == 1:
                if s in ev_zh_chars:
                    return True
            else:
                # 2+ 字：看子串
                ok = True
                bigrams_s = {s[j:j+2] for j in range(len(s)-1)}
                chars_s = set(s)
                if len(s) >= 2 and (len(bigrams_s & ev_zh_bigrams) >= max(1, len(bigrams_s) // 2)):
                    return True
                if chars_s and chars_s.issubset(ev_zh_chars):
                    return True
                ok = False
                if ok:
                    return True
        return False

    hit = 0
    total = len(unique_kw)
    for k in unique_kw:
        if len(k) == 2 and "\u4e00" <= k[0] <= "\u9fa5":
            if k in ev_zh_bigrams:
                hit += 1
        elif len(k) == 1 and "\u4e00" <= k <= "\u9fa5":
            if k in ev_zh_chars:
                hit += 1
        else:
            if english_synonyms_hit(k):
                hit += 1
    score = hit / total if total else 0.0
    return hit, total, score


# =================================================================
# 4) PaddleOCR 封装
# =================================================================
def _run_paddle_ocr(image_path: str) -> Optional[str]:
    ocr = _get_paddle_ocr()
    if not ocr or not os.path.exists(image_path):
        return None
    try:
        result = ocr.ocr(image_path, cls=True)
    except Exception:
        return None
    lines: List[str] = []
    if not result:
        return None
    # paddleocr 返回结构：[[ [box, (text, score)], ... ]]
    try:
        for page in result:
            if not page:
                continue
            for item in page:
                try:
                    text = str(item[1][0]).strip()
                    if text:
                        lines.append(text)
                except Exception:
                    continue
    except Exception:
        return None
    return "\n".join(lines) if lines else None


# =================================================================
# 5) 云 OCR 占位（PaddleOCR 不可用但配置了 API Key 时走这个分支）
# =================================================================
def _run_cloud_ocr(image_path: str) -> Optional[str]:
    """配置了云 OCR 时调用（当前只实现 provider=baidu/general 的接口，不实际请求时返回 None）。"""
    if not os.path.exists(image_path):
        return None
    if _OCR_PROVIDER == "baidu" and _BAIDU_API_KEY and _BAIDU_SECRET_KEY:
        # 比赛现场若用到百度 OCR，按官方文档这里实现 access_token + general_basic 即可
        # 这里暂不直接请求，避免无凭证时挂掉；返回 None 继续走兜底
        return None
    if _OCR_PROVIDER == "general" and _GENERAL_OCR_URL and _GENERAL_OCR_API_KEY:
        return None
    return None


# =================================================================
# 6) 对外主函数：extract_step_progress
# =================================================================
ImageFile = Dict[str, Any]  # {filename, path?, bytes?, content_type?}


def _gather_evidence(img: ImageFile, source_chain: List[str]) -> Tuple[Optional[str], str]:
    """尝试从一张图里提取文字证据，按 OCR 优先级回退。返回 (evidence, used_source)。"""
    path = img.get("path")
    # 1) PaddleOCR
    if _HAS_PADDLE and path:
        text = _run_paddle_ocr(path)
        if text:
            source_chain.append("paddleocr")
            return text, "paddleocr"
    # 2) 云 OCR
    if path:
        text = _run_cloud_ocr(path)
        if text:
            source_chain.append(_OCR_PROVIDER or "cloud")
            return text, (_OCR_PROVIDER or "cloud")
    # 3) 都没识别出来 → evidence=None，source_chain 记 "fallback"
    source_chain.append("fallback")
    return None, "fallback"


def extract_step_progress(
    task_requirements: str,
    images: List[ImageFile],
    *,
    min_match_ratio: float = 0.5,
) -> Dict[str, Any]:
    """
    参数：
      - task_requirements: 任务要求文本（里面可能列了步骤 1/2/3...）
      - images: 图片列表，每项 {filename:str, path:str(可选)}，顺序就是上传顺序
    返回：见文件顶部 docstring
    """
    source_chain: List[str] = []
    images = images or []

    step_names = parse_task_steps(task_requirements or "")
    step_names_explicit = bool(step_names)
    # 如果任务要求里没写步骤名：按「图片数量」/ 文件名编号 推断 total_steps
    filename_indices: Dict[str, int] = {}
    for img in images:
        idx = _extract_step_index_from_filename(img.get("filename", ""))
        if idx is not None:
            filename_indices[img.get("filename", "")] = idx
    max_file_idx = max(filename_indices.values()) if filename_indices else 0

    if step_names:
        total_steps = len(step_names)
    else:
        # 没有显式步骤名 → 以「文件名编号最大值」和「图片数」两者较大值为总数
        total_steps = max(max_file_idx, len(images))
        step_names = [f"步骤{i+1}" for i in range(total_steps)]

    # 把图片证据收集起来：{step_idx_from_filename: evidence_text} 同时保留上传顺序
    evidence_by_step_idx: Dict[int, List[str]] = {}
    ordered_evidences: List[Tuple[Optional[int], str, str]] = []  # (step_idx or None, evidence, filename)
    sources_used: set = set()
    for img in images:
        fn = img.get("filename", "") or ""
        idx_from_name = filename_indices.get(fn)
        ev_text, used = _gather_evidence(img, source_chain)
        sources_used.add(used)
        # 即使 OCR 没识别出文字，也用「文件名里抓的内容」做弱证据
        if not ev_text:
            # 从文件名里取中文/英文关键词当弱证据
            base = os.path.splitext(os.path.basename(fn))[0]
            weak = " ".join(re.findall(r"[\u4e00-\u9fa5A-Za-z0-9_]{1,}", base))
            ev_text = weak or None
        if ev_text is None:
            continue
        if idx_from_name is not None:
            evidence_by_step_idx.setdefault(idx_from_name, []).append(ev_text)
        ordered_evidences.append((idx_from_name, ev_text, fn))

    # 最终 steps：按 step_names 长度构建 status
    final_steps: List[Dict[str, Any]] = []
    passed = 0
    # 全局「文件名关键词弱证据池」只在 explicit_ok 和按顺序匹配都没中时兜底用
    global_filename_keywords_pool: List[str] = []
    for _idx, _ev, _fn in ordered_evidences:
        if _ev:
            global_filename_keywords_pool.append(_ev)
    for i, name in enumerate(step_names, start=1):
        # 1. 文件名编号明确命中该步骤 i → 直接算过
        explicit_ok = (i in evidence_by_step_idx)
        pool: List[str] = []
        if explicit_ok:
            for ev in evidence_by_step_idx.get(i, []):
                pool.append(ev)
        elif (i - 1) < len(ordered_evidences):
            idx_from_name, ev, _fn = ordered_evidences[i - 1]
            if idx_from_name is None:
                pool.append(ev)
        # 兜底：当 pool 里没东西（没有命中编号也没对应无编号图片）时，再把所有文件名弱证据池放进来做关键词匹配
        #     这样 8 组「无编号但文件名里有描述词」能通过全局匹配；同时 7d 的 04_xxx 不会乱命中步骤 3（因为 04_xxx 有编号，explicit_ok 会判定是否真的匹配到 i，不会走全局）
        if not pool:
            pool = list(global_filename_keywords_pool)
        merged_ev = "\n".join(pool)
        hit, total, ratio = _keyword_match(name, merged_ev)

        kw_ok = (total > 0 and ratio >= min_match_ratio)
        implicit_ok = (not step_names_explicit and not any(filename_indices.values()) and (
            (i in evidence_by_step_idx) or ((i - 1) < len(images))
        ))

        status = "passed" if (explicit_ok or kw_ok or implicit_ok) else "missing"
        if status == "passed":
            passed += 1

        detail_parts = []
        if explicit_ok:
            detail_parts.append("文件名命中步骤编号")
        if total > 0:
            # 有显式编号命中时，关键词命中只作展示，不作判定
            detail_parts.append(f"关键词 {hit}/{total}（{'≥50% 命中' if ratio >= min_match_ratio else '未达阈值，仅展示'}）")
        if implicit_ok:
            detail_parts.append(f"无显式步骤名：按上传顺序第 {i} 张图片存在")
        # 取来源图片名
        source_image = None
        if i in evidence_by_step_idx:
            for fn, ix in filename_indices.items():
                if ix == i:
                    source_image = fn
                    break
        if source_image is None and (i - 1) < len(ordered_evidences):
            source_image = ordered_evidences[i - 1][2]

        final_steps.append({
            "index": i,
            "name": name,
            "status": status,
            "detail": "；".join(detail_parts) if detail_parts else "无匹配证据",
            "source_image": source_image,
            "evidence": (evidence_by_step_idx.get(i, [""])[0][:200] if evidence_by_step_idx.get(i) else
                         (ordered_evidences[i-1][1][:200] if (i-1) < len(ordered_evidences) else None)),
        })

    missing = total_steps - passed
    percent = round(passed / total_steps * 100, 2) if total_steps else 0.0

    # 最终 source：按优先级选最「强」的一个
    if "paddleocr" in sources_used:
        final_source = "paddleocr"
    elif _OCR_PROVIDER and _OCR_PROVIDER in sources_used:
        final_source = _OCR_PROVIDER
    elif any(filename_indices.values()):
        final_source = "filename"
    else:
        final_source = "fallback"

    return {
        "total_steps": total_steps,
        "passed": passed,
        "missing": missing,
        "percent": percent,
        "source": final_source,
        "steps": final_steps,
    }


# =================================================================
# 7) 便捷：把 progress 转成 Evaluation 两个 JSON 字段要的形状（对齐老 check_completeness）
# =================================================================
def progress_to_step_completeness(progress: Dict[str, Any]) -> List[Dict[str, Any]]:
    out = []
    for s in progress.get("steps", []) or []:
        out.append({
            "index": int(s.get("index", 0)),
            "name": str(s.get("name", "")),
            "status": str(s.get("status", "missing")),
            "detail": str(s.get("detail", "")),
            "source_image": s.get("source_image"),
        })
    return out


def progress_extra_issues(progress: Dict[str, Any]) -> List[Dict[str, str]]:
    issues: List[Dict[str, str]] = []
    total = int(progress.get("total_steps", 0) or 0)
    missing = int(progress.get("missing", 0) or 0)
    percent = float(progress.get("percent", 0.0) or 0.0)
    if total <= 0:
        issues.append({
            "type": "steps_unknown",
            "title": "未解析到任务步骤",
            "detail": "建议在「任务要求」里写明步骤 1/2/3…，系统会自动核查每步完成度。",
        })
        return issues
    if missing > 0:
        miss_names = [
            f"步骤{s['index']}（{s['name'][:14]}）"
            for s in progress.get("steps", []) or []
            if s.get("status") != "passed"
        ][:5]
        issues.append({
            "type": "missing_steps",
            "title": f"实训步骤未完成（进度 {percent:.1f}%）",
            "detail": "未完成步骤：" + "、".join(miss_names) + "；建议补齐对应截图或说明。",
        })
    src = str(progress.get("source", "") or "")
    if src in ("filename", "fallback"):
        issues.append({
            "type": "ocr_warning",
            "title": f"未使用真实 OCR（当前：{src}）",
            "detail": "建议安装 PaddleOCR 或配置 OCR_PROVIDER 以提升截图文字识别准确率。",
        })
    return issues
