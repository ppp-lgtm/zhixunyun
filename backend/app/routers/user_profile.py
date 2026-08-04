import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from app.models.database import SessionLocal
from app.models.tables import (
    LoginAccount, Teacher, Student, Submission, Evaluation, TaskClassRef,
)
from app.models.class_models import Class, ClassMember
from app.utils.auth import hash_password, verify_password

router = APIRouter(prefix="/api/user", tags=["个人中心"])

UPLOAD_DIR = "uploads/avatars"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------------------
# 工具：从 login_accounts.id 拿到角色信息
# 返回 (role_ext, real_name, user_number, role_obj)
# role_ext: 外部统一用 enterprise / teacher / student
# --------------------------------------------------------------
def _load_user_context(db: Session, account_id: int):
    acct = db.query(LoginAccount).filter(LoginAccount.id == account_id).first()
    if not acct:
        return None
    r = acct.role
    ext = "enterprise" if r == "mentor" else (r or "student")
    real_name = ""
    user_number = ""
    role_obj = None
    if r == "teacher":
        t = db.query(Teacher).filter(Teacher.account_id == acct.id).first()
        if t:
            real_name = t.real_name or ""
            user_number = t.teacher_no or ""
            role_obj = t
    elif r == "student":
        s = db.query(Student).filter(Student.account_id == acct.id).first()
        if s:
            real_name = s.real_name or ""
            user_number = s.student_no or ""
            role_obj = s
    else:  # mentor
        try:
            from app.models.enterprise_models import EnterpriseMentor
            em = db.query(EnterpriseMentor).filter(EnterpriseMentor.account_id == acct.id).first()
            if em:
                real_name = em.real_name or ""
                role_obj = em
        except Exception:
            pass
    return {
        "account": acct,
        "role_ext": ext,
        "real_name": real_name,
        "user_number": user_number,
        "role_obj": role_obj,
    }


# --------------------------------------------------------------
# 工具：给定 login_accounts.id + ext_role=student 时，查 students.id
# （因为 submissions.student_id、class_members.student_id 都指向 students.id）
# --------------------------------------------------------------
def _account_id_to_student_id(db: Session, account_id: int):
    s = db.query(Student).filter(Student.account_id == int(account_id)).first()
    return s.id if s else None


def _account_id_to_teacher_id(db: Session, account_id: int):
    t = db.query(Teacher).filter(Teacher.account_id == int(account_id)).first()
    return t.id if t else None


class ProfileUpdate(BaseModel):
    real_name: Optional[str] = None
    email: Optional[str] = None
    user_number: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.get("/profile/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    ctx = _load_user_context(db, user_id)
    if not ctx:
        raise HTTPException(404, "用户不存在")
    acct = ctx["account"]

    base_data = {
        "id": acct.id,
        "username": acct.username,
        "real_name": ctx["real_name"],
        "email": acct.email or "",
        "role": ctx["role_ext"],
        "avatar": getattr(acct, 'avatar', '') or '',
        "user_number": ctx["user_number"],
        "phone": getattr(acct, "phone", "") or "",
        "created_at": str(acct.created_at) if acct.created_at else "",
    }

    extra = {}
    if ctx["role_ext"] == "enterprise":
        try:
            from app.models.enterprise_models import (
                Enterprise, EnterpriseMentor, JobPosition, EnterpriseEvaluation, JobClassRef,
            )
        except Exception:
            pass
        else:
            em = ctx["role_obj"]  # EnterpriseMentor (如果有)
            mentor_list = (
                db.query(EnterpriseMentor)
                .filter(EnterpriseMentor.account_id == acct.id)
                .filter(EnterpriseMentor.status == "active")
                .all()
            )
            mentor = mentor_list[0] if mentor_list else None
            enterprise = None
            stats = {
                "job_count": 0,
                "eval_count": 0,
                "pending_eval_count": 0,
                "class_count": 0,
                "student_count": 0,
                "avg_score": 0,
            }
            if mentor:
                e = db.query(Enterprise).filter(Enterprise.id == mentor.enterprise_id).first()
                if e:
                    enterprise = {
                        "id": e.id, "name": e.name, "short_name": e.short_name,
                        "logo": e.logo, "industry": e.industry, "scale": e.scale,
                        "contact_person": e.contact_person, "contact_phone": e.contact_phone,
                        "contact_email": e.contact_email, "address": e.address,
                        "description": e.description,
                    }
                eid = mentor.enterprise_id
                stats["job_count"] = db.query(JobPosition).filter(JobPosition.enterprise_id == eid).count()
                all_ent_evals = db.query(EnterpriseEvaluation).filter(
                    EnterpriseEvaluation.enterprise_id == eid
                ).all()
                stats["eval_count"] = len(all_ent_evals)
                scores = [
                    float(e.total_score) for e in all_ent_evals
                    if isinstance(e.total_score, (int, float)) and 0 <= float(e.total_score or 0) <= 100
                ]
                stats["avg_score"] = round(sum(scores) / len(scores), 1) if scores else 0

                # 可见班级：直接绑定班级 + job_class_ref 关联班级
                direct_ids = {r[0] for r in db.query(Class.id).filter(Class.enterprise_id == eid).all()}
                from_job = {
                    r[0] for r in db.query(JobClassRef.class_id)
                    .join(JobPosition, JobPosition.id == JobClassRef.job_id)
                    .filter(JobPosition.enterprise_id == eid).all()
                }
                class_ids = direct_ids | from_job
                if not class_ids:
                    # 兼容老数据：从 linked_classes 逗号列也取一份
                    for (linked,) in db.query(JobPosition.linked_classes).filter(JobPosition.enterprise_id == eid).all():
                        if linked:
                            for sid in linked.split(","):
                                if sid.isdigit():
                                    class_ids.add(int(sid))
                stats["class_count"] = len(class_ids)
                if class_ids:
                    stats["student_count"] = (
                        db.query(func.count(func.distinct(ClassMember.student_id)))
                        .filter(ClassMember.class_id.in_(list(class_ids)))
                        .scalar()
                    ) or 0
                    evaluated_submission_ids = (
                        db.query(EnterpriseEvaluation.submission_id)
                        .filter(EnterpriseEvaluation.enterprise_id == eid)
                    )
                    from app.models.tables import Task
                    stats["pending_eval_count"] = (
                        db.query(Submission)
                        .join(Student, Student.id == Submission.student_id)
                        .join(ClassMember, ClassMember.student_id == Student.id)
                        .join(Task, Task.id == Submission.task_id)
                        .filter(ClassMember.class_id.in_(list(class_ids)))
                        .filter(Task.is_enterprise_project == 1)
                        .filter(~Submission.id.in_(evaluated_submission_ids))
                        .count()
                    )
            extra["enterprise"] = enterprise
            extra["mentor"] = {
                "title": mentor.title if mentor else "",
                "department": mentor.department if mentor else "",
                "is_admin": mentor.is_admin if mentor else 0,
                "joined_at": str(mentor.joined_at) if mentor else "",
            }
            extra["stats"] = stats
    elif ctx["role_ext"] == "student":
        student_id = _account_id_to_student_id(db, acct.id)
        class_count = 0
        submission_count = 0
        eval_count = 0
        avg_score = 0
        if student_id:
            class_count = (
                db.query(func.count(func.distinct(ClassMember.class_id)))
                .filter(ClassMember.student_id == student_id)
                .scalar()
            ) or 0
            sub_q = db.query(Submission).filter(Submission.student_id == student_id)
            submission_count = sub_q.count()
            evals = (
                db.query(Evaluation).join(Submission, Submission.id == Evaluation.submission_id)
                .filter(Submission.student_id == student_id).all()
            )
            eval_count = len(evals)
            eval_scores = [
                float(e.total_score) for e in evals
                if isinstance(e.total_score, (int, float)) and 0 <= float(e.total_score or 0) <= 100
            ]
            avg_score = round(sum(eval_scores) / len(eval_scores), 1) if eval_scores else 0
        extra["stats"] = {
            "class_count": class_count,
            "submission_count": submission_count,
            "evaluation_count": eval_count,
            "avg_score": avg_score,
        }
    elif ctx["role_ext"] == "teacher":
        teacher_id = _account_id_to_teacher_id(db, acct.id)
        class_count = db.query(Class).filter(Class.teacher_id == teacher_id).count() if teacher_id else 0
        student_count = 0
        eval_count = 0
        avg_score = 0
        if class_count and teacher_id:
            class_ids = [r[0] for r in db.query(Class.id).filter(Class.teacher_id == teacher_id).all()]
            student_count = (
                db.query(func.count(func.distinct(ClassMember.student_id)))
                .filter(ClassMember.class_id.in_(class_ids)).scalar()
            ) or 0
            evals = (
                db.query(Evaluation).join(Submission, Submission.id == Evaluation.submission_id)
                .join(ClassMember, ClassMember.student_id == Submission.student_id)
                .filter(ClassMember.class_id.in_(class_ids)).all()
            )
            eval_count = len(evals)
            eval_scores = [
                float(e.total_score) for e in evals
                if isinstance(e.total_score, (int, float)) and 0 <= float(e.total_score or 0) <= 100
            ]
            avg_score = round(sum(eval_scores) / len(eval_scores), 1) if eval_scores else 0
        extra["stats"] = {
            "class_count": class_count,
            "student_count": student_count,
            "evaluation_count": eval_count,
            "avg_score": avg_score,
        }

    base_data.update(extra)
    return {"success": True, "data": base_data}


@router.put("/profile/{user_id}")
def update_profile(user_id: int, req: ProfileUpdate, db: Session = Depends(get_db)):
    ctx = _load_user_context(db, user_id)
    if not ctx:
        raise HTTPException(404, "用户不存在")
    acct = ctx["account"]
    # email/avatar/phone 属于 login_accounts
    if req.email is not None:
        acct.email = req.email
    # real_name / user_number 属于角色表
    role = acct.role
    if req.real_name is not None:
        if role == "teacher" and ctx["role_obj"]:
            ctx["role_obj"].real_name = req.real_name
        elif role == "student" and ctx["role_obj"]:
            ctx["role_obj"].real_name = req.real_name
        elif role == "mentor" and ctx["role_obj"]:
            try:
                ctx["role_obj"].real_name = req.real_name
            except Exception:
                pass
    if req.user_number is not None:
        # 空串统一转 NULL，避免 UNIQUE 冲突
        _n = None if (isinstance(req.user_number, str) and req.user_number.strip() == "") else req.user_number
        if role == "teacher" and ctx["role_obj"]:
            ctx["role_obj"].teacher_no = _n
        elif role == "student" and ctx["role_obj"]:
            ctx["role_obj"].student_no = _n
    db.commit()
    return {"success": True, "message": "资料已更新"}


@router.put("/password/{user_id}")
def change_password(user_id: int, req: PasswordChange, db: Session = Depends(get_db)):
    acct = db.query(LoginAccount).filter(LoginAccount.id == user_id).first()
    if not acct:
        raise HTTPException(404, "用户不存在")
    if not verify_password(req.old_password, acct.password_hash):
        raise HTTPException(400, "旧密码不正确")
    acct.password_hash = hash_password(req.new_password)
    db.commit()
    return {"success": True, "message": "密码已修改"}


@router.post("/avatar/{user_id}")
async def upload_avatar(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    acct = db.query(LoginAccount).filter(LoginAccount.id == user_id).first()
    if not acct:
        raise HTTPException(404, "用户不存在")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {'.png', '.jpg', '.jpeg', '.gif'}:
        raise HTTPException(400, "仅支持 png/jpg/gif 格式")

    filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
    save_path = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    acct.avatar = filename
    db.commit()
    return {"success": True, "avatar": filename}


@router.delete("/account/{user_id}")
def delete_account(user_id: int, db: Session = Depends(get_db)):
    ctx = _load_user_context(db, user_id)
    if not ctx:
        raise HTTPException(404, "用户不存在")
    acct = ctx["account"]

    # 学生删 submissions / class_members
    if acct.role == "student":
        stu_id = _account_id_to_student_id(db, acct.id)
        if stu_id:
            db.query(ClassMember).filter(ClassMember.student_id == stu_id).delete()
            subs = db.query(Submission).filter(Submission.student_id == stu_id).all()
            for sub in subs:
                db.query(Evaluation).filter(Evaluation.submission_id == sub.id).delete()
                try:
                    from app.models.enterprise_models import EnterpriseEvaluation
                    db.query(EnterpriseEvaluation).filter(EnterpriseEvaluation.submission_id == sub.id).delete()
                except Exception:
                    pass
                db.delete(sub)
    # 教师删班级
    elif acct.role == "teacher":
        tid = _account_id_to_teacher_id(db, acct.id)
        if tid:
            classes = db.query(Class).filter(Class.teacher_id == tid).all()
            for c in classes:
                db.query(ClassMember).filter(ClassMember.class_id == c.id).delete()
                db.delete(c)

    db.delete(acct)
    db.commit()
    return {"success": True, "message": "账号已注销"}
