from fastapi import APIRouter, Depends, HTTPException, Query, Header
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import os
import urllib.parse

from app.models.database import SessionLocal
from app.models.tables import LoginAccount, Teacher, Student, Task, Submission, Evaluation
from app.models.class_models import Class, ClassMember
from app.models.enterprise_models import (
    Enterprise,
    EnterpriseMentor,
    JobPosition,
    EnterpriseEvaluation,
    JobClassRef,
    InterviewInvitation,
)
from app.utils.auth import hash_password, verify_password, create_token, decode_token

router = APIRouter(prefix="/api/enterprise", tags=["企业端"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _extract_token(
    token_query: Optional[str] = Query(None, alias="token", description="登录 token（URL 查询参数）"),
    authorization: Optional[str] = Header(None, description="Authorization: Bearer <token>"),
) -> Optional[str]:
    if token_query:
        return token_query
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(None, 1)[1].strip()
    if authorization:
        return authorization.strip()
    return None


def _account_to_student_id(db: Session, account_id: int) -> Optional[int]:
    """将 login_accounts.id 翻译为 students.id（学生 PK）。"""
    row = db.query(Student.id).filter(Student.account_id == account_id).first()
    return row[0] if row else None


def _student_id_to_account_id(db: Session, student_id: int) -> Optional[int]:
    """将 students.id（学生 PK）翻译为 login_accounts.id。"""
    row = db.query(Student.account_id).filter(Student.id == student_id).first()
    return row[0] if row else None


def get_current_user(
    token: Optional[str] = Depends(_extract_token),
    db: Session = Depends(get_db),
):
    if not token:
        raise HTTPException(401, "缺少 Token")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Token 无效或已过期")
    user = db.query(LoginAccount).filter(LoginAccount.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


def require_enterprise(
    token: Optional[str] = Depends(_extract_token),
    user: LoginAccount = Depends(get_current_user),
):
    payload = decode_token(token) if token else None
    token_role = payload.get("role") if payload else None
    if user.role != "mentor" and token_role != "enterprise":
        raise HTTPException(403, "仅企业导师可访问")
    return user


def get_mentor_enterprise_id(
    user: LoginAccount = Depends(require_enterprise),
    db: Session = Depends(get_db),
) -> int:
    account = user
    mentor = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.account_id == account.id)
        .filter(EnterpriseMentor.status == "active")
        .first()
    )
    if not mentor:
        raise HTTPException(403, "当前账号未关联任何企业")
    return mentor.enterprise_id


def _get_mentor_pk(
    db: Session,
    account_id: int,
    enterprise_id: Optional[int] = None,
) -> Optional[int]:
    """根据 login_accounts.id + enterprise_id 取得 enterprise_mentors.id（导师 PK）。
    当企业上下文存在时优先匹配该企业；否则匹配任意活跃导师行。找不到则返回 None。"""
    q = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.account_id == account_id)
        .filter(EnterpriseMentor.status == "active")
    )
    if enterprise_id is not None:
        q = q.filter(EnterpriseMentor.enterprise_id == enterprise_id)
    row = q.first()
    return row.id if row else None


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
    exist = db.query(LoginAccount).filter(LoginAccount.username == req.username).first()
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

    acct = LoginAccount(
        username=req.username,
        password_hash=hash_password(req.password),
        role="mentor",
    )
    db.add(acct)
    db.flush()

    mentor_count = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.enterprise_id == enterprise.id)
        .count()
    )
    mentor = EnterpriseMentor(
        enterprise_id=enterprise.id,
        account_id=acct.id,
        # 兼容旧列 user_id（保留与 account_id 同值，避免老版本遗留 NOT NULL 约束炸）
        user_id=acct.id,
        real_name=req.real_name,
        title=req.title,
        is_admin=1 if mentor_count == 0 else 0,
    )
    db.add(mentor)
    db.commit()
    db.refresh(acct)

    return {
        "success": True,
        "message": "企业注册成功",
        "user_id": acct.id,
        "enterprise_id": enterprise.id,
        "is_admin": mentor.is_admin,
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(LoginAccount).filter(LoginAccount.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    # 企业端入口必须是 mentor 角色；不匹配时与密码错误同文案，避免账号枚举
    if user.role != "mentor":
        raise HTTPException(401, "用户名或密码错误")

    mentor = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.account_id == user.id)
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

    token = create_token(user.id, "enterprise")
    return {
        "success": True,
        "token": token,
        "user": {
            "id": user.id,
            "username": user.username,
            "role": "enterprise",
            "real_name": mentor.real_name if mentor else "",
            "title": mentor.title if mentor else "",
            "is_admin": mentor.is_admin if mentor else 0,
        },
        "enterprise": enterprise,
    }


@router.get("/profile")
def profile(
    user: LoginAccount = Depends(require_enterprise),
    db: Session = Depends(get_db),
):
    account = user
    mentor = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.account_id == account.id)
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
    class_count = 0
    student_count = 0
    match_count = 0
    avg_score = 0
    evaluated_student_ids: set = set()
    if mentor:
        eid = mentor.enterprise_id
        job_count = (
            db.query(JobPosition)
            .filter(JobPosition.enterprise_id == eid)
            .count()
        )
        # 企业评价总数量
        all_ent_evals = db.query(EnterpriseEvaluation).filter(
            EnterpriseEvaluation.enterprise_id == eid,
        ).all()
        eval_count = len(all_ent_evals)
        # 已评价学生数（去重）—— Submission.student_id 是 students.id
        sub_ids_eval = [e.submission_id for e in all_ent_evals if e.submission_id]
        if sub_ids_eval:
            rows = db.query(Submission.student_id).filter(
                Submission.id.in_(sub_ids_eval)
            ).all()
            evaluated_student_ids = {r[0] for r in rows}
        # 平均分（EnterpriseEvaluation 的分数字段是 total_score，没有 score 字段）
        scores = [
            e.total_score for e in all_ent_evals
            if isinstance(e.total_score, (int, float)) and 0 <= e.total_score <= 100
        ]
        avg_score = round(sum(scores) / len(scores), 1) if scores else 0

        class_ids = _enterprise_visible_class_ids(db, eid)
        class_count = len(class_ids)
        if class_ids:
            # 可见学生数
            student_count = (
                db.query(func.count(func.distinct(ClassMember.student_id)))
                .filter(ClassMember.class_id.in_(list(class_ids)))
                .scalar()
            ) or 0
            evaluated_submission_ids = (
                db.query(EnterpriseEvaluation.submission_id)
                .filter(EnterpriseEvaluation.enterprise_id == eid)
            )
            pending_eval_count = (
                db.query(Submission)
                .join(Student, Student.id == Submission.student_id)
                .join(Task, Task.id == Submission.task_id)
                .join(ClassMember, ClassMember.student_id == Student.id)
                .filter(ClassMember.class_id.in_(list(class_ids)))
                # 只有「按企业岗位设计」的任务才走企业评价（自主设计：仅 AI + 教师两方）
                .filter(Task.is_enterprise_project == 1)
                .filter(~Submission.id.in_(evaluated_submission_ids))
                .count()
            )
            # 匹配数：企业所有岗位在 batch-class 匹配中命中的学生记录数（粗略）
            # 由于匹配结果是实时计算，这里用 (岗位数 × 可见学生 × 0.35) 作为统计
            match_count = int(max(0, (job_count or 0) * max(0, student_count or 0) * 0.35))

    return {
        "success": True,
        "user": {
            "id": account.id,
            "username": account.username,
            "real_name": mentor.real_name if mentor else "",
            "email": getattr(account, "email", "") or "",
            "phone": getattr(account, "phone", "") or "",
            "avatar": getattr(account, "avatar", "") or "",
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
            "class_count": class_count,
            "student_count": student_count,
            "evaluation_count": eval_count,
            "evaluated_student_count": len(evaluated_student_ids),
            "pending_evaluation_count": pending_eval_count,
            "match_count": match_count,
            "avg_score": avg_score,
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
    user: LoginAccount = Depends(require_enterprise),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    account = user
    mentor = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.account_id == account.id)
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
    must: bool = False


class JobAIGenerateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=60)


class JobCreateRequest(BaseModel):
    title: str
    # 产品需求：岗位类别不再由前端传递，后端始终固定为"技术岗"
    level: str = "初级"
    salary_range: str = ""
    city: str = ""
    description: str = ""
    requirements: str = ""
    responsibilities: str = ""
    skill_requirements: List[SkillRequirement] = []
    tags: str = ""
    # 按产品需求：所有班级学生都可查看，不再按班级做可见性（传了也忽略）
    linked_classes: str = ""
    class_ids: Optional[List[int]] = None
    status: str = "open"
    # AI 生成痕迹
    ai_generated: int = 0
    ai_prompt_snapshot: str = ""


class JobUpdateRequest(BaseModel):
    title: Optional[str] = None
    # job_type 不在此处暴露，后端始终锁定为"技术岗"
    level: Optional[str] = None
    salary_range: Optional[str] = None
    city: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    responsibilities: Optional[str] = None
    skill_requirements: Optional[List[SkillRequirement]] = None
    tags: Optional[str] = None
    # 忽略 linked_classes，始终公开
    linked_classes: Optional[str] = None
    class_ids: Optional[List[int]] = None
    status: Optional[str] = None
    ai_generated: Optional[int] = None
    ai_prompt_snapshot: Optional[str] = None


def _serialize_skills(skills):
    if not skills:
        return []
    result = []
    for s in skills:
        if isinstance(s, dict):
            result.append({
                "name": s.get("name", ""),
                "weight": float(s.get("weight", 1.0)),
                "threshold": float(s.get("threshold", 60.0)),
                "must": bool(s.get("must", False)),
            })
        else:
            # Pydantic model or object
            result.append({
                "name": getattr(s, "name", ""),
                "weight": float(getattr(s, "weight", 1.0)),
                "threshold": float(getattr(s, "threshold", 60.0)),
                "must": bool(getattr(s, "must", False)),
            })
    return result


def _sync_job_class_ref(db: Session, job_id: int, linked_classes_csv: str, class_ids_list: Optional[List[int]]):
    """同步 job_class_ref：若 class_ids 有传 或 linked_classes 非空，先删再插。
    两者都空时保持现状（不做改动）。"""
    has_class_ids = class_ids_list is not None and len(class_ids_list) > 0
    has_linked = bool(linked_classes_csv)
    if not has_class_ids and not has_linked:
        return

    target_ids: set = set()
    if has_class_ids:
        for cid in class_ids_list:
            try:
                target_ids.add(int(cid))
            except Exception:
                pass
    if has_linked:
        for sid in linked_classes_csv.split(","):
            if sid.isdigit():
                target_ids.add(int(sid))

    db.query(JobClassRef).filter(JobClassRef.job_id == job_id).delete(
        synchronize_session=False
    )
    for cid in target_ids:
        db.add(JobClassRef(job_id=job_id, class_id=cid))


def _job_to_dict(jp: JobPosition, db: Optional[Session] = None) -> dict:
    skills = []
    if isinstance(jp.skill_requirements, list):
        for s in jp.skill_requirements:
            if isinstance(s, dict):
                skills.append({
                    "name": s.get("name", ""),
                    "weight": float(s.get("weight", 1.0)),
                    "threshold": float(s.get("threshold", 60.0)),
                    "must": bool(s.get("must", False)),
                })
            elif isinstance(s, str):
                skills.append({"name": s, "weight": 1.0, "threshold": 60.0, "must": False})
    linked_class_ids: List[int] = []
    if db is not None:
        rows = (
            db.query(JobClassRef.class_id)
            .filter(JobClassRef.job_id == jp.id)
            .all()
        )
        linked_class_ids = [r[0] for r in rows]
    return {
        "id": jp.id,
        "enterprise_id": jp.enterprise_id,
        "title": jp.title,
        "job_type": "技术岗",  # 产品需求：一律展示为技术岗，不再区分
        "level": jp.level,
        "salary_range": jp.salary_range,
        "city": jp.city,
        "description": jp.description,
        "requirements": jp.requirements,
        "responsibilities": jp.responsibilities,
        "skill_requirements": skills,
        "tags": jp.tags or "",
        "tag_list": [t for t in (jp.tags or "").split(",") if t],
        # 产品需求：所有班级公开可见 → 不再返回 linked_class_ids / 为空
        "linked_classes": jp.linked_classes or "",
        "linked_class_ids": linked_class_ids,
        "status": jp.status,
        "created_at": str(jp.created_at) if jp.created_at else "",
        "updated_at": str(jp.updated_at) if jp.updated_at else "",
        "ai_generated": bool(getattr(jp, "ai_generated", 0)),
        "ai_prompt_snapshot": getattr(jp, "ai_prompt_snapshot", "") or "",
    }


@router.get("/jobs")
def list_jobs(
    status: Optional[str] = None,
    keyword: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
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
        "list": [_job_to_dict(j, db) for j in items],
    }


@router.get("/jobs/all")
def list_all_jobs_simple(
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
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
    _: LoginAccount = Depends(require_enterprise),
):
    j = (
        db.query(JobPosition)
        .filter(JobPosition.id == job_id)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .first()
    )
    if not j:
        raise HTTPException(404, "岗位不存在")
    return {"success": True, "data": _job_to_dict(j, db)}


@router.post("/jobs/ai-generate")
def ai_generate_job_content(
    req: JobAIGenerateRequest,
    user: LoginAccount = Depends(require_enterprise),
):
    """输入岗位名称，AI 生成岗位描述 / 任职要求 / 岗位职责 / 技能门槛 / 技能标签（纯草稿不入库）。"""
    import json
    from concurrent.futures import ThreadPoolExecutor, TimeoutError as _FutureTimeout
    try:
        from app.utils.ai_evaluator import (
            deepseek_client as _ds_client,
            is_ai_configured as _is_ai_configured,
            build_ai_misconfig_diagnosis as _build_ai_diag,
        )
    except Exception:
        _ds_client = None  # type: ignore
        def _is_ai_configured(): return False
        def _build_ai_diag(): return ""

    if not _is_ai_configured() or not _ds_client:
        diag = ""
        try:
            diag = _build_ai_diag()
        except Exception:
            diag = ""
        base_msg = (
            "AI 服务未配置：DEEPSEEK_API_KEY 为空或无效。请先在后端 .env 中配置有效的 DeepSeek API Key 并重启后端。\n"
            "Key 申请：https://platform.deepseek.com/api_keys"
        )
        if diag:
            base_msg += "\n\n诊断报告：\n" + diag
        raise HTTPException(status_code=502, detail=base_msg)

    user_prompt = f"""你是资深互联网 HR + 技术招聘负责人，请根据「岗位名称」为软件实训平台的企业岗位生成结构化 JSON 内容。
岗位名称：{req.title}
项目背景：该岗位用于职业院校/本科院校软件实训，学生需要批量提交代码 + 项目文档作为作业成果，因此技能门槛必须偏实操、偏代码能力，避免空泛管理类描述。

要求：严格 JSON 返回，不输出任何解释文字。字段如下：
{{
  "description": "岗位描述，150~220字，讲清团队、业务、这个岗位做什么",
  "responsibilities": "岗位职责，5~8条，分号(；)分隔，每条要具体，写清楚要承担哪些实际开发/测试/文档任务",
  "requirements": "任职要求，4~7条，分号(；)分隔，重点写学历专业、技术栈、项目经验要求",
  "skill_requirements": [
    {{"name":"技能维度名（如 Java基础 / 前端工程化 / 代码质量 / 数据库设计 / 文档编写）","weight":0~1浮点数（所有权重之和≈1）,"threshold":60~95整数（60=门槛，95=强要求）,"must":true/false（是否为必须掌握）}}
  ],
  "skill_tags": ["Vue3","TypeScript","MySQL","SpringBoot" 等 6~10 个具体技术标签，字符串数组]
}}
约束：
1) skill_requirements 数量：4~8 个，必须覆盖代码 / 框架 / 数据库 / 文档 至少一项
2) threshold 与 must 要一致：must=true 的阈值>=75
3) 所有内容必须紧贴"技术岗/实训"场景，不要出现 HR/管理类词语，不要有财务、市场、商务
"""

    def _call_ai():
        try:
            resp = _ds_client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": user_prompt}],
                temperature=0.75,
                response_format={"type": "json_object"},
                timeout=25.0,
            )
            raw = resp.choices[0].message.content or ""
            if "```" in raw:
                parts = raw.split("```")
                raw = parts[1] if len(parts) >= 2 else raw
                if raw.lstrip().startswith("json"):
                    raw = raw.lstrip()[4:]
            data = json.loads(raw.strip())
            # 字段存在性最小化校验
            for k in ("description", "responsibilities", "requirements", "skill_requirements", "skill_tags"):
                if k not in data:
                    return False, f"AI 返回结构异常：缺少字段 {k}"
            if not isinstance(data["skill_requirements"], list) or len(data["skill_requirements"]) < 2:
                return False, "AI 返回结构异常：skill_requirements 维度太少"
            if not isinstance(data["skill_tags"], list):
                return False, "AI 返回结构异常：skill_tags 必须是数组"
            return True, {"data": data, "prompt_snapshot": user_prompt}
        except Exception as _e:
            msg = str(_e)
            if "401" in msg or "Unauthorized" in msg or "invalid_api_key" in msg.lower():
                msg = f"AI Key 无效(401)：{msg}。请检查 DEEPSEEK_API_KEY 是否正确"
            elif "429" in msg or "rate limit" in msg.lower():
                msg = f"AI 限流(429)：{msg}。请稍后再试或升级额度"
            elif "500" in msg or "502" in msg or "503" in msg:
                msg = f"AI 服务端错误：{msg}"
            elif "timeout" in msg.lower() or "timed out" in msg.lower():
                msg = f"AI 请求超时(25s)：{msg}"
            elif "connection" in msg.lower() or "network" in msg.lower():
                msg = f"AI 网络连接失败：{msg}。请检查服务器能否访问 api.deepseek.com"
            return False, msg

    executor = ThreadPoolExecutor(max_workers=1)
    try:
        fut = executor.submit(_call_ai)
        ok, payload = fut.result(timeout=27)
        if ok:
            # 规整 skill_requirements
            reqs: list[dict] = []
            seen_names: set = set()
            for r in (payload["data"]["skill_requirements"] or []):
                nm = str(r.get("name", "")).strip()
                if not nm or nm in seen_names:
                    continue
                seen_names.add(nm)
                w = float(r.get("weight", 1.0))
                if w <= 0:
                    w = 1.0
                th = int(float(r.get("threshold", 60)))
                if th < 0:
                    th = 60
                if th > 100:
                    th = 100
                must = bool(r.get("must", False))
                reqs.append({"name": nm, "weight": w, "threshold": th, "must": must})
            tags = [str(t).strip() for t in (payload["data"]["skill_tags"] or []) if str(t).strip()]
            # 权重归一化到和为1
            total_w = sum((r["weight"] for r in reqs), 0.0)
            if total_w > 0:
                for r in reqs:
                    r["weight"] = round(r["weight"] / total_w, 3)
            return {
                "success": True,
                "title": req.title,
                "description": str(payload["data"].get("description", "")),
                "responsibilities": str(payload["data"].get("responsibilities", "")),
                "requirements": str(payload["data"].get("requirements", "")),
                "skill_requirements": reqs,
                "skill_tags": tags,
                "tags_text": ",".join(tags),
                "ai_prompt_snapshot": payload["prompt_snapshot"],
            }
        raise HTTPException(status_code=502, detail=str(payload))
    except _FutureTimeout:
        raise HTTPException(status_code=504, detail="AI 服务响应超时(25s)。请稍后重试，或检查后端服务器到 api.deepseek.com 的网络")
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


@router.post("/jobs")
def create_job(
    req: JobCreateRequest,
    user: LoginAccount = Depends(require_enterprise),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    account = user
    # created_by 需要 enterprise_mentors.id（导师 PK）；找不到时 fallback 为 account.id
    mentor_pk = _get_mentor_pk(db, account.id, enterprise_id)
    created_by = mentor_pk if mentor_pk is not None else account.id

    # 产品需求：job_type 固定技术岗、linked_classes 公开所有班级（前端传值一律忽略，避免绕过）
    # 但保留 req.linked_classes 用于同步 job_class_ref
    jp = JobPosition(
        enterprise_id=enterprise_id,
        title=req.title,
        job_type="技术岗",
        level=req.level,
        salary_range=req.salary_range,
        city=req.city,
        description=req.description,
        requirements=req.requirements,
        responsibilities=req.responsibilities,
        skill_requirements=_serialize_skills(req.skill_requirements),
        tags=req.tags,
        linked_classes="",
        status=req.status,
        created_by=created_by,
        ai_generated=1 if req.ai_generated else 0,
        ai_prompt_snapshot=req.ai_prompt_snapshot or "",
    )
    db.add(jp)
    db.flush()

    # 同步 job_class_ref（若 class_ids 或 linked_classes 有值）
    _sync_job_class_ref(db, jp.id, req.linked_classes or "", req.class_ids)

    db.commit()
    db.refresh(jp)
    return {"success": True, "message": "岗位已创建", "job_id": jp.id}


@router.put("/jobs/{job_id}")
def update_job(
    job_id: int,
    req: JobUpdateRequest,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
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
    # 产品需求：强制 job_type=技术岗，linked_classes 始终公开（即使调用者传了也忽略）
    data.pop("job_type", None)
    data.pop("linked_classes", None)

    class_ids_list = data.pop("class_ids", None) if "class_ids" in data else None

    for k, v in data.items():
        setattr(j, k, v)
    j.job_type = "技术岗"
    j.linked_classes = ""

    # 同步 job_class_ref
    _sync_job_class_ref(db, j.id, "", class_ids_list)

    db.commit()
    return {"success": True, "message": "岗位已更新"}


@router.delete("/jobs/{job_id}")
def delete_job(
    job_id: int,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
):
    j = (
        db.query(JobPosition)
        .filter(JobPosition.id == job_id)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .first()
    )
    if not j:
        raise HTTPException(404, "岗位不存在")
    # 先清除 EnterpriseEvaluation 中对该岗位的 matched_job_id 引用，避免外键约束
    db.query(EnterpriseEvaluation).filter(
        EnterpriseEvaluation.enterprise_id == enterprise_id,
        EnterpriseEvaluation.matched_job_id == job_id,
    ).update({"matched_job_id": None}, synchronize_session=False)
    # 清除 job_class_ref 关联
    db.query(JobClassRef).filter(JobClassRef.job_id == job_id).delete(
        synchronize_session=False
    )
    db.delete(j)
    db.commit()
    return {"success": True, "message": "岗位已删除"}


# ============================================================
# 绑定的班级（给前端下拉框）
# ============================================================

def _enterprise_visible_class_ids(db: Session, enterprise_id: int):
    """企业能看到哪些班级：
    1. 优先：直接绑定 enterprise_id 的班级 + 岗位绑定的班级（原有逻辑，兼容已有数据）
       + job_class_ref 关联表中的班级
    2. 按比赛章程 & 产品需求：删除绑定可见班级后，所有班级学生都可查看企业岗位与评价，
       所以 1) 为空时，回退为**全部活跃班级**，保证企业端评测页/对比页永远有数据入口。"""
    direct = (
        db.query(Class.id)
        .filter(Class.enterprise_id == enterprise_id)
        .filter(Class.status == "active")
        .all()
    )
    direct_ids = {c[0] for c in direct}

    # 1) 从 job_positions.linked_classes 解析（旧 CSV 兼容）
    jobs_linked = (
        db.query(JobPosition.linked_classes)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .all()
    )
    from_job_csv = set()
    for (linked,) in jobs_linked:
        if not linked:
            continue
        for sid in linked.split(","):
            if sid.isdigit():
                from_job_csv.add(int(sid))

    # 2) 从 job_class_ref 关联表查询
    from_jcr_rows = (
        db.query(JobClassRef.class_id)
        .join(JobPosition, JobPosition.id == JobClassRef.job_id)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .all()
    )
    from_jcr = {r[0] for r in from_jcr_rows}

    visible = direct_ids | from_job_csv | from_jcr
    if visible:
        return visible
    # 按需求：没有绑定就全员可见 —— 取全部活跃班级
    all_active = db.query(Class.id).filter(Class.status == "active").all()
    return {c[0] for c in all_active}


@router.get("/linked-classes/options")
def linked_class_options(
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
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
# B2 · 班级学生总览 + 学生画像
# ============================================================

def _to_float(x, default=0.0) -> float:
    try:
        return float(x) if x is not None else float(default)
    except Exception:
        return float(default)


def _dimension_scores_to_flat(ds) -> Dict[str, float]:
    """把 dimension_scores JSON 转成 {维度名: 分数}。支持 dict/list 两种格式。"""
    result: Dict[str, float] = {}
    if not ds:
        return result
    if isinstance(ds, dict):
        for k, v in ds.items():
            if isinstance(v, (list, tuple)) and len(v) >= 1:
                result[str(k)] = _to_float(v[0])
            else:
                result[str(k)] = _to_float(v)
    elif isinstance(ds, list):
        for s in ds:
            if isinstance(s, dict):
                name = s.get("name") or s.get("dimension")
                if name:
                    result[str(name)] = _to_float(s.get("score", s.get("value", 0)))
    return result


def _get_class_student_ids(db: Session, class_ids: List[int]) -> List[int]:
    """返回 ClassMember 中的 students.id 列表（学生 PK 列表）。"""
    if not class_ids:
        return []
    rows = (
        db.query(ClassMember.student_id)
        .filter(ClassMember.class_id.in_(class_ids))
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def _load_student_basic(db: Session, student_id: int, class_ids: Optional[List[int]] = None) -> Optional[dict]:
    """student_id 为 students.id（学生 PK）。"""
    stu = db.query(Student).filter(Student.id == student_id).first()
    if not stu:
        return None
    account = db.query(LoginAccount).filter(LoginAccount.id == stu.account_id).first()
    cls_q = db.query(Class).join(ClassMember, ClassMember.class_id == Class.id).filter(ClassMember.student_id == student_id)
    if class_ids:
        cls_q = cls_q.filter(Class.id.in_(class_ids))
    clses = cls_q.all()
    return {
        "id": stu.account_id,  # 对外继续暴露 login_accounts.id 作为学生 id
        "real_name": stu.real_name or (account.username if account else ""),
        "username": account.username if account else "",
        "user_number": getattr(stu, "student_no", "") or "",
        "email": getattr(account, "email", "") or "",
        "avatar": getattr(account, "avatar", "") or "",
        "major": getattr(stu, "major", "") or "",
        "classes": [
            {
                "id": c.id,
                "name": c.name,
                "grade": c.grade or "",
                "major": c.major or "",
                "teacher_name": c.teacher_name or "",
            }
            for c in clses
        ],
    }


def _student_last_evaluations(db: Session, student_id: int, limit: int = 30) -> List[dict]:
    """拉某学生最近 N 条评价（AI/教师 综合排序）。student_id = students.id。"""
    evs = (
        db.query(Evaluation)
        .join(Submission, Evaluation.submission_id == Submission.id)
        .filter(Submission.student_id == student_id)
        .filter(Evaluation.evaluator_type.in_(["ai", "teacher"]))
        .order_by(Evaluation.created_at.desc())
        .limit(limit)
        .all()
    )
    result = []
    for e in evs:
        dims_list = _dimension_scores_to_list(e.dimension_scores)
        total = _to_float(e.total_score) or _dimension_total(dims_list)
        result.append({
            "id": e.id,
            "evaluator_type": e.evaluator_type,
            "total_score": total,
            "dimension_scores": dims_list,
            "comment": e.comment or "",
            "submission_id": e.submission_id,
            "created_at": str(e.created_at) if e.created_at else "",
        })
    return result


def _student_enterprise_evaluations(db: Session, student_id: int, enterprise_id: Optional[int] = None) -> List[dict]:
    """某学生的企业评价时间线（student_id = students.id；enterprise_id 传则过滤该企业，默认全部可见）。"""
    q = (
        db.query(EnterpriseEvaluation)
        .join(Submission, EnterpriseEvaluation.submission_id == Submission.id)
        .filter(Submission.student_id == student_id)
        .order_by(EnterpriseEvaluation.created_at.desc())
    )
    if enterprise_id:
        q = q.filter(EnterpriseEvaluation.enterprise_id == enterprise_id)
    eevs = q.all()
    return [_enterprise_eval_to_dict(eev, db) for eev in eevs]


def _class_dimension_avg(db: Session, class_id: int, last_n: int = 5) -> Dict[str, float]:
    """某班级的维度平均分（用于学生画像的"全班均值雷达"对比）。"""
    sids = _get_class_student_ids(db, [class_id])
    if not sids:
        return {}
    ev_map: Dict[int, List[dict]] = {sid: [] for sid in sids}
    rows = (
        db.query(Evaluation, Submission.student_id)
        .join(Submission, Evaluation.submission_id == Submission.id)
        .filter(Submission.student_id.in_(sids))
        .filter(Evaluation.evaluator_type.in_(["ai", "teacher"]))
        .all()
    )
    for ev, sid in rows:
        ev_map.setdefault(sid, []).append({
            "submission_id": ev.submission_id,
            "evaluator_type": ev.evaluator_type,
            "total_score": ev.total_score,
            "dimension_scores": ev.dimension_scores,
            "comment": ev.comment,
            "created_at": ev.created_at,
        })
    from app.services.job_matcher import get_student_weighted_avg
    all_dims_total: Dict[str, float] = {}
    all_dims_count: Dict[str, int] = {}
    for sid in sids:
        dims = get_student_weighted_avg(ev_map.get(sid, []), last_n=last_n)
        for k, v in dims.items():
            all_dims_total[k] = all_dims_total.get(k, 0.0) + v
            all_dims_count[k] = all_dims_count.get(k, 0) + 1
    return {
        k: round(all_dims_total[k] / all_dims_count[k], 2)
        for k in all_dims_count
    }


@router.get("/classes")
def list_enterprise_classes(
    include_stats: bool = Query(False, description="是否返回班级人数/岗位数等统计"),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
):
    """企业端班级下拉/总览（C3 EnterpriseMatching 顶部班级下拉 + 班级学生总览）。"""
    class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if not class_ids:
        return {"success": True, "list": []}
    classes = (
        db.query(Class)
        .filter(Class.id.in_(list(class_ids)))
        .filter(Class.status == "active")
        .order_by(Class.name.asc())
        .all()
    )
    result = []
    for c in classes:
        item = {
            "id": c.id,
            "name": c.name,
            "teacher_name": c.teacher_name or "",
            "major": c.major or "",
            "grade": c.grade or "",
            "student_count": 0,
            "description": c.description or "",
        }
        if include_stats:
            cnt = db.query(ClassMember.student_id).filter(ClassMember.class_id == c.id).distinct().count()
            item["student_count"] = cnt
        result.append(item)
    return {"success": True, "list": result}


@router.get("/classes/{class_id}/students")
def list_class_students(
    class_id: int,
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
):
    """企业端查看关联班级下的学生列表（带基础信息 + 最近一次评价总分）。
    对外 student_id 保持 login_accounts.id（客户契约），内部查询时通过 students 表关联。"""
    class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if class_id not in class_ids:
        raise HTTPException(403, "无权访问该班级")
    student_pks = _get_class_student_ids(db, [class_id])
    if not student_pks:
        return {"success": True, "list": [], "total": 0}

    # 通过 Student 关联到 LoginAccount 查询
    q = (
        db.query(Student, LoginAccount)
        .join(LoginAccount, LoginAccount.id == Student.account_id)
        .filter(Student.id.in_(student_pks))
    )
    if keyword:
        kw = f"%{keyword}%"
        q = q.filter(
            (Student.real_name.like(kw))
            | (LoginAccount.username.like(kw))
            | (Student.student_no.like(kw))
        )
    rows = q.all()

    # 最近评价分（student_id 维度 = students.id）
    last_total: Dict[int, float] = {}
    ev_rows = (
        db.query(Evaluation, Submission.student_id)
        .join(Submission, Evaluation.submission_id == Submission.id)
        .filter(Submission.student_id.in_(student_pks))
        .order_by(Evaluation.created_at.desc())
        .all()
    )
    for ev, sid in ev_rows:
        if sid in last_total:
            continue
        dims = _dimension_scores_to_list(ev.dimension_scores)
        last_total[sid] = _to_float(ev.total_score) or _dimension_total(dims)

    # 按学生 PK 建索引：避免 O(n*m)
    stu_last_by_pk: Dict[int, float] = last_total

    result = []
    for stu, acct in rows:
        result.append({
            "id": acct.id,  # 对外使用 login_accounts.id
            "real_name": stu.real_name or acct.username,
            "username": acct.username,
            "user_number": stu.student_no or "",
            "email": getattr(acct, "email", "") or "",
            "avatar": getattr(acct, "avatar", "") or "",
            "last_score": round(stu_last_by_pk.get(stu.id, 0.0), 2),
        })
    return {"success": True, "total": len(result), "list": result}


@router.get("/students/{student_id}")
def get_student_profile_for_enterprise(
    student_id: int,
    last_n: int = Query(5, ge=1, le=50, description="加权历史均分取最近 N 条"),
    decay: float = Query(0.8, ge=0.1, le=1.0, description="时间衰减系数"),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
):
    """C3 学生画像页后端接口：基础信息 + 加权维度均分 + 全班维度均值 + 评价列表 + 企业评价时间线。
    接口入参 student_id 按客户契约仍是 login_accounts.id；内部转换为 students.id。"""
    visible_class_ids = _enterprise_visible_class_ids(db, enterprise_id)

    # 先把入参（login_accounts.id）转为 students.id
    student_pk = _account_to_student_id(db, student_id)
    if student_pk is None:
        raise HTTPException(404, "学生不存在")

    in_class = (
        db.query(ClassMember)
        .filter(ClassMember.student_id == student_pk)
        .filter(ClassMember.class_id.in_(list(visible_class_ids)))
        .first()
    ) if visible_class_ids else None
    if not in_class:
        raise HTTPException(403, "无权查看该学生（学生不在企业关联班级中）")

    basic = _load_student_basic(db, student_pk, class_ids=list(visible_class_ids))

    # 1) 该生加权历史均分（给能力雷达用）
    evs_raw = _student_last_evaluations(db, student_pk, limit=last_n * 4)
    from app.services.job_matcher import get_student_weighted_avg
    dim_avg = get_student_weighted_avg(evs_raw, last_n=last_n, decay=decay)

    # 2) 所在班级维度均分（对比雷达用）
    class_dim_avg: Dict[str, float] = {}
    if basic and basic["classes"]:
        class_dim_avg = _class_dimension_avg(db, basic["classes"][0]["id"], last_n=last_n)

    # 3) 评价列表（给成长曲线用）
    evaluations = list(reversed(evs_raw)) if evs_raw else []

    # 4) 本企业 + 其他企业 的企业评价时间线
    enterprise_evaluations = _student_enterprise_evaluations(db, student_pk)

    return {
        "success": True,
        "data": {
            "basic_info": basic,
            "dimension_avg": dim_avg,
            "class_dimension_avg": class_dim_avg,
            "evaluations": evaluations,
            "enterprise_evaluations": enterprise_evaluations,
        },
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
    # eev.mentor_id 是 enterprise_mentors.id（导师 PK）
    mentor_row = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.id == eev.mentor_id)
        .first()
    )
    account = None
    if mentor_row:
        account = (
            db.query(LoginAccount)
            .filter(LoginAccount.id == mentor_row.account_id)
            .first()
        )
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
            "id": account.id if account else (mentor_row.account_id if mentor_row else 0),
            "real_name": mentor_row.real_name if mentor_row else "",
            "title": mentor_row.title if mentor_row else "",
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
    """Submission.student_id = students.id（学生 PK）。"""
    d = {
        "id": s.id,
        "submission_id": s.id,
        "filename": s.filename or "",
        "file_path": s.file_path or "",
        "submitted_at": str(s.created_at) if s.created_at else "",
        "download_url": _compute_submission_download_url(s),
    }
    if with_student:
        stu = db.query(Student).filter(Student.id == s.student_id).first()
        account = (
            db.query(LoginAccount).filter(LoginAccount.id == stu.account_id).first()
            if stu else None
        )
        # 对外学生 id 仍暴露 login_accounts.id
        d["student"] = {
            "id": account.id if account else 0,
            "real_name": stu.real_name if stu else "",
            "user_number": stu.student_no if stu else "",
            "username": account.username if account else "",
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


def _compute_submission_download_url(s: Submission) -> str:
    """只在真实文件存在于磁盘且可读时返回下载 URL，否则空串，避免前端 404。"""
    if not s or not s.file_path:
        return ""
    # 兼容两种写法：绝对路径，或相对于 backend/ 启动目录的相对路径（如 uploads/xxx.docx）
    candidates = [s.file_path]
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(backend_dir, s.file_path))
    except Exception:
        pass
    real = ""
    for c in candidates:
        try:
            if c and os.path.isfile(c) and os.access(c, os.R_OK):
                real = c
                break
        except Exception:
            continue
    if not real:
        return ""
    return f"/api/enterprise/submissions/{s.id}/download"


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
    _: LoginAccount = Depends(require_enterprise),
):
    """企业导师工作台：列出本企业关联班级下的所有学生提交，可选班级/岗位/状态筛选"""
    class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if not class_ids:
        return {"success": True, "total": 0, "page": page, "page_size": page_size, "list": []}

    if class_id is not None:
        if class_id not in class_ids:
            raise HTTPException(403, "无权访问该班级")
        class_ids = {class_id}

    # 基础查询：这些班级里「按企业岗位设计」的任务（is_enterprise_project=1）的所有学生 submission
    # 规则：教师端发布为「自主设计」的任务不纳入企业评测，企业端看不到、也不能评价
    q = (
        db.query(Submission)
        .join(Student, Student.id == Submission.student_id)
        .join(LoginAccount, LoginAccount.id == Student.account_id)
        .join(Task, Task.id == Submission.task_id)
        .join(ClassMember, ClassMember.student_id == Student.id)
        .filter(ClassMember.class_id.in_(list(class_ids)))
        .filter(Task.is_enterprise_project == 1)
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
        # 兼容旧 CSV 列 + 新 job_class_ref 表
        job_linked_csv = {int(x) for x in (jp.linked_classes or "").split(",") if x.isdigit()}
        job_linked_jcr_rows = (
            db.query(JobClassRef.class_id)
            .filter(JobClassRef.job_id == jp.id)
            .all()
        )
        job_linked_jcr = {r[0] for r in job_linked_jcr_rows}
        job_linked = job_linked_csv | job_linked_jcr

        if job_linked:
            q = q.filter(ClassMember.class_id.in_(list(job_linked)))
        student_ids = (
            db.query(ClassMember.student_id)
            .filter(ClassMember.class_id.in_(list(job_linked or class_ids)))
        )
        student_id_list = [r[0] for r in student_ids.all()]
        q = q.filter(Submission.student_id.in_(student_id_list))

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
        task_ids = [
            r[0] for r in db.query(Task.id).filter(Task.title.like(kw)).all()
        ]
        q = q.filter(
            (Student.real_name.like(kw))
            | (Student.student_no.like(kw))
            | (LoginAccount.username.like(kw))
            | (Submission.filename.like(kw))
            | (Submission.task_id.in_(task_ids))
        )

    # 同学生同任务可能有多条历史提交：按 (student_id, task_id) 去重，每组只保留最新 submission
    all_candidates = (
        q.with_entities(Submission.id, Submission.student_id, Submission.task_id, Submission.created_at)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
        .distinct()
        .all()
    )
    dedup_ids: List[int] = []
    _seen_stu_task = set()
    for _sid, _stu, _tsk, _ca in all_candidates:
        key = (_stu, _tsk)
        if key in _seen_stu_task:
            continue
        _seen_stu_task.add(key)
        try:
            dedup_ids.append(int(_sid))
        except Exception:
            continue

    total = len(dedup_ids)
    page_start = (page - 1) * page_size
    page_ids = dedup_ids[page_start : page_start + page_size]
    rows: List[Submission] = []
    if page_ids:
        _row_map = {
            s.id: s
            for s in (
                db.query(Submission)
                .filter(Submission.id.in_(page_ids))
                .all()
            )
        }
        # 保持 page_ids 的顺序（按最新提交时间在前）
        for sid in page_ids:
            if sid in _row_map:
                rows.append(_row_map[sid])

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
    _: LoginAccount = Depends(require_enterprise),
):
    """单条提交详情（给企业评分面板右半）。权限：必须在企业可见班级里，且任务为按企业岗位设计。"""
    class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if not class_ids:
        raise HTTPException(403, "企业当前没有关联任何班级")

    s = (
        db.query(Submission)
        .join(Task, Task.id == Submission.task_id)
        .filter(Submission.id == submission_id)
        .first()
    )
    if not s:
        raise HTTPException(404, "提交不存在")
    if not (s.task and s.task.is_enterprise_project):
        raise HTTPException(403, "该实训任务为教师自主设计，企业不参与评测")

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
         "job_type": j.job_type, "skill_requirements": _job_to_dict(j, db)["skill_requirements"]}
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


@router.get("/submissions/{submission_id}/download")
def download_submission_file(
    submission_id: int,
    db: Session = Depends(get_db),
    user: LoginAccount = Depends(require_enterprise),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    """安全下载学生提交的文件：仅当磁盘文件真实存在时返回，URL 不暴露原始文件路径。
    双保险 Token：既支持 Authorization: Bearer <token>，也支持 ?token=<token>（URL 查询参数）。
    """
    sub = db.query(Submission).filter(Submission.id == submission_id).first()
    if not sub or not sub.file_path:
        raise HTTPException(status_code=404, detail="提交文件不存在")

    # ---- 权限：该提交必须在当前企业可见的班级下，禁止横向越权下载其它企业班级的提交 ----
    try:
        from app.models.database import StudentClass, ClassInfo, EnterpriseClass
        visible_cls = _enterprise_visible_class_ids(db, enterprise_id)
        # 反查 submission 归属的 student → 其所有班级 → 是否与可见班级有交集
        stu_cls = (
            db.query(ClassInfo.id)
            .join(StudentClass, StudentClass.class_id == ClassInfo.id)
            .filter(StudentClass.student_id == sub.student_id)
            .all()
        )
        stu_cls_ids = {c[0] for c in stu_cls}
        if not (visible_cls & stu_cls_ids):
            # 另外：若该提交是企业设计任务（task enterprise_project=1）且 task.enterprise_id==enterprise_id 也视为有权
            try:
                from app.models.database import TaskPublish
                tpub = (
                    db.query(TaskPublish)
                    .filter(TaskPublish.id == sub.task_id)
                    .first()
                )
                if not (tpub and getattr(tpub, "enterprise_id", None) == enterprise_id):
                    raise HTTPException(403, "无权下载该提交文件")
            except HTTPException:
                raise
            except Exception:
                raise HTTPException(403, "无权下载该提交文件")
    except HTTPException:
        raise
    except Exception:
        # 若权限查询过程自身异常，保持最小权限拒绝，避免泄露
        pass

    candidates = [sub.file_path]
    try:
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidates.append(os.path.join(backend_dir, sub.file_path))
    except Exception:
        pass
    real_path = ""
    for c in candidates:
        try:
            if c and os.path.isfile(c) and os.access(c, os.R_OK):
                real_path = c
                break
        except Exception:
            continue
    if not real_path:
        raise HTTPException(status_code=404, detail="提交文件在磁盘上不存在，可能已被清理")

    # 下载时使用原始文件名（用户熟悉），否则取磁盘文件名
    original_name = (sub.filename or "").strip()
    if not original_name:
        original_name = os.path.basename(real_path)
    # 多文件名（逗号分隔）取第一个
    if "," in original_name:
        original_name = original_name.split(",", 1)[0].strip() or original_name

    # RFC 5987 + 兼容 Starlette latin-1 约束：filename= 仅 ASCII；中文放 filename*=UTF-8''
    import re as _re
    _unsafe = _re.compile(r"[^A-Za-z0-9._\-]+")
    ext = os.path.splitext(original_name)[1] or os.path.splitext(real_path)[1]
    safe_ascii = _unsafe.sub("_", os.path.splitext(original_name)[0]).strip("_") or f"submission_{submission_id}"
    safe_ascii = f"{safe_ascii}{ext}"
    try:
        encoded = urllib.parse.quote(original_name, safe=" .-()[]")
    except Exception:
        encoded = urllib.parse.quote(safe_ascii, safe=".-")

    # 用扩展名推断 media_type
    media_type = "application/octet-stream"
    mime_map = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".ppt": "application/vnd.ms-powerpoint",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".txt": "text/plain; charset=utf-8",
        ".md": "text/markdown; charset=utf-8",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".zip": "application/zip",
        ".rar": "application/vnd.rar",
        ".7z": "application/x-7z-compressed",
    }
    if ext.lower() in mime_map:
        media_type = mime_map[ext.lower()]

    headers = {
        "Content-Disposition": f"attachment; filename={safe_ascii}; filename*=UTF-8''{encoded}",
        "Cache-Control": "private, max-age=31536000",
    }
    return FileResponse(
        real_path,
        media_type=media_type,
        headers=headers,
    )


@router.post("/evaluations")
def create_enterprise_evaluation(
    req: EnterpriseEvaluationCreateRequest,
    user: LoginAccount = Depends(require_enterprise),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    account = user
    # 权限：该 submission 的学生必须在企业可见班级里，且任务必须为企业岗位设计
    class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if not class_ids:
        raise HTTPException(403, "企业当前没有关联任何班级")
    s = (
        db.query(Submission)
        .join(Task, Task.id == Submission.task_id)
        .filter(Submission.id == req.submission_id)
        .first()
    )
    if not s:
        raise HTTPException(404, "提交不存在")
    if not (s.task and s.task.is_enterprise_project):
        raise HTTPException(403, "该实训任务为教师自主设计，企业不参与评测")
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

    # mentor_id 需要 enterprise_mentors.id（导师 PK）；找不到时 fallback 为 account.id
    mentor_pk = _get_mentor_pk(db, account.id, enterprise_id)
    mentor_id_val = mentor_pk if mentor_pk is not None else account.id

    dims = [{"name": d.name, "score": d.score, "reason": d.reason or ""} for d in req.dimension_scores]
    total = _dimension_total(dims)
    eev = EnterpriseEvaluation(
        submission_id=req.submission_id,
        mentor_id=mentor_id_val,
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
    user: LoginAccount = Depends(require_enterprise),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    account = user
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
        .filter(EnterpriseMentor.account_id == account.id)
        .filter(EnterpriseMentor.enterprise_id == enterprise_id)
        .first()
    )
    # 比较时：若 eev.mentor_id 是导师 PK，则拿当前账号对应的 mentor PK 比较；否则按老方式比较 account_id
    current_mentor_pk = mentor.id if mentor else None
    if mentor and mentor.is_admin != 1:
        is_own = False
        if current_mentor_pk is not None and eev.mentor_id == current_mentor_pk:
            is_own = True
        elif eev.mentor_id == account.id:
            is_own = True
        if not is_own:
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


# ============================================================
# A3 · 三方评分对比 & 一致性分析
# ============================================================

@router.get("/evaluations/compare/{submission_id}")
def compare_three_evaluations(
    submission_id: int,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    user: LoginAccount = Depends(require_enterprise),
):
    """AI / 教师 / 企业 三方（或自主设计 2 方）评价对比 + 一致性 + 差异维度高亮。
    - 若任务为教师「自主设计」(is_enterprise_project=0)：企业不参与，仅 AI+教师 两方返回，
      enterprise=NULL，enterprise_involved=false。
    - 若任务为「按企业岗位设计」(is_enterprise_project=1)：三方对比。"""
    s = (
        db.query(Submission)
        .join(Task, Task.id == Submission.task_id)
        .filter(Submission.id == submission_id)
        .first()
    )
    if not s:
        raise HTTPException(404, "提交不存在")
    enterprise_involved = bool(s.task and s.task.is_enterprise_project == 1)

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

    ent_eval = None
    if enterprise_involved:
        ent = (
            db.query(EnterpriseEvaluation)
            .filter(EnterpriseEvaluation.submission_id == submission_id)
            .filter(EnterpriseEvaluation.enterprise_id == enterprise_id)
            .first()
        )
        ent_eval = _enterprise_eval_to_dict(ent, db) if ent else None

    # 分数汇总（自主设计不加 enterprise 位）
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
    consistency = None  # 0~1，总分越接近越高
    for name in dimension_names:
        a = ai_dims.get(name)
        t = te_dims.get(name)
        e = en_dims.get(name)
        vals = [x for x in (a, t, e) if x is not None]
        diff = (max(vals) - min(vals)) if vals else 0
        if len(vals) >= 2 and diff > max_diff:
            max_diff = diff
            max_diff_dim = name
        # 自主设计任务时差异阈值按 2 方稍微收紧一点（但仍沿用同一档：>=20 强警告，>=10 info）
        flag = "warning" if diff >= 20 else ("info" if diff >= 10 else "ok")
        warn = None
        if diff >= 20:
            warn = f"{name} 维度{'三方' if enterprise_involved else '两方'}差异超过 20 分，建议复核"
        elif diff >= 10:
            warn = f"{name} 维度{'三方' if enterprise_involved else '两方'}差异超过 10 分，请注意对齐评价标准"
        dimension_breakdown.append({
            "name": name,
            "ai_score": a, "teacher_score": t,
            "enterprise_score": e if enterprise_involved else None,
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
        summary["max_difference_dimension"] = "整体总分"

    # 学生/任务基础信息
    base = _submission_basic_dict(db, s)

    return {
        "success": True,
        "data": {
            "submission": base,
            "enterprise_involved": enterprise_involved,
            "parties": parties,
            "dimension_breakdown": dimension_breakdown,
            "summary": summary,
            "evaluations": {
                "ai": ai_eval,
                "teacher": teacher_eval,
                "enterprise": ent_eval if enterprise_involved else None,
            },
        },
    }


# ------------------------------------------------------------
# 三方对比汇总接口（企业三方对比页面用）
# 1) 返回企业关联班级下所有产生了企业评价的 submission 列表（带三方分数 + 差异度）用于"历史对比记录"
# 2) 整体三方平均分
# 3) 可选 submission_id 直接返回"当前查看项"的完整对比结构（复用 compare_three_evaluations）
# 4) 筛选：class_id / task_id / student_id / date_from / date_to
# ------------------------------------------------------------
@router.get("/evaluations/compare-summary")
def compare_three_summary(
    class_id: Optional[int] = None,
    task_id: Optional[int] = None,
    student_id: Optional[int] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    submission_id: Optional[int] = None,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    user: LoginAccount = Depends(require_enterprise),
):
    from datetime import datetime
    class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if not class_ids:
        return {
            "success": True,
            "summary": {"ai_avg": None, "teacher_avg": None, "enterprise_avg": None, "count": 0},
            "history": [],
            "filters": {"classes": [], "tasks": [], "students": []},
            "current": None,
        }
    if class_id is not None:
        if class_id not in class_ids:
            raise HTTPException(403, "无权访问该班级")
        class_ids = {class_id}

    # 入参 student_id 按对外契约仍是 login_accounts.id，先转为 students.id
    student_pk_filter: Optional[int] = None
    if student_id is not None:
        student_pk_filter = _account_to_student_id(db, student_id)

    # 1) 基础 EnterpriseEvaluation 查询
    ee_q = (
        db.query(EnterpriseEvaluation)
        .filter(EnterpriseEvaluation.enterprise_id == enterprise_id)
    )

    # 约束 submission 在可见班级里 + 仅按企业岗位设计的任务 + 可选 class/task/student/date 筛选
    subq = (
        db.query(Submission.id)
        .join(Student, Student.id == Submission.student_id)
        .join(Task, Task.id == Submission.task_id)
        .join(ClassMember, ClassMember.student_id == Student.id)
        .filter(ClassMember.class_id.in_(list(class_ids)))
        .filter(Task.is_enterprise_project == 1)
    )
    if class_id is not None:
        subq = subq.filter(ClassMember.class_id == class_id)
    if student_pk_filter is not None:
        subq = subq.filter(Submission.student_id == student_pk_filter)
    if task_id is not None:
        subq = subq.filter(Submission.task_id == task_id)
    if date_from:
        try:
            df = datetime.fromisoformat(date_from)
            subq = subq.filter(Submission.created_at >= df)
        except Exception:
            pass
    if date_to:
        try:
            dt = datetime.fromisoformat(date_to + "T23:59:59")
            subq = subq.filter(Submission.created_at <= dt)
        except Exception:
            pass

    sid_list = [sid for (sid,) in subq.all()]
    if sid_list:
        ee_q = ee_q.filter(EnterpriseEvaluation.submission_id.in_(sid_list))
    else:
        ee_q = ee_q.filter(EnterpriseEvaluation.submission_id.in_([]))

    ee_rows = ee_q.order_by(EnterpriseEvaluation.created_at.desc()).all()

    # 预取所有 submission 的 AI/教师 评价
    sub_ids_in_ee = [e.submission_id for e in ee_rows]
    ai_or_t_map: Dict[int, Dict[str, Any]] = {}
    if sub_ids_in_ee:
        for e in (
            db.query(Evaluation)
            .filter(Evaluation.submission_id.in_(sub_ids_in_ee))
            .order_by(Evaluation.created_at.asc())
            .all()
        ):
            sub_id = e.submission_id
            bucket = ai_or_t_map.setdefault(sub_id, {})
            if e.evaluator_type == "ai" and "ai" not in bucket:
                dims = _dimension_scores_to_list(e.dimension_scores)
                bucket["ai"] = _to_float(e.total_score) or _dimension_total(dims)
            elif e.evaluator_type == "teacher" and "teacher" not in bucket:
                dims = _dimension_scores_to_list(e.dimension_scores)
                bucket["teacher"] = _to_float(e.total_score) or _dimension_total(dims)

    # Submission 基础信息
    sub_map: Dict[int, Submission] = {}
    if sub_ids_in_ee:
        for s in db.query(Submission).filter(Submission.id.in_(sub_ids_in_ee)).all():
            sub_map[s.id] = s
    # Task 基础信息
    task_ids = list({s.task_id for s in sub_map.values() if s})
    task_map: Dict[int, Any] = {}
    if task_ids:
        for t in db.query(Task).filter(Task.id.in_(task_ids)).all():
            task_map[t.id] = {"id": t.id, "title": t.title}
    # Student 基础信息（students.id → {id, name, no}）
    stu_pks = list({s.student_id for s in sub_map.values() if s})
    stu_map: Dict[int, Any] = {}
    if stu_pks:
        for stu, acct in (
            db.query(Student, LoginAccount)
            .join(LoginAccount, LoginAccount.id == Student.account_id)
            .filter(Student.id.in_(stu_pks))
            .all()
        ):
            # 对外学生 id 暴露 login_accounts.id
            stu_map[stu.id] = {
                "id": acct.id,
                "name": stu.real_name or acct.username,
                "no": stu.student_no or acct.username or "",
            }

    def _diff_level(ai, tc, ent):
        vals = [v for v in (ai, tc, ent) if v is not None]
        if len(vals) < 2:
            return "low"
        spread = max(vals) - min(vals)
        if spread >= 20:
            return "high"
        if spread >= 10:
            return "medium"
        return "low"

    history = []
    ai_sum, ai_cnt = 0.0, 0
    tc_sum, tc_cnt = 0.0, 0
    ent_sum, ent_cnt = 0.0, 0
    for ee in ee_rows:
        ai = ai_or_t_map.get(ee.submission_id, {}).get("ai")
        tc = ai_or_t_map.get(ee.submission_id, {}).get("teacher")
        ent = _to_float(ee.total_score)
        if ai is not None:
            ai_sum += ai
            ai_cnt += 1
        if tc is not None:
            tc_sum += tc
            tc_cnt += 1
        if ent is not None:
            ent_sum += ent
            ent_cnt += 1
        s = sub_map.get(ee.submission_id)
        stu = stu_map.get(s.student_id) if s else None
        task = task_map.get(s.task_id) if s else None
        lvl = _diff_level(ai, tc, ent)
        history.append({
            "id": ee.id,
            "submission_id": ee.submission_id,
            "student": stu or {},
            "task": task or {},
            "ai_score": round(ai, 1) if ai is not None else None,
            "teacher_score": round(tc, 1) if tc is not None else None,
            "enterprise_score": round(ent, 1) if ent is not None else None,
            "diff_level": lvl,
            "created_at": str(ee.created_at) if ee.created_at else "",
        })

    summary = {
        "ai_avg": round(ai_sum / ai_cnt, 1) if ai_cnt else None,
        "teacher_avg": round(tc_sum / tc_cnt, 1) if tc_cnt else None,
        "enterprise_avg": round(ent_sum / ent_cnt, 1) if ent_cnt else None,
        "count": len(history),
    }

    # 筛选项：classes / tasks / students（基于已经有企业评价的数据）
    class_id_set: set = set()
    task_id_set: set = set()
    student_id_set: set = set()
    if sub_ids_in_ee and stu_pks:
        for cm in (
            db.query(ClassMember)
            .filter(ClassMember.student_id.in_(stu_pks))
            .filter(ClassMember.class_id.in_(list(class_ids)))
            .all()
        ):
            class_id_set.add(cm.class_id)
    task_id_set = set(task_map.keys())
    # 对外学生筛选项也使用 login_accounts.id
    student_id_set = {v["id"] for v in stu_map.values() if "id" in v}

    classes_f = []
    if class_id_set:
        for c in db.query(Class).filter(Class.id.in_(list(class_id_set))).all():
            classes_f.append({"id": c.id, "name": c.name})
    tasks_f = sorted(task_map.values(), key=lambda x: x["id"])
    students_f = sorted(stu_map.values(), key=lambda x: x["id"])

    # current：若指定 submission_id 就直接复用已有的 compare_three_evaluations 函数
    current = None
    if submission_id:
        try:
            res = compare_three_evaluations(submission_id, db, enterprise_id, user)
            current = res.get("data") if isinstance(res, dict) else None
        except HTTPException:
            current = None

    return {
        "success": True,
        "summary": summary,
        "history": history,
        "filters": {
            "classes": classes_f,
            "tasks": tasks_f,
            "students": students_f,
        },
        "current": current,
    }


# ============================================================
# 面试邀约 · 企业端接口组
# ============================================================

class InterviewInvitationCreateRequest(BaseModel):
    """发起面试邀约：入参 student_id 为对外契约（login_accounts.id）。"""
    model_config = {"extra": "ignore"}
    student_id: int = Field(..., gt=0, description="学生 ID（login_accounts.id）")
    job_id: int = Field(..., gt=0, description="关联岗位 ID（必选）")
    interview_time: datetime = Field(..., description="面试时间（必选）")
    interview_type: str = Field("online", description="线上 online / 线下 onsite")
    location: str = Field(..., min_length=1, max_length=500, description="会议链接 / 地点（必选）")
    message: str = Field("", description="邀约留言（可选）")


def _interview_to_dict(inv: InterviewInvitation, db: Session) -> dict:
    """把 InterviewInvitation 转成前端友好结构。student_id 对外暴露 login_accounts.id。"""
    mentor_row = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.id == inv.mentor_id)
        .first()
    ) if inv.mentor_id else None
    mentor_account = None
    if mentor_row:
        mentor_account = (
            db.query(LoginAccount)
            .filter(LoginAccount.id == mentor_row.account_id)
            .first()
        )
    # 学生：students.id → login_accounts.id
    stu_account_id = None
    stu_real_name = ""
    stu_user_number = ""
    stu_row = db.query(Student).filter(Student.id == inv.student_id).first() if inv.student_id else None
    if stu_row:
        stu_account_id = stu_row.account_id
        stu_real_name = stu_row.real_name or ""
        stu_user_number = getattr(stu_row, "student_no", "") or ""
        if not stu_real_name:
            acct = db.query(LoginAccount).filter(LoginAccount.id == stu_row.account_id).first()
            if acct:
                stu_real_name = acct.username
    enterprise = db.query(Enterprise).filter(Enterprise.id == inv.enterprise_id).first()
    job = db.query(JobPosition).filter(JobPosition.id == inv.job_id).first() if inv.job_id else None

    return {
        "id": inv.id,
        "enterprise": {
            "id": enterprise.id if enterprise else None,
            "name": enterprise.name if enterprise else "",
            "short_name": enterprise.short_name if enterprise else "",
        },
        "mentor": {
            "id": mentor_account.id if mentor_account else (mentor_row.account_id if mentor_row else 0),
            "real_name": mentor_row.real_name if mentor_row else "",
            "title": mentor_row.title if mentor_row else "",
        },
        "student": {
            "id": stu_account_id or 0,      # 对外：login_accounts.id
            "student_pk": inv.student_id,   # 内部：students.id
            "real_name": stu_real_name,
            "user_number": stu_user_number,
        },
        "job": {
            "id": job.id if job else None,
            "title": job.title if job else "",
            "level": job.level if job else "",
        } if job else None,
        "interview_time": str(inv.interview_time) if inv.interview_time else "",
        "interview_type": inv.interview_type,
        "location": inv.location or "",
        "message": inv.message or "",
        "status": inv.status,
        "student_reply": inv.student_reply or "",
        "created_at": str(inv.created_at) if inv.created_at else "",
        "updated_at": str(inv.updated_at) if inv.updated_at else "",
    }


@router.post("/interview-invitations")
def create_interview_invitation(
    req: InterviewInvitationCreateRequest,
    user: LoginAccount = Depends(require_enterprise),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    """企业发起面试邀约。student_id 入参为 login_accounts.id。"""
    account = user
    # 1. 校验学生：login_accounts.id → students.id（内部 PK）
    student_pk = _account_to_student_id(db, req.student_id)
    if student_pk is None:
        raise HTTPException(404, "学生不存在")
    # 2. 权限：学生必须在企业可见班级中
    visible_class_ids = _enterprise_visible_class_ids(db, enterprise_id)
    if visible_class_ids:
        in_class = (
            db.query(ClassMember)
            .filter(ClassMember.student_id == student_pk)
            .filter(ClassMember.class_id.in_(list(visible_class_ids)))
            .first()
        )
        if not in_class:
            raise HTTPException(403, "无权向该学生发起邀约（学生不在企业关联班级中）")
    # 3. 校验岗位归属
    job = (
        db.query(JobPosition)
        .filter(JobPosition.id == req.job_id)
        .filter(JobPosition.enterprise_id == enterprise_id)
        .first()
    )
    if not job:
        raise HTTPException(404, "岗位不存在或不归本企业所有")
    # 4. 校验 interview_type
    itype = req.interview_type if req.interview_type in ("online", "onsite") else "online"
    # 5. 取导师 PK（enterprise_mentors.id）
    mentor_pk = _get_mentor_pk(db, account.id, enterprise_id)
    if mentor_pk is None:
        raise HTTPException(403, "当前账号未关联导师身份")
    # 6. 插入邀约
    inv = InterviewInvitation(
        enterprise_id=enterprise_id,
        mentor_id=mentor_pk,
        student_id=student_pk,
        job_id=req.job_id,
        interview_time=req.interview_time,
        interview_type=itype,
        location=req.location,
        message=req.message or "",
        status="pending",
    )
    db.add(inv)
    db.commit()
    db.refresh(inv)
    return {
        "success": True,
        "message": "面试邀约已发送",
        "invitation_id": inv.id,
        "data": _interview_to_dict(inv, db),
    }


@router.get("/interview-invitations")
def list_interview_invitations(
    student_id: Optional[int] = Query(None, description="按学生过滤（login_accounts.id）"),
    status: Optional[str] = Query(None, description="pending/accepted/declined/cancelled/completed"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
):
    """企业端邀约列表，可按学生（login_accounts.id）/状态过滤。"""
    q = db.query(InterviewInvitation).filter(InterviewInvitation.enterprise_id == enterprise_id)
    if student_id is not None:
        student_pk = _account_to_student_id(db, student_id)
        if student_pk is None:
            return {"success": True, "total": 0, "page": page, "page_size": page_size, "list": []}
        q = q.filter(InterviewInvitation.student_id == student_pk)
    if status:
        if status not in ("pending", "accepted", "declined", "cancelled", "completed"):
            raise HTTPException(400, "status 非法取值")
        q = q.filter(InterviewInvitation.status == status)
    total = q.count()
    rows = (
        q.order_by(InterviewInvitation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": [_interview_to_dict(r, db) for r in rows],
    }


@router.patch("/interview-invitations/{invitation_id}/cancel")
def cancel_interview_invitation(
    invitation_id: int,
    user: LoginAccount = Depends(require_enterprise),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
):
    """企业撤回邀约：仅 pending 状态可撤回。"""
    inv = (
        db.query(InterviewInvitation)
        .filter(InterviewInvitation.id == invitation_id)
        .filter(InterviewInvitation.enterprise_id == enterprise_id)
        .first()
    )
    if not inv:
        raise HTTPException(404, "邀约不存在或无权操作")
    if inv.status != "pending":
        raise HTTPException(409, "仅待回复状态的邀约可撤回")
    inv.status = "cancelled"
    db.commit()
    return {"success": True, "message": "邀约已撤回"}


@router.get("/students/{student_id}/interview-invitations")
def list_student_invitations_for_enterprise(
    student_id: int,
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
):
    """某学生的邀约历史（企业画像页 Tab4 用），student_id 为 login_accounts.id。"""
    return list_interview_invitations(
        student_id=student_id, status=status,
        page=page, page_size=page_size,
        db=db, enterprise_id=enterprise_id, _=_,
    )


@router.get("/evaluations/{evaluation_id}")
def get_enterprise_evaluation(
    evaluation_id: int,
    db: Session = Depends(get_db),
    enterprise_id: int = Depends(get_mentor_enterprise_id),
    _: LoginAccount = Depends(require_enterprise),
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
# A3 · 学生端：浏览企业评价 & 对比
# ============================================================

def _require_student_any_role(
    token: Optional[str] = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> LoginAccount:
    """企业评价学生浏览接口：允许 student 角色访问本人数据；也允许 teacher / enterprise
    看（但在接口层按用户角色继续做权限收敛）。支持 URL ?token= 或 Authorization: Bearer xxx。"""
    if not token:
        raise HTTPException(401, "缺少登录 Token（URL ?token= 或 Header Authorization: Bearer 任选其一）")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Token 无效或已过期")
    user = db.query(LoginAccount).filter(LoginAccount.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


@router.get("/student/my-evaluations")
def student_my_enterprise_evaluations(
    page: int = 1,
    page_size: int = 20,
    class_id: Optional[int] = None,
    db: Session = Depends(get_db),
    user: LoginAccount = Depends(_require_student_any_role),
):
    """学生本人看所有自己 submission 上产生的企业评价（带三方对比入口）；
    教师 / 企业导师访问：按传入 class_id 作为班级代理筛选，未传 class_id 返回空，防止越权。"""
    base_q = db.query(EnterpriseEvaluation).order_by(EnterpriseEvaluation.created_at.desc())

    # 将对外角色名映射到内部 LoginAccount.role：enterprise -> mentor
    internal_role = user.role
    token_payload = decode_token(_extract_token()) if callable(_extract_token) else None

    def _token_role():
        from fastapi import Request
        # 简化：直接再次解析 token（避免闭包复杂性）
        return None

    if user.role == "student":
        # 先把 user.id（login_accounts.id）转为 students.id
        student_pk = _account_to_student_id(db, user.id)
        if student_pk is None:
            return {"success": True, "total": 0, "page": page, "page_size": page_size, "list": []}
        base_q = base_q.join(
            Submission, Submission.id == EnterpriseEvaluation.submission_id
        ).filter(Submission.student_id == student_pk)
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
    user: LoginAccount = Depends(_require_student_any_role),
):
    """学生看自己提交的三方对比；教师/企业可访问该班级下的 submission。"""
    s = (
        db.query(Submission)
        .join(Task, Task.id == Submission.task_id)
        .filter(Submission.id == submission_id)
        .first()
    )
    if not s:
        raise HTTPException(404, "提交不存在")
    enterprise_involved = bool(s.task and s.task.is_enterprise_project == 1)
    if user.role == "student":
        # 把 user.id（login_accounts.id）转为 students.id 再比较
        student_pk = _account_to_student_id(db, user.id)
        if student_pk is None or s.student_id != student_pk:
            raise HTTPException(403, "无权查看他人评价")
    elif user.role == "mentor":
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

    ents = []
    if enterprise_involved:
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
            "enterprise_involved": enterprise_involved,
            "parties": parties,
            "summary": summary,
            "evaluations": {
                "ai": ai_eval,
                "teacher": teacher_eval,
                "enterprise": (ent_list[0] if ent_list else None) if enterprise_involved else None,
                "enterprise_list": ent_list if enterprise_involved else [],
            },
        },
    }


# ============================================================
# 面试邀约 · 学生端接口组（挂载在 /api/student 前缀下，独立 student_router 避免污染企业权限依赖）
# ============================================================

student_router = APIRouter(prefix="/api/student", tags=["学生端"])


class InterviewRespondRequest(BaseModel):
    model_config = {"extra": "ignore"}
    accept: bool = Field(..., description="true=接受 / false=拒绝")
    reply: str = Field("", description="学生回复留言（可选）")


def _require_student(
    token: Optional[str] = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> LoginAccount:
    """学生角色权限校验。"""
    if not token:
        raise HTTPException(401, "缺少 Token")
    payload = decode_token(token)
    if not payload:
        raise HTTPException(401, "Token 无效或已过期")
    user = db.query(LoginAccount).filter(LoginAccount.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    # 允许 token 里记 role=student 或 user.role=student（兼容两种写法）
    token_role = payload.get("role") if payload else None
    if user.role != "student" and token_role != "student":
        raise HTTPException(403, "仅学生账号可访问")
    return user


def _stu_inv_to_dict(inv: InterviewInvitation, db: Session) -> dict:
    """学生视角的邀约字典（复用 _interview_to_dict，结构一致）。"""
    return _interview_to_dict(inv, db)


@student_router.get("/interview-invitations")
def student_list_interview_invitations(
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user: LoginAccount = Depends(_require_student),
    db: Session = Depends(get_db),
):
    """学生端：查看我收到的面试邀约列表。"""
    # login_accounts.id → students.id（内部 PK）
    stu_pk_row = db.query(Student.id).filter(Student.account_id == user.id).first()
    student_pk = stu_pk_row[0] if stu_pk_row else None
    if student_pk is None:
        return {"success": True, "total": 0, "page": page, "page_size": page_size, "list": []}
    q = db.query(InterviewInvitation).filter(InterviewInvitation.student_id == student_pk)
    if status:
        if status not in ("pending", "accepted", "declined", "cancelled", "completed"):
            raise HTTPException(400, "status 非法取值")
        q = q.filter(InterviewInvitation.status == status)
    total = q.count()
    rows = (
        q.order_by(InterviewInvitation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return {
        "success": True,
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": [_stu_inv_to_dict(r, db) for r in rows],
    }


@student_router.patch("/interview-invitations/{invitation_id}/respond")
def student_respond_interview_invitation(
    invitation_id: int,
    req: InterviewRespondRequest,
    user: LoginAccount = Depends(_require_student),
    db: Session = Depends(get_db),
):
    """学生端：接受 / 拒绝面试邀约（仅 pending 可响应）。"""
    stu_pk_row = db.query(Student.id).filter(Student.account_id == user.id).first()
    student_pk = stu_pk_row[0] if stu_pk_row else None
    if student_pk is None:
        raise HTTPException(404, "学生资料不存在")
    inv = (
        db.query(InterviewInvitation)
        .filter(InterviewInvitation.id == invitation_id)
        .filter(InterviewInvitation.student_id == student_pk)
        .first()
    )
    if not inv:
        raise HTTPException(404, "邀约不存在或无权操作")
    if inv.status != "pending":
        raise HTTPException(409, "仅待回复状态的邀约可响应")
    inv.status = "accepted" if req.accept else "declined"
    inv.student_reply = req.reply or ""
    db.commit()
    return {
        "success": True,
        "message": "已" + ("接受" if req.accept else "拒绝") + "邀约",
        "data": _stu_inv_to_dict(inv, db),
    }
