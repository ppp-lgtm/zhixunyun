import os
import uuid
from datetime import datetime
from fastapi import APIRouter, UploadFile, File
from app.services.file_parser import parse_file, ALLOWED_TYPES

router = APIRouter(prefix="/api/upload", tags=["文件上传"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/file")
async def upload_file(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()

    if ext not in ALLOWED_TYPES:
        return {"success": False, "error": f"不支持 {ext}，允许：{', '.join(ALLOWED_TYPES)}"}

    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_name = f"{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
    save_path = os.path.join(UPLOAD_DIR, save_name)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    # 解析文件
    result = await parse_file(save_path)

    return {
        "success": result.get("success", False),
        "filename": file.filename,
        "saved_as": save_name,
        "text": result.get("text", ""),
        "text_length": len(result.get("text", ""))
    }