import os
from datetime import datetime
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import SessionLocal
from app.services.report_generator import generate_excel, generate_word, generate_pdf

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