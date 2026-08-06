import os
import re
from datetime import datetime
from urllib.parse import quote
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import SessionLocal
from app.services.report_generator import (
    generate_excel, generate_word, generate_pdf,
    generate_class_report, generate_school_report,
)
from app.utils.auth_deps import (
    get_db, get_current_user, get_teacher_id, _extract_token,
)
from app.utils.auth import decode_token
from app.models.tables import LoginAccount

router = APIRouter(prefix="/api/report", tags=["报表导出"])
REPORT_DIR = "reports"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 移除原有的 get_db 函数，改用 auth_deps.get_db

_UNSAFE = re.compile(r'[\\/:*?"<>|\s]+')


def _safe(fn: str) -> str:
    return _UNSAFE.sub('_', (fn or '').strip('_')) or 'report'


def _disposition(filename: str) -> dict:
    """RFC 5987 标准 Content-Disposition 头。
    重要：Starlette/uvicorn 的 HTTP header 必须 latin-1 编码，
    所以 filename= 字段只能放 ASCII 安全名；中文原文件名仅放在 filename*=UTF-8''<urlencode>。
    """
    safe_ascii = _safe(filename)  # 中文会被 _UNSAFE 全清
    if not safe_ascii or not all(ord(c) < 128 for c in safe_ascii):
        # 学生名是中文会变 '_'，这里兜底用固定前缀
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = os.path.splitext(filename)[1] or '.bin'
        safe_ascii = f"Zhixunyun_Report_{ts}{ext}"
    return {
        "Content-Disposition":
            f"attachment; filename={safe_ascii}; filename*=UTF-8''{quote(filename)}"
    }


class ReportRequest(BaseModel):
    task_requirements: str
    evaluation: dict
    student_name: str = "学生"


@router.post("/excel")
def export_excel(
    req: ReportRequest,
    user: LoginAccount = Depends(get_current_user),
):
    safe_stu = _safe(req.student_name or "学生")
    filename = (f"实训评价报告_{safe_stu}_"
              f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    filepath = generate_excel(filename, req.task_requirements, req.evaluation,
                       student_name=req.student_name or "学生")
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=_disposition(filename),
    )


@router.post("/word")
def export_word(
    req: ReportRequest,
    user: LoginAccount = Depends(get_current_user),
):
    safe_stu = _safe(req.student_name or "学生")
    filename = (f"实训评价报告_{safe_stu}_"
              f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx")
    filepath = generate_word(filename, req.task_requirements, req.evaluation, req.student_name)
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=_disposition(filename),
    )


@router.post("/pdf")
def export_pdf(
    req: ReportRequest,
    user: LoginAccount = Depends(get_current_user),
):
    safe_stu = _safe(req.student_name or "学生")
    filename = (f"实训评价报告_{safe_stu}_"
              f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    filepath = generate_pdf(filename, req.task_requirements, req.evaluation, req.student_name)
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/pdf",
        headers=_disposition(filename),
    )


@router.post("/batch-excel")
def export_batch_excel(
    req: dict,
    db: Session = Depends(get_db),
    user: LoginAccount = Depends(get_current_user),
):
    """批量导出全班成绩"""
    from app.services.report_generator import generate_batch_excel
    filename = f"班级成绩汇总_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = generate_batch_excel(filename, req, db)
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=_disposition(filename),
    )


@router.get("/class-report/{class_id}")
def export_class_report(
    class_id: int,
    format: str = Query("pdf", pattern="^(pdf|excel|xlsx)$"),
    db: Session = Depends(get_db),
    user: LoginAccount = Depends(get_current_user),
):
    """F1 班级教学质量画像报表。教师只能导出自己班级的报告。"""
    # 权限：教师只能导出自己班级的
    teacher_id = get_teacher_id(user, db)
    if teacher_id:
        from app.models.class_models import Class as Cls
        cls = db.query(Cls).filter(Cls.id == class_id).first()
        if not cls:
            raise HTTPException(status_code=404, detail="班级不存在")
        if cls.teacher_id != teacher_id:
            raise HTTPException(status_code=403, detail="只能导出自己班级的报告")
    try:
        ext = "xlsx" if format in ("excel", "xlsx") else "pdf"
        media = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                 if ext == "xlsx" else "application/pdf")
        fmt = "excel" if ext == "xlsx" else "pdf"
        filename = f"班级报表_{class_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        filepath = generate_class_report(filename, class_id, db, fmt=fmt)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="report file not generated")
        return FileResponse(filepath, filename=filename, media_type=media,
                            headers=_disposition(filename))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/school-overview")
def export_school_overview(
    format: str = Query("pdf", pattern="^(pdf|excel|xlsx)$"),
    db: Session = Depends(get_db),
    user: LoginAccount = Depends(get_current_user),
):
    """F1 校级教学质量总览报表。仅教师可查看。"""
    # 仅教师可查看校级报表
    teacher_id = get_teacher_id(user, db)
    if not teacher_id:
        raise HTTPException(status_code=403, detail="仅教师可查看校级报表")
    try:
        ext = "xlsx" if format in ("excel", "xlsx") else "pdf"
        media = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                 if ext == "xlsx" else "application/pdf")
        fmt = "excel" if ext == "xlsx" else "pdf"
        filename = f"校级总览_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        filepath = generate_school_report(filename, db, fmt=fmt)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="report file not generated")
        return FileResponse(filepath, filename=filename, media_type=media,
                            headers=_disposition(filename))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))