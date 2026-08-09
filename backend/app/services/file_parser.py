import os
import re
import io
import zipfile
import base64
from typing import List, Optional, Tuple

try:
    import docx  # python-docx
    _HAS_DOCX = True
except Exception:  # pragma: no cover - optional runtime dep
    docx = None  # type: ignore
    _HAS_DOCX = False

try:
    import fitz  # PyMuPDF
    _HAS_PDF = True
except Exception:  # pragma: no cover
    fitz = None  # type: ignore
    _HAS_PDF = False

ALLOWED_TYPES = {
    '.docx', '.pdf', '.png', '.jpg', '.jpeg',
    # ===== D1 新增：单源码文件 + 代码 zip 包
    '.py', '.java', '.cpp', '.cc', '.cxx', '.c++', '.c',
    '.h', '.hpp', '.hh', '.hxx', '.zip',
}

_CODE_EXTS = {'.py', '.java', '.cpp', '.cc', '.cxx', '.c++', '.c', '.h', '.hpp', '.hh', '.hxx'}
_SKIP_DIR_PATTERNS = (
    '__pycache__', '.git/', '.git\\', '.idea/', 'node_modules/',
    '.vscode/', '.mypy_cache/', '.pytest_cache/', 'dist/', 'build/',
)


def _decode_bytes(raw: bytes) -> Tuple[Optional[str], List[str]]:
    """按顺序尝试 utf-8 / utf-8-sig / gbk / gb18030 / latin1，返回 (text, warnings)"""
    warnings: List[str] = []
    for enc in ("utf-8", "utf-8-sig", "gbk", "gb18030", "latin1"):
        try:
            return raw.decode(enc), warnings
        except Exception:
            continue
    warnings.append("无法识别文件编码，已跳过")
    return None, warnings


def _filter_zip_name(name: str) -> bool:
    """过滤 zip 内部垃圾目录/文件"""
    if not name:
        return False
    low = name.lower().replace("\\", "/")
    if any(p in low for p in _SKIP_DIR_PATTERNS):
        return False
    return True


async def parse_file(file_path: str) -> dict:
    """根据后缀自动解析文件，返回提取的文字"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.docx':
        return parse_docx(file_path)
    elif ext == '.pdf':
        return parse_pdf(file_path)
    elif ext in {'.png', '.jpg', '.jpeg'}:
        return parse_image(file_path)
    # ===== D1 新增：单源码文件解析 =====
    elif ext in _CODE_EXTS:
        return parse_source_file(file_path)
    # ===== D1 新增：多文件 zip 包解析 =====
    elif ext == '.zip':
        return parse_zip(file_path)
    else:
        return {"success": False, "error": f"不支持 {ext} 格式"}


def parse_docx(file_path: str) -> dict:
    if not _HAS_DOCX:
        return {"success": False, "error": "缺少 python-docx 依赖，请先安装 requirements.txt"}
    doc = docx.Document(file_path)
    text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    return {"success": True, "text": text, "type": "word"}


def parse_pdf(file_path: str) -> dict:
    if not _HAS_PDF:
        return {"success": False, "error": "缺少 PyMuPDF (fitz) 依赖，请先安装 requirements.txt"}
    pdf = fitz.open(file_path)
    text = ""
    for page in pdf:
        text += page.get_text()
    pdf.close()
    return {"success": True, "text": text, "type": "pdf"}


def parse_image(file_path: str) -> dict:
    with open(file_path, "rb") as f:
        img_data = base64.b64encode(f.read()).decode()

    ext = os.path.splitext(file_path)[1].lower()
    mime = "image/png" if ext == ".png" else "image/jpeg"
    data_url = f"data:{mime};base64,{img_data}"

    return {
        "success": True,
        "text": "[图片内容将通过AI视觉模型识别]",
        "type": "image",
        "image_data": data_url,
        # D2：单独上传图片时也在 images[] 里返回一份，方便和 zip 内图片统一结构
        "images": [{
            "filename": os.path.basename(file_path),
            "name": os.path.basename(file_path),
            "path": file_path,
            "file_path": file_path,
            "ext": ext,
            "content_type": mime,
            "image_data": data_url,
        }],
    }


# =================================================================
# D1 新增：单源码文件 / 多文件 zip 包解析
# 返回结构与原 success/text/type 兼容（额外加 files[] / warnings[]）
# =================================================================

def _build_code_summary(files: List[dict]) -> str:
    """把多个源码文件拼接成一段「兼容原 text 字段」的摘要，避免破坏老链路。"""
    chunks = []
    for f in files:
        filename = f.get("filename", "")
        content = f.get("content", "") or ""
        preview_len = min(len(content), 2000)
        chunks.append(
            f"===== 源码文件: {filename} =====\n"
            f"{content[:preview_len]}{'...[已截断，完整内容见 files[]]' if preview_len < len(content) else ''}"
        )
    return "\n\n".join(chunks)


def parse_source_file(file_path: str) -> dict:
    """单源码文件解析（.py/.java/.cpp 等）"""
    filename = os.path.basename(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in _CODE_EXTS:
        return {"success": False, "error": f"parse_source_file 不支持 {ext}"}
    try:
        with open(file_path, "rb") as f:
            raw = f.read()
    except Exception as e:
        return {"success": False, "error": f"读文件失败: {e}"}

    text, warns = _decode_bytes(raw)
    if text is None:
        return {"success": False, "error": warns[-1] if warns else "编码识别失败"}

    stripped = text.strip()
    if len(stripped) < 10:
        warns.append(f"{filename}: 代码内容过短(<10字符)，已跳过，避免学生提交 DB 漏入库")
        return {
            "success": False,
            "error": f"{filename}: 代码内容过短(<10字符)",
            "warnings": warns,
        }

    file_item = {
        "filename": filename,
        "path": file_path,
        "ext": ext,
        "content": text,
    }
    return {
        "success": True,
        "text": _build_code_summary([file_item]),
        "type": "code",
        "files": [file_item],
        "warnings": warns,
    }


def parse_zip(file_path: str) -> dict:
    """多文件 zip 包解析：源码文件 → files[]，图片文件（步骤截图）→ images[]。"""
    files_out: List[dict] = []
    images_out: List[dict] = []
    warns: List[str] = []
    _IMG_EXTS = {".png", ".jpg", ".jpeg"}
    try:
        with open(file_path, "rb") as f:
            zip_bytes = f.read()
        bio = io.BytesIO(zip_bytes)
        # D2：为了给步骤进度 extract_step_progress 用，需要把图片解到磁盘（PaddleOCR 只认路径）
        import tempfile as _tf
        tmp_root = _tf.mkdtemp(prefix="zhixunyun_zip_images_")
        with zipfile.ZipFile(bio, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = info.filename.replace("\\", "/")
                if not _filter_zip_name(name):
                    continue
                ext = os.path.splitext(name)[1].lower()
                if ext in _IMG_EXTS:
                    # 解压到临时目录
                    safe_name = os.path.basename(name) or f"img_{len(images_out)+1}{ext}"
                    local_path = os.path.join(tmp_root, f"{len(images_out):04d}_{safe_name}")
                    try:
                        raw_img = zf.read(info)
                        os.makedirs(os.path.dirname(local_path), exist_ok=True)
                        with open(local_path, "wb") as wf:
                            wf.write(raw_img)
                        mime = "image/png" if ext == ".png" else "image/jpeg"
                        try:
                            img_b64 = base64.b64encode(raw_img).decode()
                            data_url = f"data:{mime};base64,{img_b64}"
                        except Exception:
                            data_url = ""
                        images_out.append({
                            "filename": name,
                            "name": name,
                            "path": local_path,
                            "file_path": local_path,
                            "ext": ext,
                            "content_type": mime,
                            "image_data": data_url,
                        })
                    except Exception as e:
                        warns.append(f"{name}: 图片解压失败 {e}")
                    continue
                if ext not in _CODE_EXTS:
                    continue
                try:
                    raw = zf.read(info)
                except Exception as e:
                    warns.append(f"{name}: 读取失败 {e}")
                    continue
                text, dec_warns = _decode_bytes(raw)
                warns.extend(f"{name}: {w}" for w in dec_warns)
                if text is None:
                    continue
                stripped = text.strip()
                if len(stripped) < 10:
                    # 字节数太少，很可能是被截断的残缺代码：记 warning 但不加入 files_out，避免后续学生提交漏入库
                    warns.append(f"{name}: 代码内容过短(<10字符)，已跳过")
                    continue
                files_out.append({
                    "filename": name,
                    "path": name,
                    "ext": ext,
                    "content": text,
                })
    except zipfile.BadZipFile as e:
        return {"success": False, "error": f"不是合法 zip 文件: {e}"}
    except Exception as e:
        return {"success": False, "error": f"zip 解析失败: {e}"}

    if not files_out:
        return {
            "success": False,
            "error": "zip 中未发现 .py/.java/.cpp 等源码文件",
            "warnings": warns,
        }
    result = {
        "success": True,
        "text": _build_code_summary(files_out),
        "type": "zip",
        "files": files_out,
        "warnings": warns,
    }
    if images_out:
        result["images"] = images_out
    return result
