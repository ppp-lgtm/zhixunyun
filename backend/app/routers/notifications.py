from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import SessionLocal
from app.models.tables import Task, Submission, Evaluation
from app.models.class_models import Class, ClassMember

router = APIRouter(prefix="/api/notifications", tags=["消息通知"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class MarkReadRequest(BaseModel):
    notification_type: str  # 'submission' 或 'evaluation'


@router.get("/student/{student_id}")
def student_notifications(student_id: int, db: Session = Depends(get_db)):
    """学生消息：教师评分 + 新任务发布"""
    members = db.query(ClassMember).filter(ClassMember.student_id == student_id).all()
    class_ids = [m.class_id for m in members]

    notifications = []
    total_unread = 0

    if class_ids:
        # 教师评分通知
        teacher_evals = db.query(Evaluation.submission_id, Submission.filename, Evaluation.total_score).join(
            Submission, Evaluation.submission_id == Submission.id
        ).filter(
            Submission.student_id == student_id,
            Evaluation.evaluator_type == "teacher"
        ).all()

        evaluated_ids = [e.submission_id for e in teacher_evals]

        all_submissions = db.query(Submission.id).filter(Submission.student_id == student_id).all()
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

        # 新任务通知（该班级最近3天发布的任务）
        from datetime import datetime, timedelta
        three_days_ago = datetime.now() - timedelta(days=3)

        new_tasks = db.query(Task).filter(
            Task.class_id.in_(class_ids),
            Task.created_at >= three_days_ago
        ).all()

        for t in new_tasks:
            submitted = db.query(Submission).filter(
                Submission.task_id == t.id,
                Submission.student_id == student_id
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
def teacher_notifications(teacher_id: int, db: Session = Depends(get_db)):
    """教师消息：学生提交了作业"""
    # 查教师创建的班级
    my_classes = db.query(Class).filter(Class.teacher_id == teacher_id).all()
    class_ids = [c.id for c in my_classes]

    notifications = []
    total_unread = 0

    if class_ids:
        # 查教师发布的任务
        my_tasks = db.query(Task).filter(Task.created_by == teacher_id).all()
        task_ids = [t.id for t in my_tasks]

        if task_ids:
            # 查最近24小时提交
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(hours=24)

            recent_subs = db.query(Submission, Task.title, Evaluation.id).join(
                Task, Submission.task_id == Task.id
            ).outerjoin(
                Evaluation, Evaluation.submission_id == Submission.id
            ).filter(
                Submission.task_id.in_(task_ids),
                Submission.created_at >= yesterday
            ).all()

            # 去重计数
            unrated_subs = [s for s in recent_subs if not s[2]]  # s[2] 是 Evaluation.id

            new_count = len([s for s in recent_subs if s[0].created_at >= yesterday])

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