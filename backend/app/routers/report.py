import os
from datetime import datetime
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import SessionLocal
from app.services.report_generator import (
    generate_excel, generate_word, generate_pdf,
    generate_class_report, generate_school_report,
)

router = APIRouter(prefix="/api/report", tags=["报表导出"])
REPORT_DIR = "reports"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class ReportRequest(BaseModel):
    task_requirements: str
    evaluation: dict
    student_name: str = "学生"


@router.post("/excel")
def export_excel(req: ReportRequest):
    filename = f"评价报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = generate_excel(filename, req.task_requirements, req.evaluation)
    return FileResponse(filepath, filename=filename,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.post("/word")
def export_word(req: ReportRequest):
    filename = f"评价报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
    filepath = generate_word(filename, req.task_requirements, req.evaluation, req.student_name)
    return FileResponse(
        filepath,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )


@router.post("/pdf")
def export_pdf(req: ReportRequest):
    filename = f"评价报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    filepath = generate_pdf(filename, req.task_requirements, req.evaluation, req.student_name)
    return FileResponse(filepath, filename=filename, media_type="application/pdf")


@router.post("/batch-excel")
def export_batch_excel(req: dict, db: Session = Depends(get_db)):
    """批量导出全班成绩"""
    from app.services.report_generator import generate_batch_excel
    filename = f"班级成绩汇总_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = generate_batch_excel(filename, req, db)
    return FileResponse(filepath, filename=filename,
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@router.get("/class-report/{class_id}")
def export_class_report(
    class_id: int,
    format: str = Query("pdf", pattern="^(pdf|excel|xlsx)$"),
    db: Session = Depends(get_db),
):
    """F1 班级教学质量画像报表。格式 ?format=pdf|excel。"""
    try:
        ext = "xlsx" if format in ("excel", "xlsx") else "pdf"
        media = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                 if ext == "xlsx" else "application/pdf")
        fmt = "excel" if ext == "xlsx" else "pdf"
        filename = f"班级报表_{class_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        filepath = generate_class_report(filename, class_id, db, fmt=fmt)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="report file not generated")
        return FileResponse(filepath, filename=filename, media_type=media)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/school-overview")
def export_school_overview(
    format: str = Query("pdf", pattern="^(pdf|excel|xlsx)$"),
    db: Session = Depends(get_db),
):
    """F1 校级教学质量总览报表。格式 ?format=pdf|excel。"""
    try:
        ext = "xlsx" if format in ("excel", "xlsx") else "pdf"
        media = ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                 if ext == "xlsx" else "application/pdf")
        fmt = "excel" if ext == "xlsx" else "pdf"
        filename = f"校级总览_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        filepath = generate_school_report(filename, db, fmt=fmt)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="report file not generated")
        return FileResponse(filepath, filename=filename, media_type=media)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))