from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.models.database import SessionLocal
from app.models.tables import Evaluation, Submission, LoginAccount, Teacher, Student
from app.models.class_models import Class, ClassMember
from app.utils.auth_deps import get_db, get_current_user, get_teacher_id

router = APIRouter(prefix="/api/teacher", tags=["教师评分"])


class DimensionScore(BaseModel):
    name: str
    score: float
    reason: str


class TeacherScoreRequest(BaseModel):
    submission_id: int
    scores: List[DimensionScore]
    total_score: float
    comment: str


# 教师提交主观评分 — 需要登录且为教师，只能评价自己班级学生的提交
@router.post("/score")
def submit_teacher_score(
    req: TeacherScoreRequest,
    db: Session = Depends(get_db),
    user: LoginAccount = Depends(get_current_user),
):
    # 鉴权：仅教师
    teacher_pk = get_teacher_id(user, db)
    if not teacher_pk:
        raise HTTPException(403, "仅教师可提交评分")

    # 权限检查：该 submission 的学生必须在教师班级里
    submission = db.query(Submission).filter(Submission.id == req.submission_id).first()
    if not submission:
        raise HTTPException(404, "提交不存在")
    student_in_classes = (
        db.query(ClassMember)
        .join(Class, Class.id == ClassMember.class_id)
        .filter(
            ClassMember.student_id == submission.student_id,
            Class.teacher_id == teacher_pk,
        )
        .first()
    )
    if not student_in_classes:
        raise HTTPException(403, "只能评价自己班级学生的提交")
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


# 获取某个提交的所有评分（AI + 教师）— 需要登录
@router.get("/scores/{submission_id}")
def get_scores(
    submission_id: int,
    db: Session = Depends(get_db),
    user: LoginAccount = Depends(get_current_user),
):
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