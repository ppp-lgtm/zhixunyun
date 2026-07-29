from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from app.models.database import SessionLocal
from app.models.tables import User, Task, Submission, Evaluation
from app.models.class_models import Class, ClassMember
from app.models.enterprise_models import (
    Enterprise,
    EnterpriseMentor,
    JobPosition,
    EnterpriseEvaluation,
)
from app.utils.auth import hash_password, verify_password, create_token, decode_token

router = APIRouter(prefix="/api/enterprise", tags=["企业端"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Query(..., description="登录 Token"),
    db: Session = Depends(get_db),
):
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Token 无效或已过期")
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


def require_enterprise(user: User = Depends(get_current_user)):
    if user.role != "enterprise":
        raise HTTPException(403, "仅企业导师可访问")
    return user


def get_mentor_enterprise_id(
    user: User = Depends(require_enterprise),
    db: Session = Depends(get_db),
) -> int:
    mentor = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.user_id == user.id)
        .filter(EnterpriseMentor.status == "active")
        .first()
    )
    if not mentor:
        raise HTTPException(403, "当前账号未关联任何企业")
    return mentor.enterprise_id


# ============================================================
# 注册登录 & Profile
# ============================================================

class EnterpriseRegisterRequest(BaseModel):
    model_config = {"extra": "ignore"}
    username: str
    password: str
    real_name: str = ""
    title: str = ""
    enterprise_name: str
    enterprise_short_name: str = ""
    industry: str = ""
    scale: str = ""
    contact_phone: str = ""
    contact_email: str = ""
    address: str = ""
    description: str = ""


class LoginRequest(BaseModel):
    model_config = {"extra": "ignore"}
    username: str
    password: str


@router.post("/register")
def register(req: EnterpriseRegisterRequest, db: Session = Depends(get_db)):
    exist = db.query(User).filter(User.username == req.username).first()
    if exist:
        raise HTTPException(400, "用户名已存在")

    enterprise = (
        db.query(Enterprise)
        .filter(Enterprise.name == req.enterprise_name)
        .first()
    )
    if not enterprise:
        enterprise = Enterprise(
            name=req.enterprise_name,
            short_name=req.enterprise_short_name,
            industry=req.industry,
            scale=req.scale,
            contact_person=req.real_name,
            contact_phone=req.contact_phone,
            contact_email=req.contact_email,
            address=req.address,
            description=req.description,
        )
        db.add(enterprise)
        db.flush()

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        role="enterprise",
        real_name=req.real_name,
    )
    db.add(user)
    db.flush()

    mentor_count = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.enterprise_id == enterprise.id)
        .count()
    )
    mentor = EnterpriseMentor(
        enterprise_id=enterprise.id,
        user_id=user.id,
        real_name=req.real_name,
        title=req.title,
        is_admin=1 if mentor_count == 0 else 0,
    )
    db.add(mentor)
    db.commit()
    db.refresh(user)

    return {
        "success": True,
        "message": "企业注册成功",
        "user_id": user.id,
        "enterprise_id": enterprise.id,
        "is_admin": mentor.is_admin,
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    if user.role != "enterprise":
        raise HTTPException(401, "当前账号不是企业导师账号")

    mentor = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.user_id == user.id)
        .filter(EnterpriseMentor.status == "active")
        .first()
    )
    enterprise = None
    if mentor:
        e = (
            db.query(Enterprise)
            .filter(Enterprise.id == mentor.enterprise_id)
            .first()
        )
        if e:
            enterprise = {
                "id": e.id,
                "name": e.name,
                "short_name": e.short_name,
                "logo": e.logo,
                "industry": e.industry,
            }

    token = create_token(user.id, user.role)
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "real_name": user.real_name,
            "title": mentor.title if mentor else "",
            "is_admin": mentor.is_admin if mentor else 0,
        },
        "enterprise": enterprise,
    }


@router.get("/profile")
def profile(
    user: User = Depends(require_enterprise),
    db: Session = Depends(get_db),
):
    mentor = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.user_id == user.id)
        .first()
    )
    enterprise = None
    if mentor:
        e = (
            db.query(Enterprise)
            .filter(Enterprise.id == mentor.enterprise_id)
            .first()
        )
        if e:
            enterprise = {
                "id": e.id,
                "name": e.name,
                "short_name": e.short_name,
                "logo": e.logo,
                "industry": e.industry,
                "scale": e.scale,
                "contact_person": e.contact_person,
                "contact_phone": e.contact_phone,
                "contact_email": e.contact_email,
                "address": e.address,
                "description": e.description,
            }

    job_count = 0
    eval_count = 0
    pending_eval_count = 0
    if mentor:
        job_count = (
            db.query(JobPosition)
            .filter(JobPosition.enterprise_id == mentor.enterprise_id)
            .count()
        )
        eval_count = (
            db.query(EnterpriseEvaluation)
            .filter(EnterpriseEvaluation.mentor_id == user.id)
            .count()
        )
        class_ids = _enterprise_visible_class_ids(db, mentor.enterprise_id)
        if class_ids:
            evaluated_submission_ids = (
                db.query(EnterpriseEvaluation.submission_id)
                .filter(EnterpriseEvaluation.enterprise_id == mentor.enterprise_id)
                .subquery()
            )
            pending_eval_count = (
                db.query(Submission)
                .join(User, User.id == Submission.student_id)
                .join(ClassMember, ClassMember.student_id == User.id)
                .filter(ClassMember.class_id.in_(list(class_ids)))
                .filter(~Submission.id.in_(evaluated_submission_ids))
                .count()
            )

    return {
        "success": True,
        "user": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "email": getattr(user, "email", "") or "",
            "phone": getattr(user, "phone", "") or "",
            "avatar": getattr(user, "avatar", "") or "",
        },
        "mentor": {
            "title": mentor.title if mentor else "",
            "department": mentor.department if mentor else "",
            "is_admin": mentor.is_admin if mentor else 0,
            "joined_at": str(mentor.joined_at) if mentor else "",
        },
        "enterprise": enterprise,
        "stats": {
            "job_count": job_count,
            "evaluation_count": eval_count,
            "pending_evaluation_count": pending_eval_count,
        },
    }


# ============================================================
# 企业信息管理
# ============================================================

class EnterpriseUpdateRequest(BaseModel):
    name: Optional[str] = None
    short_name: Optional[str] = None
    logo: Optional[str] = None
    industry: Optional[str] = None
    scale: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None
    description: Optional[str] = None


@router.put("/enterprise")
def update_enterprise(
    req: EnterpriseUpdateRequest,
    user: User = Depends(require_enterprise),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    mentor = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.user_id == user.id)
        .first()
    )
    if not mentor or mentor.is_admin != 1:
        raise HTTPException(403, "仅企业管理员可编辑企业信息")

    e = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not e:
        raise HTTPException(404, "企业不存在")

    for k, v in req.model_dump(exclude_unset=True).items():
        setattr(e, k, v)

    db.commit()
    return {"success": True, "message": "企业信息已更新"}


# ============================================================
# 岗位管理 CRUD
# ============================================================

class SkillRequirement(BaseModel):
    name: str
    weight: float = 1.0
    threshold: float = 60.0


class JobCreateRequest(BaseModel):
    title: str
    job_type: str = "技术岗"
    level: str = "初级"
    salary_range: str = ""
    city: str = ""
    description: str = ""
    requirements: str = ""
    responsibilities: str = ""
    skill_requirements: List[SkillRequirement] = []
    tags: str = ""
    linked_classes: str = ""
    status: str = "open"


class JobUpdateRequest(BaseModel):
    title: Optional[str] = None
    job_type: Optional[str] = None
    level: Optional[str] = None
    salary_range: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    skill_requirements: Optional[List[SkillRequirement]] = None
    tags: Optional[str] = None
    linked_classes: Optional[str] = None
    status: Optional[str] = None


def _serialize_skills(skills):
    if not skills:
        return []
    return [
        {
            "name": s.name if hasattr(s, "name") else s["name"],
            "weight": float(s.weight if hasattr(s, "weight") else s.get("weight", 1.0)),
            "threshold": float(
                s.threshold if hasattr(s, "threshold") else s.get("threshold", 60.0)
            ),
        }
        for s in skills
    ]


def _job_to_dict(jp: JobPosition) -> dict:
    skills = []
    if isinstance(jp.skill_requirements, list):
        for s in jp.skill_requirements:
            if isinstance(s, dict):
                skills.append({
                    "name": s.get("name", ""),
                    "weight": float(s.get("weight", 1.0)),
                    "threshold": float(s.get("threshold", 60.0)),
                })
            elif isinstance(s, str):
                skills.append({"name": s, "weight": 1.0, "threshold": 60.0})
    return {
        "id": jp.id,
        "enterprise_id": jp.enterprise_id,
        "title": jp.title,
        "job_type": jp.job_type,
        "level": jp.level,
        "salary_range": jp.salary_range,
        "city": jp.city,
        "description": jp.description,
        "requirements": jp.requirements,
        "responsibilities": jp.responsibilities,
        "skill_requirements": skills,
        "tags": jp.tags or "",
        "tag_list": [t for t in (jp.tags or "").split(",") if t],
        "linked_classes": jp.linked_classes or "",
        "linked_class_ids": [
            int(x) for x in (jp.linked_classes or "").split(",") if x.isdigit()
        ],
        "status": jp.status,
        "created_at": str(jp.created_at) if jp.created_at else "",
        "updated_at": str(jp.updated_at) if jp.updated_at else "",
    }


@router.get("/jobs")
def list_jobs(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: User = Depends(require_enterprise),
):
    q = db.query(JobPosition).filter(JobPosition.enterprise_id == enterprise_id)
    if status:
        q = q.filter(JobPosition.status == status)
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            (JobPosition.title.like(kw))
            | (JobPosition.tags.like(kw))
            | (JobPosition.city.like(kw))
        )

    total = q.count()
    items = (
        q.order_by(JobPosition.updated_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": [_job_to_dict(j) for j in items],
    }


@router.get("/jobs/all")
def list_all_jobs_simple(
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: User = Depends(require_enterprise),
):
    items = (
        db.query(JobPosition)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .order_by(JobPosition.title.asc())
        .all()
    )
    return {
        "success": True,
        "list": [
            {"id": j.id, "title": j.title, "level": j.level, "status": j.status}
            for j in items
        ],
    }


@router.get("/jobs/{job_id}")
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: User = Depends(require_enterprise),
):
    j = (
        db.query(JobPosition)
        .filter(JobPosition.id == job_id)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .first()
    )
    if not j:
        raise HTTPException(404, "岗位不存在")
    return {"success": True, "data": _job_to_dict(j)}


@router.post("/jobs")
def create_job(
    req: JobCreateRequest,
    user: User = Depends(require_enterprise),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    jp = JobPosition(
        enterprise_id=enterprise_id,
        title=req.title,
        job_type=req.job_type,
        level=req.level,
        salary_range=req.salary_range,
        city=req.city,
        description=req.description,
        requirements=req.requirements,
        responsibilities=req.responsibilities,
        skill_requirements=_serialize_skills(req.skill_requirements),
        tags=req.tags,
        linked_classes=req.linked_classes,
        status=req.status,
        created_by=user.id,
    )
    db.add(jp)
    db.commit()
    db.refresh(jp)
    return {"success": True, "message": "岗位已创建", "job_id": jp.id}


@router.put("/jobs/{job_id}")
def update_job(
    job_id: int,
    req: JobUpdateRequest,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: User = Depends(require_enterprise),
):
    j = (
        db.query(JobPosition)
        .filter(JobPosition.id == job_id)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .first()
    )
    if not j:
        raise HTTPException(404, "岗位不存在")

    data = req.model_dump(exclude_unset=True)
    if "skill_requirements" in data and data["skill_requirements"] is not None:
        data["skill_requirements"] = _serialize_skills(data["skill_requirements"])
    for k, v in data.items():
        setattr(j, k, v)

    db.commit()
    return {"success": True, "message": "岗位已更新"}


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: User = Depends(require_enterprise),
):
    j = (
        db.query(JobPosition)
        .filter(JobPosition.id == job_id)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .first()
    )
    if not j:
        raise HTTPException(404, "岗位不存在")
    db.delete(j)
    db.commit()
    return {"success": True, "message": "岗位已删除"}


# ============================================================
# 绑定的班级（给前端下拉框）
# ============================================================

def _enterprise_visible_class_ids(db: Session, enterprise_id: int):
    """企业能看到哪些班级：直接绑定 enterprise_id 的班级 + 所有岗位绑定的班级，合并去重"""
    direct = (
        db.query(Class.id)
        .filter(Class.enterprise_id == enterprise_id)
        .filter(Class.status == "active")
        .all()
    )
    direct_ids = {c[0] for c in direct}
    jobs = (
        db.query(JobPosition.linked_classes)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .all()
    )
    from_job = set()
    for (linked,) in jobs:
        if not linked:
            continue
        for sid in linked.split(","):
            if sid.isdigit():
                from_job.add(int(sid))
    return direct_ids | from_job


@router.get("/linked-classes/options")
def linked_class_options(
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: User = Depends(require_enterprise),
):
    class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if not class_ids:
        return {"success": True, "list": []}
    classes = (
        db.query(Class)
        .filter(Class.id.in_(list(class_ids)))
        .filter(Class.status == "active")
        .all()
    )
    return {
        "success": True,
        "list": [
            {
                "id": c.id,
                "name": c.name,
                "teacher_name": c.teacher_name or "",
                "major": c.major or "",
                "grade": c.grade or "",
            }
            for c in classes
        ],
    }


# ============================================================
# A3 · 企业评价工作台（核心端点组）
# ============================================================

class DimensionScore(BaseModel):
    name: str
    score: float = Field(ge=0, le=100)
    reason: Optional[str] = ""


class EnterpriseEvaluationCreateRequest(BaseModel):
    submission_id: int
    dimension_scores: List[DimensionScore]
    job_fit_score: float = Field(ge=0, le=100, default=0.0)
    strength_points: str = ""
    improvement_points: str = ""
    interview_suggest: str = "maybe"   # recommend / maybe / not_recommend
    comment: str = ""
    matched_job_id: Optional[int] = None


class EnterpriseEvaluationUpdateRequest(BaseModel):
    dimension_scores: Optional[List[DimensionScore]] = None
    job_fit_score: Optional[float] = Field(ge=0, le=100, default=None)
    strength_points: Optional[str] = None
    improvement_points: Optional[str] = None
    interview_suggest: Optional[str] = None
    comment: Optional[str] = None
    matched_job_id: Optional[int] = None


def _to_float(x):
    try:
        return float(x)
    except Exception:
        return 0.0


def _dimension_scores_to_list(ds):
    """把 enterpris_evaluation.dimension_scores JSON 转成稳定列表：
    list 直接返回，dict 转成 [{"name":k,"score":v[0],"reason":v[1] if len>1 else ""}]"""
    if not ds:
        return []
    if isinstance(ds, list):
        return [
            {
                "name": s.get("name", ""),
                "score": _to_float(s.get("score", 0)),
                "reason": s.get("reason", "") or "",
            }
            for s in ds
            if isinstance(s, dict)
        ]
    if isinstance(ds, dict):
        out = []
        for k, v in ds.items():
            if isinstance(v, (list, tuple)) and len(v) >= 1:
                out.append({
                    "name": k,
                    "score": _to_float(v[0]),
                    "reason": v[1] if len(v) > 1 else "",
                })
            else:
                out.append({"name": k, "score": _to_float(v), "reason": ""})
        return out
    return []


def _dimension_total(score_list):
    if not score_list:
        return 0.0
    total = sum(_to_float(s.get("score", 0)) for s in score_list)
    return round(total / len(score_list), 2)


def _enterprise_eval_to_dict(eev: EnterpriseEvaluation, db: Session) -> dict:
    dims = _dimension_scores_to_list(eev.dimension_scores)
    mentor = db.query(User).filter(User.id == eev.mentor_id).first()
    enterprise = db.query(Enterprise).filter(Enterprise.id == eev.enterprise_id).first()
    job = db.query(JobPosition).filter(JobPosition.id == eev.matched_job_id).first() if eev.matched_job_id else None
    return {
        "id": eev.id,
        "submission_id": eev.submission_id,
        "enterprise": {
            "id": enterprise.id,
            "name": enterprise.name,
            "short_name": enterprise.short_name,
            "logo": enterprise.logo,
        } if enterprise else None,
        "mentor": {
            "id": mentor.id if mentor else 0,
            "real_name": mentor.real_name if mentor else "",
            "title": db.query(EnterpriseMentor.title).filter(EnterpriseMentor.user_id == mentor.id).scalar() if mentor else "",
        },
        "total_score": _to_float(eev.total_score) or _dimension_total(dims),
        "dimension_scores": dims,
        "job_fit_score": _to_float(eev.job_fit_score),
        "strength_points": eev.strength_points or "",
        "improvement_points": eev.improvement_points or "",
        "interview_suggest": eev.interview_suggest or "maybe",
        "comment": eev.comment or "",
        "matched_job": {
            "id": job.id,
            "title": job.title,
            "level": job.level,
        } if job else None,
        "created_at": str(eev.created_at) if eev.created_at else "",
    }


def _submission_basic_dict(db: Session, s: Submission, with_student=True, with_task=True) -> dict:
    d = {
        "id": s.id,
        "submission_id": s.id,
        "filename": s.filename or "",
        "file_path": s.file_path or "",
        "submitted_at": str(s.created_at) if s.created_at else "",
    }
    if with_student:
        stu = db.query(User).filter(User.id == s.student_id).first()
        d["student"] = {
            "id": stu.id if stu else 0,
            "real_name": stu.real_name if stu else "",
            "user_number": stu.user_number if stu and hasattr(stu, "user_number") else "",
            "username": stu.username if stu else "",
        }
    if with_task:
        t = db.query(Task).filter(Task.id == s.task_id).first()
        if t:
            d["task"] = {
                "id": t.id,
                "title": t.title,
                "requirements": t.requirements or "",
                "criteria": t.criteria or "",
                "total_score": t.total_score,
                "deadline": str(t.deadline) if t.deadline else "",
                "status": t.status,
            }
    return d


@router.get("/evaluations/submissions")
def list_submissions_to_evaluate(
    class_id: Optional[int] = None,
    job_id: Optional[int] = None,
    status: Optional[str] = Query(None, description="pending=待评价 / done=已评价"),
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: User = Depends(require_enterprise),
):
    """企业导师工作台：列出本企业关联班级下的所有学生提交，可选班级/岗位/状态筛选"""
    class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if not class_ids:
        return {"success": True, "total": 0, "page": page, "page_size": page_size, "list": []}

    if class_id is not None:
        if class_id not in class_ids:
            raise HTTPException(403, "无权访问该班级")
        class_ids = {class_id}

    # 基础查询：这些班级里所有学生的 submission
    q = (
        db.query(Submission)
        .join(User, User.id == Submission.student_id)
        .join(ClassMember, ClassMember.student_id == User.id)
        .filter(ClassMember.class_id.in_(list(class_ids)))
    )

    # job_id 筛选：若指定，则只保留学生所在班级里被对应岗位 linked_classes 覆盖的 submission
    if job_id is not None:
        jp = (
            db.query(JobPosition)
            .filter(JobPosition.id == job_id)
            .filter(JobPosition.enterprise_id == enterprise_id)
            .first()
        )
        if not jp:
            raise HTTPException(404, "岗位不存在或不归本企业所有")
        job_linked = {int(x) for x in (jp.linked_classes or "").split(",") if x.isdigit()}
        if job_linked:
            q = q.filter(ClassMember.class_id.in_(list(job_linked)))
        student_ids = (
            db.query(ClassMember.student_id)
            .filter(ClassMember.class_id.in_(list(job_linked or class_ids)))
            .subquery()
        )
        q = q.filter(Submission.student_id.in_(student_ids))

    # 状态筛选：已评价 / 待评价
    evaluated_subq = (
        db.query(EnterpriseEvaluation.submission_id)
        .filter(EnterpriseEvaluation.enterprise_id == enterprise_id)
    )
    if status == "done":
        q = q.filter(Submission.id.in_(evaluated_subq))
    elif status == "pending":
        q = q.filter(~Submission.id.in_(evaluated_subq))

    # 关键词：学生姓名 / 学号 / 任务标题 / 提交文件名
    if keyword:
        kw = f"%{keyword}%"
        task_ids = (
            db.query(Task.id).filter(Task.title.like(kw)).subquery()
        )
        q = q.filter(
            (User.real_name.like(kw))
            | (getattr(User, "user_number", "").like(kw) if False else User.username.like(kw))
            | (Submission.filename.like(kw))
            | (Submission.task_id.in_(task_ids))
        )

    total = q.count()
    rows = (
        q.order_by(Submission.created_at.desc())
        .distinct()
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    submission_ids = [s.id for s in rows]
    ev_map: Dict[int, EnterpriseEvaluation] = {}
    if submission_ids:
        for eev in (
            db.query(EnterpriseEvaluation)
            .filter(EnterpriseEvaluation.enterprise_id == enterprise_id)
            .filter(EnterpriseEvaluation.submission_id.in_(submission_ids))
            .all()
        ):
            ev_map[eev.submission_id] = eev

    result = []
    for s in rows:
        base = _submission_basic_dict(db, s)
        eev = ev_map.get(s.id)
        base["enterprise_evaluation"] = (
            _enterprise_eval_to_dict(eev, db) if eev else None
        )
        base["evaluation_status"] = "done" if eev else "pending"
        # 所属班级名列表
        cls = (
            db.query(Class.name)
            .join(ClassMember, ClassMember.class_id == Class.id)
            .filter(ClassMember.student_id == s.student_id)
            .filter(ClassMember.class_id.in_(list(class_ids)))
            .all()
        )
        base["classes"] = [name for (name,) in cls]
        result.append(base)

    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": result,
    }


@router.get("/evaluations/submissions/{submission_id}")
def get_submission_detail_for_eval(
    submission_id: int,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: User = Depends(require_enterprise),
):
    """单条提交详情（给企业评分面板右半）。权限：必须在企业可见班级里。"""
    class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if not class_ids:
        raise HTTPException(403, "企业当前没有关联任何班级")

    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        raise HTTPException(404, "提交不存在")

    in_class = (
        db.query(ClassMember)
        .filter(ClassMember.student_id == s.student_id)
        .filter(ClassMember.class_id.in_(list(class_ids)))
        .first()
    )
    if not in_class:
        raise HTTPException(403, "无权访问该提交")

    data = _submission_basic_dict(db, s)
    data["content"] = s.content or ""

    # 已有的 AI + 教师评价，供企业参考
    evs = (
        db.query(Evaluation)
        .filter(Evaluation.submission_id == s.id)
        .order_by(Evaluation.created_at.asc())
        .all()
    )
    data["evaluations"] = []
    for e in evs:
        dims = _dimension_scores_to_list(e.dimension_scores)
        data["evaluations"].append({
            "id": e.id,
            "evaluator_type": e.evaluator_type,
            "total_score": _to_float(e.total_score) or _dimension_total(dims),
            "dimension_scores": dims,
            "comment": e.comment or "",
            "created_at": str(e.created_at) if e.created_at else "",
        })

    # 本企业已提交过的评价
    eev = (
        db.query(EnterpriseEvaluation)
        .filter(EnterpriseEvaluation.enterprise_id == enterprise_id)
        .filter(EnterpriseEvaluation.submission_id == s.id)
        .first()
    )
    data["enterprise_evaluation"] = (
        _enterprise_eval_to_dict(eev, db) if eev else None
    )

    # 可供选择的岗位
    job_options = (
        db.query(JobPosition)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .filter(JobPosition.status != "closed")
        .order_by(JobPosition.title.asc())
        .all()
    )
    data["available_jobs"] = [
        {"id": j.id, "title": j.title, "level": j.level, "city": j.city,
         "job_type": j.job_type, "skill_requirements": _job_to_dict(j)["skill_requirements"]}
        for j in job_options
    ]

    # 学生基本资料：班级 / 加入时间
    data["student_classes"] = [
        {"id": c.id, "name": c.name, "grade": c.grade or "", "major": c.major or ""}
        for c in (
            db.query(Class)
            .join(ClassMember, ClassMember.class_id == Class.id)
            .filter(ClassMember.student_id == s.student_id)
            .filter(ClassMember.class_id.in_(list(class_ids)))
            .all()
        )
    ]

    return {"success": True, "data": data}


@router.post("/evaluations")
def create_enterprise_evaluation(
    req: EnterpriseEvaluationCreateRequest,
    user: User = Depends(require_enterprise),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    # 权限：该 submission 的学生必须在企业可见班级里
    class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if not class_ids:
        raise HTTPException(403, "企业当前没有关联任何班级")
    s = db.query(Submission).filter(Submission.id == req.submission_id).first()
    if not s:
        raise HTTPException(404, "提交不存在")
    in_class = (
        db.query(ClassMember)
        .filter(ClassMember.student_id == s.student_id)
        .filter(ClassMember.class_id.in_(list(class_ids)))
        .first()
    )
    if not in_class:
        raise HTTPException(403, "无权评价该提交")

    # 同企业同一 submission 只能写一条评价（避免重复）
    exist = (
        db.query(EnterpriseEvaluation)
        .filter(EnterpriseEvaluation.enterprise_id == enterprise_id)
        .filter(EnterpriseEvaluation.submission_id == req.submission_id)
        .first()
    )
    if exist:
        raise HTTPException(
            409,
            "该提交本企业已写过评价，请调用 PUT 接口修改；或通过 /compare 查看三方对比。"
        )

    # matched_job_id 校验
    if req.matched_job_id:
        ok = (
            db.query(JobPosition.id)
            .filter(JobPosition.id == req.matched_job_id)
            .filter(JobPosition.enterprise_id == enterprise_id)
            .first()
        )
        if not ok:
            raise HTTPException(400, "matched_job_id 不属于本企业")

    dims = [{"name": d.name, "score": d.score, "reason": d.reason or ""} for d in req.dimension_scores]
    total = _dimension_total(dims)
    eev = EnterpriseEvaluation(
        submission_id=req.submission_id,
        mentor_id=user.id,
        enterprise_id=enterprise_id,
        total_score=total,
        dimension_scores=dims,
        job_fit_score=_to_float(req.job_fit_score),
        strength_points=req.strength_points,
        improvement_points=req.improvement_points,
        interview_suggest=req.interview_suggest if req.interview_suggest in ("recommend", "maybe", "not_recommend") else "maybe",
        comment=req.comment,
        matched_job_id=req.matched_job_id,
    )
    db.add(eev)
    db.commit()
    db.refresh(eev)
    return {
        "success": True,
        "message": "企业评价已提交",
        "evaluation_id": eev.id,
        "total_score": total,
    }


@router.put("/evaluations/{evaluation_id}")
def update_enterprise_evaluation(
    evaluation_id: int,
    req: EnterpriseEvaluationUpdateRequest,
    user: User = Depends(require_enterprise),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    eev = (
        db.query(EnterpriseEvaluation)
        .filter(EnterpriseEvaluation.id == evaluation_id)
        .filter(EnterpriseEvaluation.enterprise_id == enterprise_id)
        .first()
    )
    if not eev:
        raise HTTPException(404, "企业评价不存在或无权修改")
    # 非企业管理员：只能改自己的
    mentor = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.user_id == user.id)
        .filter(EnterpriseMentor.enterprise_id == enterprise_id)
        .first()
    )
    if mentor and mentor.is_admin != 1 and eev.mentor_id != user.id:
        raise HTTPException(403, "只能修改自己写的评价")

    data = req.model_dump(exclude_unset=True)
    if "dimension_scores" in data and data["dimension_scores"] is not None:
        dims = [
            {
                "name": d["name"] if isinstance(d, dict) else getattr(d, "name", ""),
                "score": float(d["score"] if isinstance(d, dict) else getattr(d, "score", 0)),
                "reason": (d.get("reason", "") if isinstance(d, dict) else (getattr(d, "reason", "") or "")),
            }
            for d in data["dimension_scores"]
        ]
        eev.dimension_scores = dims
        eev.total_score = _dimension_total(dims)
        del data["dimension_scores"]
    if "interview_suggest" in data:
        if data["interview_suggest"] not in ("recommend", "maybe", "not_recommend", None):
            raise HTTPException(400, "interview_suggest 非法取值")
    if "matched_job_id" in data and data["matched_job_id"] is not None:
        ok = (
            db.query(JobPosition.id)
            .filter(JobPosition.id == data["matched_job_id"])
            .filter(JobPosition.enterprise_id == enterprise_id)
            .first()
        )
        if not ok:
            raise HTTPException(400, "matched_job_id 不属于本企业")

    for k, v in data.items():
        if v is None:
            continue
        setattr(eev, k, v)

    db.commit()
    return {"success": True, "message": "企业评价已更新", "total_score": eev.total_score}


@router.get("/evaluations/{evaluation_id}")
def get_enterprise_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: User = Depends(require_enterprise),
):
    eev = (
        db.query(EnterpriseEvaluation)
        .filter(EnterpriseEvaluation.id == evaluation_id)
        .filter(EnterpriseEvaluation.enterprise_id == enterprise_id)
        .first()
    )
    if not eev:
        raise HTTPException(404, "企业评价不存在")
    return {"success": True, "data": _enterprise_eval_to_dict(eev, db)}


# ============================================================
# A3 · 三方评分对比 & 一致性分析
# ============================================================

@router.get("/evaluations/compare/{submission_id}")
def compare_three_evaluations(
    submission_id: int,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    user: User = Depends(require_enterprise),
):
    """AI / 教师 / 企业 三方评价对比 + 一致性 + 差异维度高亮。
    角色 enterprise 访问：默认展示本企业那条。如果企业还没评就标 pending。"""
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        raise HTTPException(404, "提交不存在")

    ai_eval = None
    teacher_eval = None
    for e in (
        db.query(Evaluation)
        .filter(Evaluation.submission_id == submission_id)
        .order_by(Evaluation.created_at.asc())
        .all()
    ):
        dims = _dimension_scores_to_list(e.dimension_scores)
        obj = {
            "id": e.id,
            "evaluator_type": e.evaluator_type,
            "total_score": _to_float(e.total_score) or _dimension_total(dims),
            "dimension_scores": dims,
            "comment": e.comment or "",
            "created_at": str(e.created_at) if e.created_at else "",
        }
        if e.evaluator_type == "ai" and ai_eval is None:
            ai_eval = obj
        elif e.evaluator_type == "teacher" and teacher_eval is None:
            teacher_eval = obj

    ent = (
        db.query(EnterpriseEvaluation)
        .filter(EnterpriseEvaluation.submission_id == submission_id)
        .filter(EnterpriseEvaluation.enterprise_id == enterprise_id)
        .first()
    )
    ent_eval = _enterprise_eval_to_dict(ent, db) if ent else None

    # 三方分数汇总
    parties = []
    if ai_eval:
        parties.append({"role": "ai", "label": "AI 自动评价", "total": ai_eval["total_score"], "comment": ai_eval.get("comment", "")})
    if teacher_eval:
        parties.append({"role": "teacher", "label": "教师评价", "total": teacher_eval["total_score"], "comment": teacher_eval.get("comment", "")})
    if ent_eval:
        parties.append({"role": "enterprise", "label": f"{ent_eval['enterprise']['name']} · {ent_eval['mentor']['real_name'] or '企业导师'}",
                        "total": ent_eval["total_score"], "comment": ent_eval.get("comment", "")})

    # 维度对齐（所有出现过的维度名并集，保持出现顺序）
    def dims_by_name(obj):
        return {d["name"]: d["score"] for d in obj.get("dimension_scores", []) or []}
    seen = {}
    ai_dims = dims_by_name(ai_eval) if ai_eval else {}
    te_dims = dims_by_name(teacher_eval) if teacher_eval else {}
    en_dims = dims_by_name(ent_eval) if ent_eval else {}
    for k in list(ai_dims.keys()) + list(te_dims.keys()) + list(en_dims.keys()):
        seen[k] = True
    dimension_names = list(seen.keys())

    dimension_breakdown = []
    max_diff = 0.0
    max_diff_dim = None
    consistency = None  # 0~1，三方总分越接近越高
    for name in dimension_names:
        a = ai_dims.get(name)
        t = te_dims.get(name)
        e = en_dims.get(name)
        vals = [x for x in (a, t, e) if x is not None]
        diff = (max(vals) - min(vals)) if vals else 0
        if len(vals) >= 2 and diff > max_diff:
            max_diff = diff
            max_diff_dim = name
        flag = "warning" if diff >= 20 else ("info" if diff >= 10 else "ok")
        warn = None
        if diff >= 20:
            warn = f"{name} 维度三方差异超过 20 分，建议复核"
        elif diff >= 10:
            warn = f"{name} 维度三方差异超过 10 分，请注意对齐评价标准"
        dimension_breakdown.append({
            "name": name,
            "ai_score": a, "teacher_score": t, "enterprise_score": e,
            "max_diff": round(diff, 2),
            "flag": flag,
            "warning": warn,
        })

    total_vals = [p["total"] for p in parties if p.get("total") is not None]
    if len(total_vals) >= 2:
        spread = max(total_vals) - min(total_vals)
        # 0 分差=1.0；40 分差=0.0
        consistency = round(max(0.0, 1.0 - spread / 40.0), 3)

    summary = {
        "score_spread": round((max(total_vals) - min(total_vals)), 2) if total_vals else 0.0,
        "consistency_index": consistency,
        "max_difference_dimension": max_diff_dim,
        "max_difference": round(max_diff, 2),
        "needs_review": (max_diff >= 20) or (len(total_vals) >= 2 and max(total_vals) - min(total_vals) >= 20),
    }
    if summary["needs_review"] and not summary["max_difference_dimension"] and total_vals:
        # 无维度但总分差异大：归因到整体
        summary["max_difference_dimension"] = "整体总分"

    # 学生/任务基础信息
    base = _submission_basic_dict(db, s)

    return {
        "success": True,
        "data": {
            "submission": base,
            "parties": parties,
            "dimension_breakdown": dimension_breakdown,
            "summary": summary,
            "evaluations": {
                "ai": ai_eval,
                "teacher": teacher_eval,
                "enterprise": ent_eval,
            },
        },
    }


# ============================================================
# A3 · 学生端：浏览企业评价 & 对比
# ============================================================

def _require_student_any_role(
    token: str = Query(..., description="登录 Token"),
    db: Session = Depends(get_db),
) -> User:
    """企业评价学生浏览接口：允许 student 角色访问本人数据；也允许 teacher / enterprise
    看（但在接口层按用户角色继续做权限收敛）。"""
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Token 无效或已过期")
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


@router.get("/student/my-evaluations")
def student_my_enterprise_evaluations(
    page: int = 1,
    page_size: int = 20,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: User = Depends(_require_student_any_role),
):
    """学生本人看所有自己 submission 上产生的企业评价（带三方对比入口）；
    教师 / 企业导师访问：按传入 class_id 作为班级代理筛选，未传 class_id 返回空，防止越权。"""
    base_q = db.query(EnterpriseEvaluation).order_by(EnterpriseEvaluation.created_at.desc())
    if user.role == "student":
        base_q = base_q.join(
            Submission, Submission.id == EnterpriseEvaluation.submission_id
        ).filter(Submission.student_id == user.id)
    elif class_id is not None:
        base_q = base_q.join(Submission, Submission.id == EnterpriseEvaluation.submission_id) \
            .join(ClassMember, ClassMember.student_id == Submission.student_id) \
            .filter(ClassMember.class_id == int(class_id))
    else:
        # 非学生没传 class_id → 不允许查全部，避免越权
        return {"success": True, "total": 0, "page": page, "page_size": page_size, "list": []}

    total = base_q.count()
    rows = (
        base_q.offset((page - 1) * page_size).limit(page_size).all()
    )

    result = []
    for eev in rows:
        d = _enterprise_eval_to_dict(eev, db)
        sub = db.query(Submission).filter(Submission.id == eev.submission_id).first()
        if sub:
            d["submission"] = {
                "id": sub.id,
                "filename": sub.filename or "",
                "submitted_at": str(sub.created_at) if sub.created_at else "",
            }
            t = db.query(Task).filter(Task.id == sub.task_id).first()
            if t:
                d["task"] = {"id": t.id, "title": t.title, "deadline": str(t.deadline) if t.deadline else ""}
        result.append(d)

    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": result,
    }


@router.get("/student/compare/{submission_id}")
def student_compare_three(
    submission_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(_require_student_any_role),
):
    """学生看自己提交的三方对比；教师/企业可访问该班级下的 submission。"""
    s = db.query(Submission).filter(Submission.id == submission_id).first()
    if not s:
        raise HTTPException(404, "提交不存在")
    if user.role == "student":
        if s.student_id != user.id:
            raise HTTPException(403, "无权查看他人评价")
    elif user.role == "enterprise":
        class_ids = _enterprise_visible_class_ids(
            db, get_mentor_enterprise_id(user=user, db=db)
        )
        in_c = (
            db.query(ClassMember)
            .filter(ClassMember.student_id == s.student_id)
            .filter(ClassMember.class_id.in_(list(class_ids)))
            .first()
        )
        if not in_c:
            raise HTTPException(403, "无权查看该提交评价")
    else:  # teacher
        # teacher 不做强校验：默认教师有全校查阅权限
        pass

    # 直接复用 compare_three_evaluations 的构建逻辑（避免重复代码）
    ai_eval = None
    teacher_eval = None
    for e in (
        db.query(Evaluation)
        .filter(Evaluation.submission_id == submission_id)
        .order_by(Evaluation.created_at.asc())
        .all()
    ):
        dims = _dimension_scores_to_list(e.dimension_scores)
        obj = {
            "id": e.id,
            "evaluator_type": e.evaluator_type,
            "total_score": _to_float(e.total_score) or _dimension_total(dims),
            "dimension_scores": dims,
            "comment": e.comment or "",
            "created_at": str(e.created_at) if e.created_at else "",
        }
        if e.evaluator_type == "ai" and ai_eval is None:
            ai_eval = obj
        elif e.evaluator_type == "teacher" and teacher_eval is None:
            teacher_eval = obj

    ents = (
        db.query(EnterpriseEvaluation)
        .filter(EnterpriseEvaluation.submission_id == submission_id)
        .all()
    )
    ent_list = [_enterprise_eval_to_dict(e, db) for e in ents]

    parties = []
    if ai_eval:
        parties.append({"role": "ai", "label": "AI 自动评价", "total": ai_eval["total_score"], "comment": ai_eval.get("comment", "")})
    if teacher_eval:
        parties.append({"role": "teacher", "label": "教师评价", "total": teacher_eval["total_score"], "comment": teacher_eval.get("comment", "")})
    for ee in ent_list:
        parties.append({
            "role": "enterprise",
            "label": f"{ee['enterprise']['name']} · {ee['mentor']['real_name'] or '企业导师'}",
            "total": ee["total_score"],
            "comment": ee.get("comment", ""),
        })

    total_vals = [p["total"] for p in parties if p.get("total") is not None]
    spread = (max(total_vals) - min(total_vals)) if len(total_vals) >= 2 else 0.0
    consistency = round(max(0.0, 1.0 - spread / 40.0), 3) if len(total_vals) >= 2 else None
    summary = {
        "score_spread": round(spread, 2),
        "consistency_index": consistency,
        "needs_review": spread >= 20,
        "enterprise_count": len(ent_list),
    }
    base = _submission_basic_dict(db, s)
    return {
        "success": True,
        "data": {
            "submission": base,
            "parties": parties,
            "summary": summary,
            "evaluations": {
                "ai": ai_eval,
                "teacher": teacher_eval,
                "enterprise": ent_list[0] if ent_list else None,
                "enterprise_list": ent_list,
            },
        },
    }
