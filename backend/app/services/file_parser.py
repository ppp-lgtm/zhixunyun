import os
import base64
from typing import Optional

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

ALLOWED_TYPES = {'.docx', '.pdf', '.png', '.jpg', '.jpeg'}


async def parse_file(file_path: str) -> dict:
    """根据后缀自动解析文件，返回提取的文字"""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.docx':
        return parse_docx(file_path)
    elif ext == '.pdf':
        return parse_pdf(file_path)
    elif ext in {'.png', '.jpg', '.jpeg'}:
        return parse_image(file_path)
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
        "image_data": data_url
    }