from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.models.database import SessionLocal
from app.models.tables import Task, Submission, Evaluation, Teacher, Student, LoginAccount
from app.models.class_models import Class, ClassMember
from app.utils.auth_deps import get_db, get_current_user, get_student_pk, get_teacher_id

router = APIRouter(prefix="/api/notifications", tags=["消息通知"])


# ============================================================
# ID 转换辅助函数
# ============================================================

def _account_to_student_pk(db: Session, account_id: int) -> Optional[int]:
    if not account_id or account_id <= 0:
        return None
    row = db.query(Student).filter(Student.account_id == int(account_id)).first()
    return row.id if row else None


def _account_to_teacher_pk(db: Session, account_id: int) -> Optional[int]:
    if not account_id or account_id <= 0:
        return None
    row = db.query(Teacher).filter(Teacher.account_id == int(account_id)).first()
    return row.id if row else None


class MarkReadRequest(BaseModel):
    notification_type: str


@router.get("/student/{student_id}")
def student_notifications(
    student_id: int,
    read_since: Optional[int] = 0,
    db: Session = Depends(get_db),
    user: LoginAccount = Depends(get_current_user),
):
    # 学生只能查看自己的通知
    if user.role == "student" and int(user.id) != int(student_id):
        raise HTTPException(status_code=403, detail="只能查看自己的通知")
    from datetime import datetime, timedelta
    student_pk = _account_to_student_pk(db, student_id)
    if not student_pk:
        return {
            "success": True,
            "data": {
                "notifications": [],
                "total_unread": 0
            }
        }

    members = db.query(ClassMember).filter(ClassMember.student_id == student_pk).all()
    class_ids = [m.class_id for m in members]

    notifications = []
    total_unread = 0

    read_threshold = datetime.fromtimestamp(read_since / 1000) if read_since and read_since > 0 else datetime.fromtimestamp(0)

    if class_ids:
        teacher_evals = db.query(Evaluation.submission_id, Submission.filename, Evaluation.total_score, Evaluation.created_at).join(
            Submission, Evaluation.submission_id == Submission.id
        ).filter(
            Submission.student_id == student_pk,
            Evaluation.evaluator_type == "teacher",
            Evaluation.created_at > read_threshold
        ).all()

        evaluated_ids = [e.submission_id for e in teacher_evals]

        all_submissions = db.query(Submission.id).filter(Submission.student_id == student_pk).all()
        all_ids = [s.id for s in all_submissions]
        evaluated_count = len(set(evaluated_ids) & set(all_ids))

        if evaluated_count > 0:
            notifications.append({
                "type": "evaluation",
                "title": "教师评分通知",
                "message": f"你有 {evaluated_count} 份作业已被教师评分",
                "count": evaluated_count,
                "icon": "📝"
            })
            total_unread += evaluated_count

        three_days_ago = datetime.now() - timedelta(days=3)

        new_tasks = db.query(Task).filter(
            Task.class_id.in_(class_ids),
            Task.created_at >= three_days_ago,
            Task.created_at > read_threshold
        ).all()

        for t in new_tasks:
            submitted = db.query(Submission).filter(
                Submission.task_id == t.id,
                Submission.student_id == student_pk
            ).first()
            if not submitted:
                notifications.append({
                    "type": "new_task",
                    "title": "新实训任务",
                    "message": f"教师发布了新任务：{t.title}",
                    "count": 1,
                    "icon": "📋",
                    "task_id": t.id
                })
                total_unread += 1

    return {
        "success": True,
        "data": {
            "notifications": notifications,
            "total_unread": total_unread
        }
    }


@router.get("/teacher/{teacher_id}")
def teacher_notifications(
    teacher_id: int,
    read_since: Optional[int] = 0,
    db: Session = Depends(get_db),
    user: LoginAccount = Depends(get_current_user),
):
    # 教师只能查看自己的通知
    if user.role == "teacher" and int(user.id) != int(teacher_id):
        raise HTTPException(status_code=403, detail="只能查看自己的通知")
    from datetime import datetime, timedelta
    teacher_pk = _account_to_teacher_pk(db, teacher_id)
    if not teacher_pk:
        return {
            "success": True,
            "data": {
                "notifications": [],
                "total_unread": 0
            }
        }

    my_classes = db.query(Class).filter(Class.teacher_id == teacher_pk).all()
    class_ids = [c.id for c in my_classes]

    notifications = []
    total_unread = 0

    read_threshold = datetime.fromtimestamp(read_since / 1000) if read_since and read_since > 0 else datetime.fromtimestamp(0)

    if class_ids:
        my_tasks = db.query(Task).filter(Task.created_by == teacher_pk).all()
        task_ids = [t.id for t in my_tasks]

        if task_ids:
            yesterday = datetime.now() - timedelta(hours=24)

            recent_subs = db.query(Submission, Task.title, Evaluation.id).join(
                Task, Submission.task_id == Task.id
            ).outerjoin(
                Evaluation, Evaluation.submission_id == Submission.id
            ).filter(
                Submission.task_id.in_(task_ids),
                Submission.created_at >= yesterday
            ).all()

            # 新提交：仅统计 read_threshold 之后创建的
            new_subs = [s for s in recent_subs if s[0].created_at > read_threshold]
            new_count = len(new_subs)

            # 待评分：未评分且创建时间在 read_threshold 之后的
            unrated_subs = [s for s in new_subs if not s[2]]
            unrated_count = len(unrated_subs)

            if new_count > 0:
                notifications.append({
                    "type": "submission",
                    "title": "学生提交提醒",
                    "message": f"最近24小时内有 {new_count} 份新提交",
                    "count": new_count,
                    "icon": "📤"
                })
                total_unread += new_count

            if unrated_count > 0:
                notifications.append({
                    "type": "unrated",
                    "title": "待评分提醒",
                    "message": f"还有 {unrated_count} 份提交未评分",
                    "count": unrated_count,
                    "icon": "⚠️"
                })
                total_unread += unrated_count

    return {
        "success": True,
        "data": {
            "notifications": notifications,
            "total_unread": total_unread
        }
    }
