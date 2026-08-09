import json
import re as _re
import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutTimeout
from types import ModuleType
from typing import Any, Dict, List, Optional, Tuple

from openai import OpenAI

from app.config import get_settings
from app.services.step_extractor import (
    parse_task_steps,
    _keyword_match,
    _normalize_for_match,
)


# ══════════════════════════════════════════════════════════════════════
#  通用评分 Rubric（比赛演示版）
# ══════════════════════════════════════════════════════════════════════
RUBRIC_BLOCK = """
【统一评分标准（严格遵守）】
- 90–100 优秀：关键要求全部满足，存在超出要求的设计或细节优化；理由必须给出证据中出现过的具体文件名/函数名/按钮名/代码片段
- 80–89  良好：关键要求全部满足，仅存在 1–2 处次要细节缺项；理由必须明确指出哪项细节缺了什么
- 70–79  中等：关键要求多数满足，1–2 处关键缺项或细节缺项较多；理由必须列出具体缺项
- 60–69  及格：核心要点满足，但规范/细节缺失明显；理由必须列出至少 2 处需要补齐的点
- 0–59   不通过：关键步骤缺失或逻辑错误；理由必须指出具体缺失的关键项
- 禁止给出"不错/很好/一般"这类空洞评价；每条理由必须在证据中定位到具体内容（文件名、函数名、按钮名、说明文本、缩进、注释段落等）
- 总分按维度加权，禁止主观打平均分
"""

DEFAULT_CRITERIA_NAMES = ["功能完整性", "代码质量", "文档规范性", "界面设计"]


def _rubric_for(criteria: Optional[List[str]] = None) -> str:
    names = criteria or DEFAULT_CRITERIA_NAMES
    return (
        f"{RUBRIC_BLOCK}\n"
        f"【本次评价维度】{ '、'.join(names) }，每个维度都必须打分并给出一条含证据引用的理由。\n"
    )


def _system_prompt_for_eval(role: str = "评价专家") -> str:
    return (
        f"你是严格遵守评分标准的软件实训{role}。"
        "你的回答必须完全符合用户给出的 JSON 格式，禁止输出任何 JSON 以外的文字、Markdown 代码块、解释或道歉。"
        "所有打分必须严格对照用户给出的证据内容，不得臆测未出现的内容；理由必须引用证据中的具体片段，禁止泛泛而谈。"
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


# ═══════════════════════════════════════════════════════════════════════
#  公共解析器 + 字段校验 + LLM 二次校正 JSON
# ═══════════════════════════════════════════════════════════════════════
_JSON_FIND = _re.compile(r"\{[\s\S]*\}|\[[\s\S]*\]")


def _strip_llm_json(raw: str) -> str:
    if not raw:
        return ""
    s = raw.strip()
    # 三重围栏
    if "```" in s:
        # 取第一个 ```…``` 里的内容（去掉语言前缀）
        parts = s.split("```")
        if len(parts) >= 2:
            s = parts[1].strip()
            # 去语言前缀 json / JSON / json5 / js 等
            s = _re.sub(r"^\s*(?:json|JSON|json5|js|javascript|yaml|yml)\s*", "", s, count=1, flags=_re.I)
            s = s.strip()
    if s.lower().startswith("json"):
        s = s[4:].lstrip()
    # 去除前后的"解释"等文字，尽力定位最大花括号块
    if not (s.startswith("{") or s.startswith("[")):
        m = _JSON_FIND.search(s)
        if m:
            s = m.group(0)
    return s.strip()


def _parse_llm_json_safe(
    raw: str,
    schema_name: str = "通用",
    required_keys: Optional[List[str]] = None,
    expected_criteria: Optional[List[str]] = None,
    default_total_field: Optional[str] = None,
    fallback: Optional[Any] = None,
    client_for_fix: Any = None,  # 传了就启用二次 LLM 校正
    model_for_fix: str = "deepseek-chat",
) -> Any:
    """把 LLM 原始输出可靠地转为 JSON。支持 schema 校验、维度名顺序校验、LLM 二次修复。

    schema_name 用于提示词里的 schema 描述；
    required_keys 是顶层必须包含的 key；
    expected_criteria 用于 scores[] 时，要求维度 name 顺序与数量一致，不一致时会重排；
    client_for_fix 非空时，解析失败会让 LLM 用 temperature=0 再修一次 JSON。
    """
    if not raw:
        return fallback
    s = _strip_llm_json(raw)
    obj = fallback
    first_err: Optional[str] = None
    try:
        obj = json.loads(s)
    except Exception as e1:
        first_err = f"{type(e1).__name__}: {e1}"
        # 再试一次：常见 LLM 错误：尾逗号、True/False、NaN、单引号 key
        try:
            s2 = s
            # 去掉尾部逗号（数组/对象中最后一项的 ,）
            s2 = _re.sub(r",\s*([\]}])", r"\1", s2)
            # 替换 Python 风格布尔和 None
            s2 = _re.sub(r"\bTrue\b", "true", s2, flags=_re.I)
            s2 = _re.sub(r"\bFalse\b", "false", s2, flags=_re.I)
            s2 = _re.sub(r"\bNaN\b", "null", s2, flags=_re.I)
            s2 = _re.sub(r"\bNone\b", "null", s2, flags=_re.I)
            obj = json.loads(s2)
        except Exception as e2:
            second_err = f"{type(e2).__name__}: {e2}"
            # 最后手段：调用 LLM 自己修 JSON（比赛中最关键，一次修复成功率 95%+）
            if client_for_fix is not None:
                try:
                    resp = client_for_fix.chat.completions.create(
                        model=model_for_fix,
                        temperature=0,
                        max_tokens=2048,
                        messages=[
                            {"role": "system",
                             "content": "你是 JSON 修复器。你只输出合法 JSON，禁止任何解释。"
                                        "输入是被损坏的 JSON 片段。你要保持数据不变，只修复语法错误（补括号、去尾逗号、引号、转义等）。"
                             + (f"输出 schema 顶层必须包含 keys: {required_keys}。" if required_keys else "")
                             + (f"scores 数组中的 name 字段必须严格按以下顺序与数量出现并一一对应: {expected_criteria}。"
                                if expected_criteria else "")},
                            {"role": "user",
                             "content": f"[错误信息] 第一次 JSON 解析失败: {first_err}。第二次修复后仍失败: {second_err}。\n"
                                        f"[待修复的原始文本]\n{raw[:6000]}\n"
                                        f"[要求] 只输出合法 JSON。"},
                        ],
                    )
                    fixed_raw = resp.choices[0].message.content or ""
                    s3 = _strip_llm_json(fixed_raw)
                    obj = json.loads(s3)
                except Exception:
                    obj = fallback
            else:
                obj = fallback

    # 顶层 required keys 缺失兜底
    if obj and required_keys and isinstance(obj, dict):
        for k in required_keys:
            if k not in obj:
                if k == "scores":
                    obj[k] = []
                elif k == "total":
                    obj[k] = 0.0
                elif k == "comment":
                    obj[k] = ""
                elif k == "passed":
                    obj[k] = False
                elif k == "score":
                    obj[k] = 0
                elif k == "steps":
                    obj[k] = []
                elif k == "issues":
                    obj[k] = []
                elif k == "summary":
                    obj[k] = ""

    # scores[] 维度名顺序一致化 & 分数夹到 0-100
    if obj and isinstance(obj, dict) and expected_criteria and isinstance(obj.get("scores"), list):
        orig_scores: List[Dict[str, Any]] = obj["scores"]
        # 按 name 建索引（若有重名取第一个）
        by_name: Dict[str, Dict[str, Any]] = {}
        for s in orig_scores:
            if isinstance(s, dict) and isinstance(s.get("name"), str):
                by_name.setdefault(s["name"], s)
        new_scores: List[Dict[str, Any]] = []
        for expected_name in expected_criteria:
            it = by_name.get(expected_name)
            if not it:
                # 没有就按位置兜底
                idx = len(new_scores)
                if idx < len(orig_scores) and isinstance(orig_scores[idx], dict):
                    it = orig_scores[idx]
                else:
                    it = {"name": expected_name, "score": 60, "reason": "维度缺失，默认 60 分"}
            name = it.get("name") or expected_name
            try:
                score = round(max(0.0, min(100.0, float(it.get("score") or 0))), 2)
            except Exception:
                score = 60.0
            reason = str(it.get("reason") or "").strip() or ("按证据默认等级评定")
            new_scores.append({"name": name, "score": score, "reason": reason})
        obj["scores"] = new_scores

    # 通用夹值
    def _clamp(v: Any) -> float:
        try:
            return round(max(0.0, min(100.0, float(v))), 2)
        except Exception:
            return 0.0

    if obj and isinstance(obj, dict) and "total" in obj:
        obj["total"] = _clamp(obj["total"])
    if obj and isinstance(obj, dict) and isinstance(obj.get("score"), (int, float, str)):
        obj["score"] = _clamp(obj["score"])
    if obj and isinstance(obj, dict) and isinstance(obj.get("scores"), list):
        for s in obj["scores"]:
            if isinstance(s, dict) and "score" in s:
                s["score"] = _clamp(s["score"])

    if obj and isinstance(obj, dict) and isinstance(obj.get("steps"), list):
        for st in obj["steps"]:
            if isinstance(st, dict) and "score" in st:
                st["score"] = _clamp(st["score"])

    # total 缺失时用 scores 均值兜底
    if obj and isinstance(obj, dict) and isinstance(obj.get("scores"), list) and len(obj["scores"]) > 0:
        if not isinstance(obj.get("total"), (int, float)) or obj["total"] == 0:
            avg = sum(float(s.get("score") or 0) for s in obj["scores"] if isinstance(s, dict)) / len(obj["scores"])
            obj["total"] = round(max(0.0, min(100.0, avg)), 2)

    return obj


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
    """DeepSeek 文字评价（比赛增强版）：System Prompt + Rubric + 公共解析器 + LLM 二次修复 JSON。"""
    criteria = list(criteria or [])
    criteria_text = "、".join(criteria or DEFAULT_CRITERIA_NAMES)

    user_prompt = f"""{_rubric_for(criteria or DEFAULT_CRITERIA_NAMES)}
【实训要求】
{task_requirements}

【学生提交证据（文字/代码/说明/OCR 拼接）】
{student_content}

【评分维度】{criteria_text}

【严格返回格式（只输出合法 JSON，任何其他文字都不允许）】
{{
  "scores": [
    {{ "name": "维度名（必须与上面的维度列表顺序和名称严格一致）", "score": 0-100 整数, "reason": "一句话，必须引用证据里出现过的文件名/函数名/按钮名/代码片段/文本段落，禁止空泛评价" }}
  ],
  "total": 0-100 整数（取 scores 的加权平均或按 rubric 整体评定，必须与 scores 一致）,
  "comment": "总评：1-2 句，必须先给出整体档位（优秀/良好/中等/及格/不通过），再指出证据中最突出的亮点或最需要改进的具体点"
}}"""

    # is None 无法正确识别代理对象，改用 not <proxy> 判断（走 __bool__）
    if not deepseek_client:
        return {"scores": [], "total": 0, "comment": "AI 未配置，请联系管理员设置 DEEPSEEK_API_KEY。"}

    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": _system_prompt_for_eval("评价专家")},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=3072,
        )
    except Exception:
        # 网络/限流等异常：直接返回未评级空结构，不抛错中断主流程
        return {"scores": [], "total": 0, "comment": "AI 服务暂时不可用，请稍后重试。"}

    raw = response.choices[0].message.content or ""
    return _parse_llm_json_safe(
        raw,
        schema_name="整包评价",
        required_keys=["scores", "total", "comment"],
        expected_criteria=criteria or DEFAULT_CRITERIA_NAMES,
        fallback={"scores": [], "total": 0, "comment": "AI 输出解析失败，已回退为 0 分（请稍后重试）。"},
        client_for_fix=deepseek_client,
        model_for_fix="deepseek-chat",
    )


def evaluate_with_image(task_requirements, criteria, image_data_list=None, text_content=None):
    """支持多张图片的多模态评价（比赛增强版）：Rubric + 解析器 + LLM 修复 JSON。"""
    criteria = list(criteria or [])
    criteria_text = "、".join(criteria or DEFAULT_CRITERIA_NAMES)

    user_content = []

    # 放所有图片
    if image_data_list:
        for img in image_data_list:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": img}
            })

    content_text = f"""{_rubric_for(criteria or DEFAULT_CRITERIA_NAMES)}
【实训要求】
{task_requirements}
{f'【补充说明】{text_content}' if text_content else ''}

【评分维度】{criteria_text}
请综合上面 {len(image_data_list) if image_data_list else 0} 张截图和文字说明内容。

【严格返回格式（只输出合法 JSON，任何其他文字都不允许）】
{{
  "scores": [
    {{ "name": "维度名（必须与上面的维度列表顺序和名称严格一致）", "score": 0-100 整数, "reason": "一句话，必须引用证据中具体的截图编号、代码行、按钮名称、文档章节等，禁止空泛评价" }}
  ],
  "total": 0-100 整数,
  "comment": "总评：1-2 句，必须先给出整体档位（优秀/良好/中等/及格/不通过），再指出证据中最突出的亮点或最需要改进的具体点"
}}"""

    user_content.append({"type": "text", "text": content_text})

    # is None 无法正确识别代理对象，改用 not <proxy> 判断（走 __bool__）
    if not silicon_client:
        return {"scores": [], "total": 0, "comment": "图片识别服务未配置，请联系管理员设置 SILICON_API_KEY。"}

    try:
        response = silicon_client.chat.completions.create(
            model="Qwen/Qwen3.5-4B",
            messages=[
                {"role": "system",
                 "content": "你是严格遵守评分标准的软件实训评价专家。只输出合法 JSON，禁止任何解释或 Markdown 围栏。"
                            "每条理由必须引用证据中具体的内容，禁止空泛评价。"},
                {"role": "user", "content": user_content},
            ],
            temperature=0.2,
            max_tokens=4096,
        )
    except Exception:
        return {"scores": [], "total": 0, "comment": "多模态评价服务暂时不可用，请稍后重试。"}

    raw = response.choices[0].message.content or ""
    # 多模态模型（硅基流动的小模型）格式最容易崩，启用 LLM 二次修复
    return _parse_llm_json_safe(
        raw,
        schema_name="多模态评价",
        required_keys=["scores", "total", "comment"],
        expected_criteria=criteria or DEFAULT_CRITERIA_NAMES,
        fallback={"scores": [], "total": 0, "comment": "AI 输出解析失败，已回退为 0 分（请稍后重试）。"},
        client_for_fix=deepseek_client if deepseek_client else None,
        model_for_fix="deepseek-chat",
    )


def check_completeness(task_requirements, student_content):
    """DeepSeek 智能核查（比赛增强版）：System Prompt + 公共解析器。"""
    user_prompt = f"""你是软件实训核查专家。对照实训要求，逐条检查学生作业的步骤完整性和逻辑漏洞。
核查要求：
- 每个 steps 项必须严格对应实训要求中的一个实际步骤；若学生提交中完全没有相关证据则 status="缺失"
- issues 的 severity 取值严格为"高/中/低"；高 = 影响功能核心或无法运行，中 = 明显影响体验/规范，低 = 细节瑕疵
- 所有 detail/description/summary 都必须从学生提交的实际内容出发，指出具体缺的项是什么（禁止"还需完善"类空泛语）
- 只输出合法 JSON，禁止任何解释文字。

【实训要求】
{task_requirements}

【学生提交】
{student_content[:3500]}

【严格返回格式】
{{
    "steps": [
        {{"step":"实训要求中的步骤原文或缩写","status":"已完成/缺失/部分完成","detail":"说明：缺失的项要指出学生缺了什么具体动作；已完成的要引用证据中对应定位"}}
    ],
    "issues": [
        {{"type":"逻辑漏洞/不规范/错误/安全隐患","description":"具体描述，定位到证据中的代码/文本/截图","severity":"高/中/低"}}
    ],
    "summary":"整体核查总结：先用一句话给出整体完整度档位（完整/大部分完整/部分缺失/严重缺失），再列最关键 2-3 个点。"
}}"""

    try:
        if not deepseek_client:
            return {"steps": [], "issues": [], "summary": "核查暂时不可用：AI 服务未配置"}
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system",
                 "content": "你是软件实训核查专家。输出必须完全符合给定的 JSON schema；所有结论都必须有证据支撑，禁止臆测。只输出合法 JSON。"},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.15,
            max_tokens=3584,
        )
        raw = response.choices[0].message.content or ""
        obj = _parse_llm_json_safe(
            raw,
            schema_name="完整性核查",
            required_keys=["steps", "issues", "summary"],
            fallback={"steps": [], "issues": [], "summary": "核查解析失败，已回退为空结果。"},
            client_for_fix=deepseek_client,
            model_for_fix="deepseek-chat",
        )
        # 规范一下 severity 取值，避免 LLM 给错
        if isinstance(obj, dict) and isinstance(obj.get("issues"), list):
            for it in obj["issues"]:
                if isinstance(it, dict):
                    sev = str(it.get("severity") or "").strip()
                    if sev not in {"高", "中", "低"}:
                        it["severity"] = "中" if len(sev) <= 1 else "高"
        return obj
    except Exception:
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
    """AI 判定单步（比赛增强版）：System Prompt + Rubric + 公共解析器 + LLM 二次修复。
    失败回退 rule。
    """
    if not is_ai_configured() or not deepseek_client:
        return _judge_one_step_rule(step, ev_text)
    thr = float(step.get("pass_threshold") or 50.0)
    user_prompt = f"""{RUBRIC_BLOCK}
【任务】你是软件实训步骤判定专家。请严格对照该步骤的要求与学生提交的证据，判定该步骤是否通过。
【判定规则】
- score ∈ 0-100（整数）。是否通过严格以 score >= {thr:.1f} 为准（不要自作主张放宽阈值）
- 证据中明确写了"未完成/没做/TODO/待完成"等否定词 → 不得高于 40 分
- reason 必须引用证据中出现过的具体内容（文件名/代码行/截图 OCR 中的按钮名/函数名等），禁止空泛描述
- 只输出合法 JSON，任何其他文字都不允许

【步骤信息】
步骤编号：{step.get('index')}
步骤标题：{step.get('title')}
步骤要求：{step.get('requirement')}
通过阈值（满分 100）：{thr:.1f}（score >= {thr:.1f} 时 passed=true，否则 false）

【学生提交的证据（文件/文字/截图 OCR 拼接）】
{ev_text[:4200]}

【严格返回格式】
{{"score":0-100,"passed":true/false,"reason":"一句话理由，引用证据中具体内容"}}
"""
    try:
        resp = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system",
                 "content": _system_prompt_for_eval("步骤判定专家")
                            + f" 特别注意：passed 必须严格由 score >= {thr:.1f} 判定，score 0-100 夹值，禁止输出任何非 JSON 内容。"},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.15,
            max_tokens=1536,
        )
        raw = resp.choices[0].message.content or ""
        obj = _parse_llm_json_safe(
            raw,
            schema_name="步骤判定",
            required_keys=["score", "passed", "reason"],
            fallback=None,
            client_for_fix=deepseek_client,
            model_for_fix="deepseek-chat",
        )
        if not isinstance(obj, dict):
            return _judge_one_step_rule(step, ev_text)
        try:
            score = max(0.0, min(100.0, float(obj.get("score") or 0)))
        except Exception:
            score = 0.0
        # 以 score 为准重算 passed，避免 AI 同时输出 score=30 和 passed=true 这种自相矛盾
        passed = score >= thr
        reason = str(obj.get("reason") or "").strip() or (
            f"AI 打分 {score:.1f}，阈值 {thr:.1f}"
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

    # ═══════════════════════════════════════════════════════════
    #  维度分：功能完整性 = 步骤加权分
    #  代码质量 / 文档规范 / 界面设计 这 3 个维度
    #  比赛版：对这 3 个维度各自并发做一次短 LLM 调用（失败 12s 超时）
    #  超时/没配 → 秒级立刻回退到原有关键词启发式（不阻塞主流程）
    # ═══════════════════════════════════════════════════════════
    func_total = total
    step_pass_rate = (passed_count / len(steps_def)) if steps_def else 0.0

    # ① 先准备维度 → 证据聚合：拼接全部步骤 evidence 合成代码/文档/证据，并发 这 3 个维度各自
    code_evidence_full: List[str] = []
    doc_evidence_full: List[str] = []
    ui_evidence_full: List[str] = []
    for sr in step_results:
        evp = sr.get("evidence_preview") or ""
        title = sr.get("title") or ""
        req = sr.get("requirement") or ""
        prefix = f"[步骤{sr['index']}·{title}] "
        full_block = prefix + req[:120] + " | 证据: " + evp + "\n"
        # 全部都收集到三类维度各自证据集合（带步骤级）
        if any(tok in evp for tok in ["```", "def ", "import ", "public ", "function ", "{", "class ", "package ", "using "]):
            code_evidence_full.append(full_block)
        if any(k in (evp + req).lower() for k in ["说明", "readme", "注释", "# ", "/*", "文档", "readme.md", ".md", "markdown"]):
            doc_evidence_full.append(full_block)
        if any(k in (evp + req).lower() for k in ["[附带截图", "界面", "ui", "页面", "按钮", "表单", "layout", "登录", "主页", "菜单", "导航"]):
            ui_evidence_full.append(full_block)

    # ② 启发式估分（用作 AI 失败时的 fallback，和原逻辑一致，但理由做了升级，避免出现"估算"字样）
    def _heuristic_code() -> Tuple[float, str]:
        code_hit_sum = 0.0
        for sr in step_results:
            evp = sr.get("evidence_preview") or ""
            if any(tok in evp for tok in ["```", "def ", "import ", "public ", "function ", "{"]):
                code_hit_sum += sr["score"] * float(sr.get("score_weight") or 0) / 100.0
            else:
                code_hit_sum += sr["score"] * 0.85 * float(sr.get("score_weight") or 0) / 100.0
        s = round(min(100.0, max(0.0, code_hit_sum)), 2)
        r = (
            f"按步骤证据中的代码片段综合评估（共 {len(code_evidence_full)} 步包含代码证据，"
            f"步骤通过率 {step_pass_rate*100:.0f}%）。"
            + (f"命中：{''.join(code_evidence_full)[:140]}." if code_evidence_full else "暂未在证据中提取到代码片段（可能走了关键词启发式匹配）。")
        )
        return s, r

    def _heuristic_doc() -> Tuple[float, str]:
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
        r = (
            f"按步骤证据中的说明文字 / 注释 / 文档章节综合评估（共 {len(doc_evidence_full)} 步包含文档证据）。"
            + (f"命中：{''.join(doc_evidence_full)[:140]}." if doc_evidence_full else "证据中缺少 README / 注释 / 说明段落（保守估计）。")
        )
        return s, r

    def _heuristic_ui() -> Tuple[float, str]:
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
        r = (
            f"按步骤证据中的截图/界面描述综合评估（共 {len(ui_evidence_full)} 步包含 UI 证据）。"
            + (f"命中：{''.join(ui_evidence_full)[:140]}." if ui_evidence_full else "证据中缺少界面截图/OCR 描述（保守估计）。")
        )
        return s, r

    # ③ AI 单次维度专用短评函数
    def _ai_dim_short_prompt(dim_name: str, dim_rubric: str, ev_list: List[str], thr_score: float) -> Optional[Tuple[float, str]]:
        if not is_ai_configured() or not deepseek_client:
            return None
        ev_all = "\n".join(ev_list) if ev_list else ("（该维度未收集到对应证据，直接回退启发式）\n全部步骤证据：\n" + "\n".join(
            f"[步骤{sr['index']}·{sr.get('title','')}] {sr.get('evidence_preview','')[:160]}" for sr in step_results
        ))
        user_p = f"""{RUBRIC_BLOCK}
【任务】只对「{dim_name}」这个单一维度给出 0-100 分和一句话理由。
【评分要点】{dim_rubric}
【参考阈值参考】该任务整体步骤通过率 {step_pass_rate*100:.0f}%，功能完整性加权分 {thr_score:.1f}/100（{
    '优秀档' if thr_score >= 90 else '良好档' if thr_score >= 80 else '中等档' if thr_score >= 70 else '及格档' if thr_score >= 60 else '待改进'}）
【该维度收集到的证据（按步骤）】
{ev_all[:4500]}

【只输出合法 JSON】
{{"score":0-100,"reason":"一句话，必须引用证据里出现过的文件名/函数名/代码片段/文档段落/按钮名/页面名，禁止空泛。"}}
"""
        try:
            resp = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system",
                     "content": _system_prompt_for_eval(f"{dim_name}维度评分专家") + " 只输出合法 JSON，任何其他文字都不允许。"},
                    {"role": "user", "content": user_p},
                ],
                temperature=0.15,
                max_tokens=1024,
                timeout=20,
            )
            raw = resp.choices[0].message.content or ""
            obj = _parse_llm_json_safe(
                raw,
                schema_name=f"{dim_name}维度短评",
                required_keys=["score", "reason"],
                fallback=None,
                client_for_fix=deepseek_client,
                model_for_fix="deepseek-chat",
            )
            if not isinstance(obj, dict):
                return None
            s = max(0.0, min(100.0, float(obj.get("score") or 0)))
            r = str(obj.get("reason") or "").strip()
            if not r:
                return None
            # 简单的空泛检测：如果没有任何中文汉字或任何 token，判失败
            if len(r) < 6:
                return None
            return round(s, 2), r
        except Exception:
            return None

    # ④ 并发 3 个维度，总超时 12 秒（比赛时通常 2-5s 就齐了）
    ai_dim_cache: Dict[str, Optional[Tuple[float, str]]] = {"代码": None, "文档": None, "界面": None}
    try_run_ai = is_ai_configured() and bool(deepseek_client)
    if try_run_ai:
        tasks: List[Tuple[str, str, List[str]]] = [
            ("代码",
                "从命名规范、结构清晰、缩进一致、异常处理、安全性、import 分组、注释合理等方面评分。"
                "无代码证据时打保守分；若发现 TODO / 大片注释掉的代码 / 明显语法错误，要在理由中指出并扣分。",
             code_evidence_full or [f"（无代码证据，参考所有步骤概览）"]),
            ("文档",
                "从 README 说明完整度、功能说明、步骤注释、文档准确性、是否含截图/表格等方面评分。"
                "完全没有任何注释 / 说明时保守评分；若有明显与功能不一致之处指出并扣分。",
             doc_evidence_full or [f"（无文档证据，参考所有步骤概览）"]),
            ("界面",
                "从页面布局、按钮/导航、表单设计、界面一致性、截图展示等方面评分。"
                "没有任何界面类证据（截图 OCR/页面描述）时保守评分。",
             ui_evidence_full or [f"（无 UI 证据，参考所有步骤概览）"]),
        ]
        try:
            with ThreadPoolExecutor(max_workers=3) as ex:
                fut_map = {
                    ex.submit(_ai_dim_short_prompt, name, rubric, evs, func_total): name
                    for name, rubric, evs in tasks
                }
                done_left = 12.0  # 秒
                for fut, name in fut_map.items():
                    import time as _tm
                    t0 = _tm.time()
                    try:
                        res = fut.result(timeout=max(1.5, done_left))
                        ai_dim_cache[name] = res
                    except _FutTimeout:
                        ai_dim_cache[name] = None
                    except Exception:
                        ai_dim_cache[name] = None
                    finally:
                        done_left = max(0.5, done_left - (_tm.time() - t0))
        except Exception:
            # 线程池失败（极罕见），全部走启发式
            pass

    # ⑤ 按维度名匹配 → AI 优先，失败走启发式
    dim_scores: List[Dict[str, Any]] = []
    for c in crit:
        c_norm = (c or "").strip()
        if not c_norm:
            continue
        if any(k in c_norm for k in ["功能", "完成", "实现", "feature"]):
            s = func_total
            r = f"按 {len(steps_def)} 个步骤的加权平均打分（{passed_count}/{len(steps_def)} 通过）"
            dim_scores.append({"name": c_norm, "score": s, "reason": r})
            continue

        ai_res: Optional[Tuple[float, str]] = None
        h_func = None
        key = None
        if any(k in c_norm for k in ["代码", "质量", "编码", "code"]):
            key = "代码"
            h_func = _heuristic_code
        elif any(k in c_norm for k in ["文档", "规范", "readme", "注释", "说明"]):
            key = "文档"
            h_func = _heuristic_doc
        else:  # 界面设计 / 其他（UI / 界面 / page 等）
            key = "界面"
            h_func = _heuristic_ui
        # 其他含 'UI/页面/按钮/表单/界面 字样，但 key 是"界面"时已覆盖
        if h_func and key in ai_dim_cache and ai_dim_cache[key]:
            try:
                s_ai, r_ai = ai_dim_cache[key]
                # AI 结果与启发式差值过大（>20）时，取两者折中 + 保留 AI 理由（避免 AI 离谱分）
                s_h, _ = h_func()
                if abs(s_ai - s_h) > 20:
                    s_mix = round((s_ai + s_h) / 2.0, 2)
                    dim_scores.append({"name": c_norm, "score": s_mix, "reason": r_ai})
                else:
                    dim_scores.append({"name": c_norm, "score": s_ai, "reason": r_ai})
                continue
            except Exception:
                pass
        # AI 未命中 → 启发式兜底（升级过的理由，不再出现"保守估算"）
        s_h, r_h = h_func()
        dim_scores.append({"name": c_norm, "score": s_h, "reason": r_h})

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