from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from typing import List
from app.services.file_parser import parse_file
from app.utils.ai_evaluator import evaluate, check_completeness
from app.models.database import SessionLocal
from app.models.tables import Task, Submission, Evaluation
import os, uuid
from datetime import datetime

router = APIRouter(prefix="/api/upload-eval", tags=["上传并评价"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/")
async def upload_and_evaluate(
    files: List[UploadFile] = File(...),
    task_requirements: str = Form("请完成实训任务"),
    criteria: str = Form("代码质量,功能完整性,文档规范性,界面设计"),
    student_id: int = Form(0),
    task_id: int = Form(0),
    db: Session = Depends(get_db)
):
    all_texts = []
    filenames = []
    save_path = ""

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_name = f"{timestamp}_{uuid.uuid4().hex[:8]}{ext}"
        save_path = os.path.join(UPLOAD_DIR, save_name)

        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)

        parse_result = await parse_file(save_path)

        if parse_result.get("success"):
            text = parse_result.get("text", "")
            if parse_result.get("type") == "image":
                all_texts.append(f"[图片文件: {file.filename}]")
            else:
                all_texts.append(text)
            filenames.append(file.filename)

    combined_text = "\n\n".join(all_texts)
    criteria_list = [c.strip() for c in criteria.split(",")]

    class_id = None
    if task_id > 0:
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            if task.criteria:
                criteria_list = [c.strip() for c in task.criteria.split(",")]
            if task.requirements:
                task_requirements = task.requirements
            class_id = task.class_id

    eval_result = evaluate(task_requirements, combined_text, criteria_list)
    completeness = check_completeness(task_requirements, combined_text)

    task_obj = None
    if task_id > 0:
        task_obj = db.query(Task).filter(Task.id == task_id).first()
    if not task_obj:
        task_obj = Task(
            title="实训任务",
            requirements=task_requirements,
            criteria=",".join(criteria_list),
            status="published"
        )
        db.add(task_obj)
        db.commit()
        db.refresh(task_obj)

    submission = Submission(
        task_id=task_obj.id,
        student_id=student_id if student_id > 0 else None,
        class_id=class_id,
        filename=", ".join(filenames),
        file_path=save_path,
        content=combined_text[:5000]
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)

    evaluation = Evaluation(
        submission_id=submission.id,
        evaluator_type="ai",
        total_score=eval_result["total"],
        dimension_scores=eval_result["scores"],
        comment=eval_result["comment"],
        step_completeness=completeness.get("steps", []),
        logic_issues=completeness.get("issues", [])
    )
    db.add(evaluation)
    db.commit()

    return {
        "success": True,
        "submission_id": submission.id,
        "filename": ", ".join(filenames),
        "content": combined_text[:500],
        "evaluation": eval_result,
        "completeness": completeness
    }