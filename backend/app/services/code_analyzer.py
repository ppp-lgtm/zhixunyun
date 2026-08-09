"""
知训云 D1 阶段：代码静态分析 + 抄袭相似度检测（纯逻辑层）
- 纯函数、不依赖 DB、不依赖 AI API，本地可快速自测
- 指标：LOC / 注释率 / 函数数 / 类数 / 圈复杂度估算 / TODO / FIXME
- 相似度：token 级 Jaccard（标识符 + 关键字，去空格/注释）

对外推荐使用的函数：
  analyze_code_file(source: str, ext: str, filename: str="")
  analyze_code_files(files: List[Tuple[filename, source]])
  jaccard_similarity(tokens_a, tokens_b)
  detect_plagiarism(student_analyses: Dict[Any, CodeArchive], threshold=0.85)
  to_evaluation_dimensions(archive, top_pair=None)   # 对齐 ai_evaluator.evaluate 的返回
  to_logic_issues(archive, top_pair=None)            # 对齐 check_completeness 返回的 issues
"""
from __future__ import annotations

import re
import io
import zipfile
from typing import Any, Dict, List, Optional, Tuple


# =================================================================
# 1. 关键字 / token 正则（按语言分）
# =================================================================
_PY_KEYWORDS = {
    'False','None','True','and','as','assert','async','await','break','class','continue',
    'def','del','elif','else','except','finally','for','from','global','if','import','in',
    'is','lambda','nonlocal','not','or','pass','raise','return','try','while','with','yield',
    'match','case','type','alias',
}
_JAVA_KEYWORDS = {
    'abstract','assert','boolean','break','byte','case','catch','char','class','const','continue',
    'default','do','double','else','enum','extends','final','finally','float','for','goto','if',
    'implements','import','instanceof','int','interface','long','native','new','package','private',
    'protected','public','return','short','static','strictfp','super','switch','synchronized','this',
    'throw','throws','transient','try','void','volatile','while','record','sealed','non-sealed',
    'permits','var','yield',
}
_CPP_KEYWORDS = {
    'alignas','alignof','and','and_eq','asm','auto','bitand','bitor','bool','break','case',
    'catch','char','char8_t','char16_t','char32_t','class','compl','concept','const','consteval',
    'constexpr','constinit','const_cast','continue','co_await','co_return','co_yield','decltype',
    'default','delete','do','double','dynamic_cast','else','enum','explicit','export','extern',
    'false','float','for','friend','goto','if','inline','int','long','mutable','namespace','new',
    'noexcept','not','not_eq','nullptr','operator','or','or_eq','private','protected','public',
    'register','reinterpret_cast','requires','return','short','signed','sizeof','static',
    'static_assert','static_cast','struct','switch','template','this','thread_local','throw',
    'true','try','typedef','typeid','typename','union','unsigned','using','virtual','void',
    'volatile','wchar_t','while','xor','xor_eq','override','final','import','module',
}

# 标识符 token（去掉纯数字）
_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
# 行内注释、整行注释、字符串字面量（简单处理，支持 "..." 和 '...'）
_PY_LINE_COMMENT_RE = re.compile(r"#.*$", re.MULTILINE)
_JAVA_CPP_LINE_COMMENT_RE = re.compile(r"//.*?$", re.MULTILINE)
_BLOCK_C_STYLE_RE = re.compile(r"/\*[\s\S]*?\*/")
_PY_TRIPLE_SINGLE = re.compile(r"'''[\s\S]*?'''")
_PY_TRIPLE_DOUBLE = re.compile(r'"""[\s\S]*?"""')
_STRING_LITERAL_SINGLE = re.compile(r"'(?:\\.|[^'\\\n])*'")
_STRING_LITERAL_DOUBLE = re.compile(r'"(?:\\.|[^"\\\n])*"')

_BRANCH_PY = re.compile(r"\b(if|elif|for|while|except|and|or|match|case|catch|finally)\b")
_BRANCH_JAVA = re.compile(r"\b(if|else|for|while|case|catch|&&|\|\||\?|:)\b")
_BRANCH_CPP = _BRANCH_JAVA

_FUNC_PY = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)
_CLASS_PY = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
_FUNC_JAVA = re.compile(r"(?:public|private|protected|static|final|synchronized|abstract|native|default)\s+[\w<>\[\],\s]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", re.MULTILINE)
_CLASS_JAVA = re.compile(r"\b(?:class|interface|enum|record)\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)
_FUNC_CPP = re.compile(r"^\s*[\w:<>,\s\*&]+\s+([A-Za-z_][A-Za-z0-9_]*)\s*\([^;]*\)\s*(?:const)?\s*\{", re.MULTILINE)
_CLASS_CPP = re.compile(r"\b(?:class|struct|union)\s+([A-Za-z_][A-Za-z0-9_]*)", re.MULTILINE)

_TODO_RE = re.compile(r"\b(TODO|HACK|XXX)\b", re.IGNORECASE)
_FIXME_RE = re.compile(r"\b(FIXME|BUG|OPTIMIZE)\b", re.IGNORECASE)


def _detect_language(ext: str) -> str:
    ext = (ext or "").lower().lstrip(".")
    if ext in ("py",):
        return "python"
    if ext in ("java",):
        return "java"
    if ext in ("cpp", "cc", "cxx", "c++", "h", "hpp", "hh", "hxx", "c"):
        return "cpp"
    return "unknown"


# =================================================================
# 2. 单个源码文件的静态分析
# =================================================================
def analyze_code_file(source: str, ext: str, filename: str = "") -> Dict[str, Any]:
    """
    返回：
    {
      "filename": str, "language": "python|java|cpp|unknown",
      "metrics": {
        lines_total, lines_code, lines_comment, lines_blank, comment_ratio,
        functions, classes, complexity_estimate, todo_count, fixme_count
      },
      "tokens": List[str]  # 用于 Jaccard 相似度
    }
    """
    language = _detect_language(ext)
    if not filename:
        filename = f"code.{ext}"

    if source is None:
        source = ""

    # 统一换行
    src_norm = source.replace("\r\n", "\n").replace("\r", "\n")
    lines = src_norm.split("\n")
    lines_total = len(lines)
    lines_blank = 0
    lines_comment = 0
    lines_code = 0

    # todo/fixme 用原文本搜（避免被去注释后丢掉）
    todo_count = len(_TODO_RE.findall(src_norm))
    fixme_count = len(_FIXME_RE.findall(src_norm))

    # ===== 修复 D1-2 FAIL 1：Python 三引号 docstring 也算注释行 =====
    # 先算出哪些行被三引号字符串覆盖（行号 0-based）
    docstring_lines: set[int] = set()
    if language == "python":
        # 用状态机扫一遍所有行，记录三引号区间
        i = 0
        in_str: Optional[str] = None  # "'''" 或 '"""'
        in_line_start = -1
        # 先合并所有行，用正则找 """...""" 区间，再映射回行号
        # 这里用简单实现：按行顺序扫描，遇到独立的 """ 或 ''' 切换状态
        while i < len(lines):
            raw = lines[i]
            stripped = raw.strip()
            if in_str is None:
                # 看这行是不是以三引号开头（含前导空格）
                m = re.match(r'^\s*("""|\'\'\')(.*)$', raw)
                if m:
                    q = m.group(1)
                    rest = m.group(2)
                    # 同是否也以相同 q 结尾（单行 docstring）
                    if rest.endswith(q) and len(rest) >= 3:
                        docstring_lines.add(i)
                        in_str = None
                    else:
                        in_str = q
                        in_line_start = i
                        docstring_lines.add(i)
            else:
                # 已经在三引号里面：只要这行包含 in_str 结尾，就关
                docstring_lines.add(i)
                # 找是否存在相同的三引号（未转义）
                if in_str in lines[i]:
                    # 简单处理：只看行里出现了相同三引号即关闭（实际情况嵌套很少）
                    in_str = None
                    in_line_start = -1
            i += 1

    for idx, line in enumerate(lines):
        s = line.strip()
        if not s:
            lines_blank += 1
            continue
        if language == "python":
            if idx in docstring_lines or s.startswith("#"):
                lines_comment += 1
                continue
        elif language in ("java", "cpp"):
            if s.startswith("//") or s.startswith("/*") or s.endswith("*/") or s.startswith("*"):
                lines_comment += 1
                continue
        # 混合行：code + trailing comment → 算 code
        lines_code += 1
    # 兜底：防止 0/0
    if lines_total == 0:
        comment_ratio = 0.0
    else:
        comment_ratio = round(lines_comment / lines_total, 3)

    # 函数/类/圈复杂度（按语言的关键字正则估算）
    if language == "python":
        clean_for_count = _PY_TRIPLE_DOUBLE.sub(" ", _PY_TRIPLE_SINGLE.sub(" ", src_norm))
        clean_for_count = _PY_LINE_COMMENT_RE.sub(" ", clean_for_count)
        funcs = len(_FUNC_PY.findall(clean_for_count))
        classes = len(_CLASS_PY.findall(clean_for_count))
        complexity = 1 + len(_BRANCH_PY.findall(clean_for_count))
    elif language == "java":
        clean_for_count = _BLOCK_C_STYLE_RE.sub(" ", src_norm)
        clean_for_count = _JAVA_CPP_LINE_COMMENT_RE.sub(" ", clean_for_count)
        funcs = len(_FUNC_JAVA.findall(clean_for_count))
        classes = len(_CLASS_JAVA.findall(clean_for_count))
        complexity = 1 + len(_BRANCH_JAVA.findall(clean_for_count))
    elif language == "cpp":
        clean_for_count = _BLOCK_C_STYLE_RE.sub(" ", src_norm)
        clean_for_count = _JAVA_CPP_LINE_COMMENT_RE.sub(" ", clean_for_count)
        funcs = len(_FUNC_CPP.findall(clean_for_count))
        classes = len(_CLASS_CPP.findall(clean_for_count))
        complexity = 1 + len(_BRANCH_CPP.findall(clean_for_count))
    else:
        # unknown：保守按类 C 风格估算
        clean_for_count = _BLOCK_C_STYLE_RE.sub(" ", src_norm)
        clean_for_count = _JAVA_CPP_LINE_COMMENT_RE.sub(" ", clean_for_count)
        funcs = 0
        classes = 0
        complexity = 1 + len(_BRANCH_JAVA.findall(clean_for_count))

    # token 化（用于 Jaccard 抄袭相似度）：
    #   先去掉注释/字符串字面量，再抓所有标识符 token；标识符再过滤掉语言关键字（避免 "if/for" 让相似度虚高），
    #   但保留标识符本身（函数名、变量名）。token 小写以降低大小写差异影响。
    if language == "python":
        no_comment = _PY_TRIPLE_DOUBLE.sub(" ", _PY_TRIPLE_SINGLE.sub(" ", src_norm))
        no_comment = _PY_LINE_COMMENT_RE.sub(" ", no_comment)
        no_comment = _STRING_LITERAL_DOUBLE.sub(" ", _STRING_LITERAL_SINGLE.sub(" ", no_comment))
        keywords = _PY_KEYWORDS
    elif language in ("java", "cpp"):
        no_comment = _BLOCK_C_STYLE_RE.sub(" ", src_norm)
        no_comment = _JAVA_CPP_LINE_COMMENT_RE.sub(" ", no_comment)
        no_comment = _STRING_LITERAL_DOUBLE.sub(" ", _STRING_LITERAL_SINGLE.sub(" ", no_comment))
        keywords = _JAVA_KEYWORDS if language == "java" else _CPP_KEYWORDS
    else:
        no_comment = _BLOCK_C_STYLE_RE.sub(" ", _JAVA_CPP_LINE_COMMENT_RE.sub(" ", src_norm))
        no_comment = _STRING_LITERAL_DOUBLE.sub(" ", _STRING_LITERAL_SINGLE.sub(" ", no_comment))
        keywords = set()
    tokens: List[str] = []
    for m in _IDENT_RE.findall(no_comment):
        t = m.lower()
        if t in keywords:
            continue
        if len(t) <= 1:  # 太短的无意义（a, b, i, j 这种也留着不删也行，但删了更好）
            continue
        tokens.append(t)

    # ===== 修复 D1-2 FAIL 4：改标识符改名仍能命中（结构 token：标识符→ID，数字→NUM，关键字/符号保留） =====
    struct_tokens = _struct_tokens(no_comment, keywords)

    metrics = {
        "lines_total": lines_total,
        "lines_code": lines_code,
        "lines_comment": lines_comment,
        "lines_blank": lines_blank,
        "comment_ratio": comment_ratio,
        "functions": funcs,
        "classes": classes,
        "complexity_estimate": max(1, complexity),
        "todo_count": todo_count,
        "fixme_count": fixme_count,
    }

    return {"filename": filename, "language": language, "metrics": metrics, "tokens": tokens, "struct_tokens": struct_tokens}


def _struct_tokens(no_comment: str, keywords: set) -> List[str]:
    """把去注释/去字符串后的源码，归一化为结构 token：
    - 标识符：保留关键字，其余统一替换为「ID」
    - 数字字面量：统一替换为「NUM」
    - 运算符、分隔符、括号等：原样保留
    返回结构 token 列表（顺序敏感，用于改标识符后的抄袭检测）
    """
    if not no_comment:
        return []
    # 1) 数字字面量（整数 + 浮点）→ NUM
    s = re.sub(r"\b\d+(?:\.\d+)?\b", " NUM ", no_comment)
    # 2) 标识符 → 关键字保留 / 其余统一为 ID
    def _ident(match):
        tok = match.group(0)
        if tok in keywords:
            return " " + tok + " "
        return " ID "
    s = re.sub(r"[A-Za-z_][A-Za-z0-9_]*", _ident, s)
    # 3) 抓结构 token（ID / NUM / 关键字 / 符号）
    tokens = re.findall(r"ID|NUM|[A-Za-z_]+|[{}();,\[\]\.+\-*/%=<>!&|?:]+", s)
    return tokens



# =================================================================
# 3. 多文件（zip 展开后）聚合分析
# =================================================================
def analyze_code_files(files: List[Tuple[str, str]]) -> Dict[str, Any]:
    """
    files = [(filename, source_str), ...]
    返回：{
      "files": [analyze_code_file(...) 结果],
      "summary_metrics": { ... 汇总 ... },
      "tokens_merged": List[str]  # 多文件合并 token（用于整包抄袭比对）
    }
    """
    results = []
    for filename, src in files:
        ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
        results.append(analyze_code_file(src or "", ext, filename=filename))

    if not results:
        return {"files": [], "summary_metrics": _empty_summary(), "tokens_merged": [], "struct_tokens_merged": []}

    lines_total = sum(r["metrics"]["lines_total"] for r in results)
    lines_code = sum(r["metrics"]["lines_code"] for r in results)
    lines_comment = sum(r["metrics"]["lines_comment"] for r in results)
    comment_ratio_avg = round(
        sum(r["metrics"]["comment_ratio"] for r in results) / len(results), 3
    ) if results else 0.0
    functions_total = sum(r["metrics"]["functions"] for r in results)
    classes_total = sum(r["metrics"]["classes"] for r in results)
    complexity_avg = round(
        sum(r["metrics"]["complexity_estimate"] for r in results) / len(results), 2
    ) if results else 1.0
    todo_total = sum(r["metrics"]["todo_count"] for r in results)
    fixme_total = sum(r["metrics"]["fixme_count"] for r in results)

    tokens_merged: List[str] = []
    struct_tokens_merged: List[str] = []
    for r in results:
        tokens_merged.extend(r.get("tokens", []))
        struct_tokens_merged.extend(r.get("struct_tokens", []))

    summary = {
        "lines_total": lines_total,
        "lines_code": lines_code,
        "lines_comment": lines_comment,
        "comment_ratio_avg": comment_ratio_avg,
        "functions_total": functions_total,
        "classes_total": classes_total,
        "complexity_estimate_avg": complexity_avg,
        "todo_total": todo_total,
        "fixme_total": fixme_total,
        "files_count": len(results),
    }
    return {"files": results, "summary_metrics": summary, "tokens_merged": tokens_merged, "struct_tokens_merged": struct_tokens_merged}


def _empty_summary() -> Dict[str, Any]:
    return {
        "lines_total": 0, "lines_code": 0, "lines_comment": 0,
        "comment_ratio_avg": 0.0, "functions_total": 0, "classes_total": 0,
        "complexity_estimate_avg": 1.0, "todo_total": 0, "fixme_total": 0,
        "files_count": 0,
    }


# =================================================================
# 4. 相似度 / 抄袭检测
# =================================================================
def jaccard_similarity(tokens_a: List[str], tokens_b: List[str]) -> float:
    sa = set(tokens_a or [])
    sb = set(tokens_b or [])
    if not sa and not sb:
        return 0.0
    inter = len(sa & sb)
    uni = len(sa | sb)
    if uni == 0:
        return 0.0
    return round(inter / uni, 4)


def plagiarism_similarity(
    archive_a: Dict[str, Any],
    archive_b: Dict[str, Any],
) -> float:
    """三信号融合的抄袭相似度（更鲁棒，不怕改标识符/改注释）：
    - 信号 1：标识符 Jaccard（tokens_merged）— 直接复制不改名字时命中
    - 信号 2：结构 Jaccard（struct_tokens_merged）— 改标识符/改变量名仍命中
    - 信号 3：长度信号（代码行数越接近，略微加分，避免 30 行 vs 300 行被误判）
    返回 0.0-1.0
    """
    ident = jaccard_similarity(archive_a.get("tokens_merged", []), archive_b.get("tokens_merged", []))
    struc = jaccard_similarity(archive_a.get("struct_tokens_merged", []), archive_b.get("struct_tokens_merged", []))
    # 长度信号（0.9-1.1 区间内长度相似 +0.03）
    sa = (archive_a.get("summary_metrics") or {}).get("lines_code", 0) or 0
    sb = (archive_b.get("summary_metrics") or {}).get("lines_code", 0) or 0
    length_bonus = 0.0
    if sa > 0 and sb > 0:
        ratio = sa / sb if sb >= sa else sb / sa
        if ratio >= 0.90:
            length_bonus = 0.03 * ratio
    # 取三信号最大值
    sim = max(float(ident), float(struc)) + length_bonus
    if sim > 1.0:
        sim = 1.0
    return round(sim, 4)


def detect_plagiarism(
    student_analyses: Dict[Any, Dict[str, Any]],
    threshold: float = 0.85,
) -> List[Dict[str, Any]]:
    """
    student_analyses: {student_id: analyze_code_files(...) 的返回}
    返回：按 similarity 倒序的雷同对（只返回相似度 >= threshold 的）
    """
    pairs: List[Dict[str, Any]] = []
    ids = list(student_analyses.keys())
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a = student_analyses[ids[i]]
            b = student_analyses[ids[j]]
            sim = plagiarism_similarity(a, b)
            if sim < threshold:
                continue
            if sim >= 0.95:
                sev = "high"
                note = "几乎完全一致，疑似直接复制"
            elif sim >= 0.90:
                sev = "high"
                note = "高度雷同，建议人工复核"
            elif sim >= 0.85:
                sev = "medium"
                note = "较高相似度，疑似参考未注明"
            else:
                sev = "low"
                note = "部分相似"
            pairs.append({
                "student_id_a": ids[i],
                "student_id_b": ids[j],
                "similarity": round(float(sim), 4),
                "severity": sev,
                "note": note,
            })
    pairs.sort(key=lambda x: x["similarity"], reverse=True)
    return pairs


# =================================================================
# 5. 和后端入库格式对齐（ai_evaluator.evaluate / check_completeness 的形状）
# =================================================================
def _clamp_score(v: float) -> float:
    return round(max(0.0, min(100.0, float(v))), 2)


def to_evaluation_dimensions(
    archive: Dict[str, Any],
    top_pair: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """对齐 ai_evaluator.evaluate 的返回：{scores:[{name,score,reason}], total, comment}"""
    s = archive.get("summary_metrics") or _empty_summary()
    files_count = s.get("files_count", 0)
    lines_code = s.get("lines_code", 0)

    # 维度 1：代码完整性（文件数 + 代码行数，越接近任务阈值越高）
    if files_count <= 0 or lines_code <= 0:
        completeness_score = 0.0
        completeness_reason = "未解析到有效代码文件"
    else:
        # 行数 100+ 算满分
        completeness_score = min(100.0, 40.0 + files_count * 15 + min(45, lines_code / 5))
        completeness_reason = f"提交 {files_count} 个文件、代码 {lines_code} 行"
    completeness_score = _clamp_score(completeness_score)

    # 维度 2：注释规范性（comment_ratio_avg，0.15-0.30 区间最优）
    cr = s.get("comment_ratio_avg", 0.0)
    if 0.15 <= cr <= 0.35:
        comment_score = 100.0
        comment_reason = f"注释率 {cr:.1%}，处于合理区间"
    elif cr < 0.05:
        comment_score = 40.0
        comment_reason = f"注释率仅 {cr:.1%}，建议补充说明"
    elif cr < 0.15:
        comment_score = 60.0 + (cr / 0.15) * 30
        comment_reason = f"注释率 {cr:.1%}，略偏低"
    else:
        # cr > 0.35：注释过多也算轻微扣分（避免为了凑分写大段无关注释）
        over = (cr - 0.35) / 0.35
        comment_score = max(60.0, 100.0 - over * 50)
        comment_reason = f"注释率 {cr:.1%}，略高，建议精简"
    comment_score = _clamp_score(comment_score)

    # 维度 3：可维护性（TODO/FIXME 数量 + 复杂度）
    todo_fixme = s.get("todo_total", 0) + s.get("fixme_total", 0) * 2  # FIXME 权重 2x
    complexity_avg = s.get("complexity_estimate_avg", 1.0)
    if todo_fixme == 0 and complexity_avg <= 10:
        maintain_score = 100.0
        maintain_reason = f"无 TODO/FIXME，平均圈复杂度 {complexity_avg:.1f}，代码简洁"
    else:
        base = 100.0
        base -= todo_fixme * 5
        base -= max(0, complexity_avg - 10) * 2
        maintain_score = base
        maintain_reason = f"TODO/FIXME={todo_fixme}，平均圈复杂度 {complexity_avg:.1f}"
    maintain_score = _clamp_score(maintain_score)

    # 维度 4：原创性 / 抄袭风险（用 top_pair）
    if top_pair is None:
        original_score = 95.0
        original_reason = "未检测到同任务高相似度提交"
    else:
        sim = top_pair.get("similarity", 0.0)
        sev = top_pair.get("severity", "low")
        note = top_pair.get("note", "")
        if sev == "high":
            original_score = 35.0
        elif sev == "medium":
            original_score = 60.0
        else:
            original_score = 80.0
        # 相似度越高分越低：线性递减
        penalty = int(round(sim * 60))
        original_score = max(20.0, original_score - penalty)
        original_reason = f"与学生 {top_pair.get('student_id_b')} 相似度 {sim*100:.1f}%：{note}"
    original_score = _clamp_score(original_score)

    scores = [
        {"name": "代码完整性", "score": completeness_score, "reason": completeness_reason},
        {"name": "注释规范性", "score": comment_score, "reason": comment_reason},
        {"name": "可维护性", "score": maintain_score, "reason": maintain_reason},
        {"name": "原创性", "score": original_score, "reason": original_reason},
    ]

    # 总分：等权均值（答辩现场"代码质量"维度权重）
    total = round(sum(s["score"] for s in scores) / len(scores), 2) if scores else 0.0

    # 总评 comment（1-2 句，前端 Result 页展示）
    lines = []
    if files_count == 0:
        lines.append("未解析到有效代码文件，请重新上传 .py/.java/.cpp/.zip")
    else:
        lines.append(f"代码 {files_count} 个文件共 {s.get('lines_total',0)} 行，函数 {s.get('functions_total',0)} 个、类 {s.get('classes_total',0)} 个。")
    if top_pair:
        lines.append(
            f"⚠️ 原创性：与学生 {top_pair.get('student_id_b')} 相似度 {top_pair.get('similarity',0)*100:.1f}%（{top_pair.get('severity')}），建议人工复核。"
        )
    if s.get("todo_total", 0) + s.get("fixme_total", 0) > 0:
        lines.append(
            f"遗留标记：TODO {s.get('todo_total',0)} 处、FIXME/BUG {s.get('fixme_total',0)} 处，建议答辩前清理。"
        )
    if not lines:
        lines.append("代码解析与静态分析完成。")
    comment = " ".join(lines)

    return {"scores": scores, "total": total, "comment": comment, "from_code_analyzer": True}


def to_logic_issues(
    archive: Dict[str, Any],
    top_pair: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, str]]:
    """对齐 check_completeness 返回的 issues 格式：List[{type, title, detail}]"""
    issues: List[Dict[str, str]] = []
    s = archive.get("summary_metrics") or _empty_summary()
    if s.get("files_count", 0) == 0:
        issues.append({"type": "empty", "title": "无有效代码", "detail": "上传内容中未解析到 .py/.java/.cpp/.zip 代码文件"})
        return issues

    # 抄袭预警
    if top_pair is not None:
        sim = top_pair.get("similarity", 0.0)
        issues.append({
            "type": "plagiarism",
            "title": f"抄袭风险（{top_pair.get('severity','high')}）",
            "detail": (
                f"与学生 {top_pair.get('student_id_b')} 提交相似度 {sim*100:.1f}%；"
                f"{top_pair.get('note','')}"
            ),
        })

    # TODO/FIXME 遗留
    td = s.get("todo_total", 0)
    fm = s.get("fixme_total", 0)
    if td + fm > 0:
        issues.append({
            "type": "incomplete",
            "title": f"{td + fm} 处遗留待处理",
            "detail": f"TODO/HACK {td} 处，FIXME/BUG {fm} 处。答辩前建议清理，避免评委追问。",
        })

    # 圈复杂度偏高的单文件（阈值 ≥10，适配学生实训代码规模）
    high_complex = [
        f for f in archive.get("files", [])
        if f.get("metrics", {}).get("complexity_estimate", 0) >= 10
    ]
    if high_complex:
        file_list = "、".join(f["filename"] for f in high_complex[:5])
        issues.append({
            "type": "complexity",
            "title": f"{len(high_complex)} 个文件圈复杂度偏高",
            "detail": f"{file_list} 圈复杂度估算均 ≥10，建议拆分函数、降低分支嵌套。",
        })

    # 注释率极低的文件（<5%）
    low_comment = [
        f for f in archive.get("files", [])
        if f.get("metrics", {}).get("lines_code", 0) >= 50 and f.get("metrics", {}).get("comment_ratio", 0.0) < 0.05
    ]
    if low_comment:
        file_list = "、".join(f["filename"] for f in low_comment[:5])
        issues.append({
            "type": "style",
            "title": f"{len(low_comment)} 个文件注释率不足 5%",
            "detail": f"{file_list} 代码行数较多但几乎无注释，建议补充关键函数说明和设计意图。",
        })

    return issues


# =================================================================
# 6. 便捷工具：把 bytes zip 内容展开成 [(filename, source_str)]
#   （后端 parser/router 会用到；这里放一起以便自测）
# =================================================================
def unpack_zip_bytes(zip_bytes: bytes) -> Tuple[List[Tuple[str, str]], List[str]]:
    """
    返回 (files, warnings)
    files = [(filename, source_str_decoded)]
    warnings = 解码失败等提示列表
    """
    files: List[Tuple[str, str]] = []
    warnings: List[str] = []
    if not zip_bytes:
        return files, warnings
    try:
        bio = io.BytesIO(zip_bytes)
        with zipfile.ZipFile(bio, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = info.filename.replace("\\", "/")
                # 跳过 __pycache__、.git、.idea、node_modules 等常见垃圾
                low = name.lower()
                if any(x in low for x in (
                    "__pycache__", ".git/", ".git\\", ".idea/", "node_modules/",
                    ".vscode/", ".mypy_cache/", ".pytest_cache/", "dist/", "build/",
                )):
                    continue
                # 只取源码扩展名
                ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
                if ext not in ("py", "java", "cpp", "cc", "cxx", "c++", "c", "h", "hpp", "hh", "hxx"):
                    continue
                raw = zf.read(info)
                text: Optional[str] = None
                for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030", "latin1"):
                    try:
                        text = raw.decode(enc)
                        break
                    except Exception:
                        continue
                if text is None:
                    warnings.append(f"{name}：无法识别编码，已跳过")
                    continue
                files.append((name, text))
    except zipfile.BadZipFile as e:
        warnings.append(f"不是合法 zip 文件：{e}")
    return files, warnings
