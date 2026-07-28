from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.models.database import SessionLocal
from app.models.tables import Evaluation, Submission

router = APIRouter(prefix="/api/teacher", tags=["教师评分"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class DimensionScore(BaseModel):
    name: str
    score: float
    reason: str


class TeacherScoreRequest(BaseModel):
    submission_id: int
    scores: List[DimensionScore]
    total_score: float
    comment: str


# 教师提交主观评分
@router.post("/score")
def submit_teacher_score(req: TeacherScoreRequest, db: Session = Depends(get_db)):
    # 查找是否已有教师评分
    existing = db.query(Evaluation).filter(
        Evaluation.submission_id == req.submission_id,
        Evaluation.evaluator_type == "teacher"
    ).first()

    if existing:
        # 更新已有评分
        existing.total_score = req.total_score
        existing.dimension_scores = [s.dict() for s in req.scores]
        existing.comment = req.comment
    else:
        # 新建教师评分
        evaluation = Evaluation(
            submission_id=req.submission_id,
            evaluator_type="teacher",
            total_score=req.total_score,
            dimension_scores=[s.dict() for s in req.scores],
            comment=req.comment
        )
        db.add(evaluation)

    db.commit()
    return {"success": True, "message": "教师评分已保存"}


# 获取某个提交的所有评分（AI + 教师）
@router.get("/scores/{submission_id}")
def get_scores(submission_id: int, db: Session = Depends(get_db)):
    evaluations = db.query(Evaluation).filter(
        Evaluation.submission_id == submission_id
    ).all()

    ai_score = None
    teacher_score = None

    for e in evaluations:
        data = {
            "id": e.id,
            "total_score": e.total_score,
            "dimension_scores": e.dimension_scores,
            "comment": e.comment,
            "created_at": e.created_at.strftime("%Y-%m-%d %H:%M") if e.created_at else ""
        }
        if e.evaluator_type == "ai":
            ai_score = data
        else:
            teacher_score = data

    return {
        "success": True,
        "data": {
            "ai_score": ai_score,
            "teacher_score": teacher_score,
            "submission_id": submission_id
        }
    }