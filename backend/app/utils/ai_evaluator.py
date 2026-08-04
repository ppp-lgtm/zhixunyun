import json
import sys
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from app.config import get_settings
from app.services.step_extractor import (
    parse_task_steps,
    _keyword_match,
    _normalize_for_match,
)


# ═══════════════════════════════════════════════════════════════════════
# AI 配置：惰性读取，不缓存模块导入时的 Settings 快照。
#   原因：有两个场景会导致"模块导入时 DEEPSEEK_API_KEY 为空但后续 .env
#   其实已经填好了"：
#     1) run.py database_bootstrap() 之前若某处间接 import 了本模块，
#        当时 .env 还没被 run.py 的 load_dotenv 补上；
#     2) 用户忘记复制 .env.example → .env 就启动了后端（旧 config.py），
#        之后才更新 .env.example（且新 config.py 支持 .env.example fallback）。
# ═══════════════════════════════════════════════════════════════════════
def _ds_key() -> str:
    return (get_settings().DEEPSEEK_API_KEY or "").strip()

def _ds_base() -> str:
    return (get_settings().DEEPSEEK_BASE_URL or "https://api.deepseek.com").strip()

def _si_key() -> str:
    return (get_settings().SILICON_API_KEY or "").strip()

def _si_base() -> str:
    return (get_settings().SILICON_BASE_URL or "https://api.siliconflow.cn/v1").strip()


# 模块级 __getattr__：任何 `from ai_evaluator import DEEPSEEK_API_KEY` 或
# `ai_evaluator.DEEPSEEK_API_KEY` 都会调用这里 → 每次实时从 Settings 取最新值。
_LAZY_ATTRS = {
    "DEEPSEEK_API_KEY": _ds_key,
    "DEEPSEEK_BASE_URL": _ds_base,
    "SILICON_API_KEY": _si_key,
    "SILICON_BASE_URL": _si_base,
}


def __getattr__(name: str):
    if name in _LAZY_ATTRS:
        return _LAZY_ATTRS[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# 延迟初始化 + 失效重建：只要 Key/Base 变了就丢掉旧 client。
_cache: dict = {"ds": (None, None), "si": (None, None)}  # (key_tuple, client_or_None)


def _get_client(kind: str):
    """kind ∈ {"ds","si"}。支持 Key 变化后自动重建 client。"""
    if kind == "ds":
        cur = (_ds_key(), _ds_base())
    else:
        cur = (_si_key(), _si_base())
    cached_key, cached_client = _cache[kind]
    if cached_key == cur and cached_client is not None:
        return cached_client
    api_key, base_url = cur
    if not api_key:
        _cache[kind] = (cur, None)
        return None
    try:
        client = OpenAI(api_key=api_key, base_url=base_url, timeout=20.0, max_retries=1)
    except Exception:
        client = None
    _cache[kind] = (cur, client)
    return client


# ═══════════════════════════════════════════════════════════════════════
# 兼容调用者"把 deepseek_client / silicon_client 当普通对象 import"：
#   task_manage.py: if ... or _ds_client is None: ...
#                   _ds_client.chat.completions.create(...)
#   evaluate.py:    if deepseek_client is None: ...
#                   deepseek_client.chat.completions.create(...)
#   statistics.py:  client.chat.completions.create(...)
# 用 proxy wrapper 让它在属性访问时懒加载真实 client。
# ═══════════════════════════════════════════════════════════════════════
class _ClientProxy:
    def __init__(self, kind: str):
        object.__setattr__(self, "_kind", kind)

    def _resolve(self):
        return _get_client(object.__getattribute__(self, "_kind"))

    def __getattr__(self, item):
        client = object.__getattribute__(self, "_resolve")()
        if client is None:
            raise AttributeError(
                f"_ClientProxy({object.__getattribute__(self, '_kind')}).{item}: "
                f"client is None (AI key not configured)"
            )
        return getattr(client, item)

    def __bool__(self):
        return object.__getattribute__(self, "_resolve")() is not None

    def __eq__(self, other):
        return other is None and bool(self) is False

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        client = object.__getattribute__(self, "_resolve")()
        return f"_ClientProxy(kind={object.__getattribute__(self, '_kind')!r}, client={'OK' if client else 'None'})"


# 把 proxy 注入到本模块（而不是走 __getattr__），避免它们被 import 时无法比较。
_self = sys.modules[__name__]
_self.deepseek_client = _ClientProxy("ds")  # type: ignore[attr-defined]
_self.silicon_client = _ClientProxy("si")   # type: ignore[attr-defined]



def evaluate(task_requirements, student_content, criteria):
    """DeepSeek 文字评价"""
    criteria_text = "、".join(criteria)

    prompt = f"""你是软件实训评价专家。请对照实训要求评价学生作业，按JSON格式返回。

实训要求：{task_requirements}

学生提交：{student_content}

评分维度：{criteria_text}

每个维度给0-100分和一句话理由，再加总分(加权平均)和总评。
只返回JSON，格式：{{"scores":[{{"name":"维度名","score":80,"reason":"理由"}}],"total":85,"comment":"总评"}}"""

    # is None 无法正确识别代理对象，改用 not <proxy> 判断（走 __bool__）
    if not deepseek_client:
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

    # is None 无法正确识别代理对象，改用 not <proxy> 判断（走 __bool__）
    if not silicon_client:
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
        if not deepseek_client:  # is None 无法正确识别代理对象，走 __bool__
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
    """检查 AI API Key 是否已配置。
    
    直接调用 _ds_key() getter 取最新值，而不是依赖 globals() 中的
    DEEPSEEK_API_KEY 名称绑定（模块内部函数不会走 __getattr__）。
    """
    k = _ds_key()
    test_values = {"", "sk-your-api-key", "sk-xxx", "sk-your-deepseek-key", "sk-your"}
    return bool(
        k
        and k not in test_values
        and (not k.startswith("sk-") or len(k) >= 16)
    )


def build_ai_misconfig_diagnosis() -> str:
    """当 is_ai_configured 为 False 时，返回可读的多段诊断文字（不含任何密钥）。

    包含：
    - 当前生效的 DEEPSEEK_API_KEY 的形态（空/示例占位/前缀正确但太短/已配置）
    - .env 加载搜索路径报告（哪个存在/哪个读取成功）
    - 若检测到 .env.example 中已填了真实 Key 但 .env 不存在，则给出明确提示
    - 一键修复命令（PowerShell）
    """
    lines: list[str] = []

    # ① 实际 Key 形态（走 getter，绕过 globals 查找）
    k = _ds_key() or ""
    if not k:
        lines.append("[1/4] 实际生效的 DEEPSEEK_API_KEY：空字符串（未读取到任何值）")
    elif k == "sk-your-api-key":
        lines.append("[1/4] 实际生效的 DEEPSEEK_API_KEY：示例占位符 sk-your-api-key（需要替换为真实 Key）")
    elif k.startswith("sk-") and len(k) < 16:
        lines.append(f"[1/4] 实际生效的 DEEPSEEK_API_KEY：sk- 前缀但长度仅 {len(k)}（疑似不完整复制）")
    else:
        lines.append(f"[1/4] 实际生效的 DEEPSEEK_API_KEY：已配置，前缀 {k[:6]}…，长度 {len(k)}")

    # ② .env 加载路径诊断
    try:
        from app.config import get_settings
        s = get_settings()
        report = getattr(s, "ENV_LOAD_REPORT", None) or []
        has_official = getattr(s, "ENV_HAS_OFFICIAL", False)
        ex_has = getattr(s, "ENV_EXAMPLE_HAS_DEEPSEEK", False)
        ex_path = getattr(s, "ENV_EXAMPLE_PATH", "")
    except Exception:
        report, has_official, ex_has, ex_path = [], False, False, ""

    lines.append("[2/4] .env 加载路径诊断（按优先级顺序搜索，后加载不覆盖已存在的同名变量）：")
    if not report:
        lines.append("      （无记录，可能 config.py 版本过旧）")
    else:
        for idx, r in enumerate(report, 1):
            # ✓ / ✗ / - 图标
            if r.get("loaded"):
                mark = "✅ LOADED"
            elif str(r.get("reason", "")).startswith("SKIP"):
                mark = "⏭  SKIP  "
            elif str(r.get("reason", "")) == "NOT FOUND":
                mark = "⚠️ MISS  "
            else:
                mark = "❌ FAIL  "
            path_disp = r.get("path", "")
            # 过长的路径只取 basename + 前 1 级
            try:
                import pathlib
                _p = pathlib.Path(path_disp)
                path_disp_short = f"...\\{_p.parent.name}\\{_p.name}" if len(path_disp) > 60 else path_disp
            except Exception:
                path_disp_short = path_disp
            lines.append(f"      {idx:>2}. {mark} | {r.get('comment','')}")
            lines.append(f"            path   = {path_disp_short}")
            lines.append(f"            reason = {r.get('reason','')}")

    # ③ 关键提示：.env.example 有 Key 但没读到 = 典型漏复制场景
    if ex_has and not is_ai_configured():
        lines.append("[3/4] ⚠️  检测到典型场景：.env.example 中已填了真实 Key，但当前没生效！")
        lines.append(f"      .env.example 路径 = {ex_path or '(未知)'}")
        lines.append("      原因：代码默认只读取 .env 文件，不读 .env.example（避免误把示例值当真实值）。")
        lines.append("      但本次 config.py 已加了 fallback，之所以仍不生效，通常是：")
        lines.append("        a) 启动后端的进程是在你修改 .env.example 之前启动的（进程环境变量只读一次）")
        lines.append("        b) 同时存在其他正式 .env（优先级更高），把 .env.example fallback 跳过了")
    else:
        lines.append("[3/4] .env.example 中 DEEPSEEK_API_KEY 状态：" + (
            "已填真实 Key" if ex_has else (
                "未检测到已填 Key（仍是 sk-your-api-key / sk-xxx 占位或空）"
            )
        ))

    # ④ 一键修复命令
    lines.append("[4/4] 一键修复（Windows PowerShell，复制执行后重启后端）：")
    lines.append('      方案A（推荐）：复制 .env.example 为正式 .env，不影响 .gitignore 规则')
    lines.append('          cd g:\\b1提交物\\code\\zhixunyun')
    lines.append('          if (-not (Test-Path .env)) { Copy-Item .env.example .env } else')
    lines.append('          { Write-Host ".env 已存在，若 Key 仍空请手动编辑： notepad .env" }')
    lines.append('          # 然后重启后端：Ctrl+C 再 python run.py')
    lines.append('      方案B（直接编辑 .env.example 已够用，且仅本次项目用）：.env.example fallback 已支持')
    lines.append('          只需 Ctrl+C 重启后端 python run.py，新的 config.py 就会在无 .env 时自动读 .env.example')
    lines.append('')
    lines.append('Key 申请：https://platform.deepseek.com/api_keys （新用户送额度）')
    return "\n".join(lines)


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
    """AI 判定单步（优先但非强制，失败回退 rule）。
    
    注意：`not deepseek_client` 走代理对象 __bool__（自动解析真实 client）。
    """
    if not is_ai_configured() or not deepseek_client:
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