from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel
from app.models.database import SessionLocal
from app.models.tables import LoginAccount, Teacher, Student
from app.utils.auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _role_internal_to_external(r: str) -> str:
    """DB 内部存的是 mentor / teacher / student；前端对外统一 enterprise / teacher / student"""
    if r == "mentor":
        return "enterprise"
    return r or "student"


def _role_external_to_internal(r: str) -> str:
    if r == "enterprise":
        return "mentor"
    if r in ("teacher", "student", "mentor"):
        return r
    return "student"


class RegisterRequest(BaseModel):
    model_config = {"extra": "ignore"}
    username: str
    password: str
    role: str = "student"
    real_name: str = ""
    user_number: str = ""


class LoginRequest(BaseModel):
    model_config = {"extra": "ignore"}
    username: str
    password: str
    expected_role: Optional[str] = None


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    exist = db.query(LoginAccount).filter(LoginAccount.username == req.username).first()
    if exist:
        raise HTTPException(400, "用户名已存在")

    internal_role = _role_external_to_internal(req.role)

    acct = LoginAccount(
        username=req.username,
        password_hash=hash_password(req.password),
        role=internal_role,
    )
    db.add(acct)
    db.flush()

    # 同时写入角色表
    # 注意：学号/工号若为空串，统一写 NULL（UNIQUE 约束下多人未分配时不冲突）
    _empty_to_none = lambda v: None if (v is None or (isinstance(v, str) and v.strip() == "")) else v

    if internal_role == "teacher":
        t = Teacher(
            account_id=acct.id,
            real_name=req.real_name,
            teacher_no=_empty_to_none(req.user_number),
        )
        db.add(t)
        db.flush()
        role_id = t.id
    elif internal_role == "student":
        s = Student(
            account_id=acct.id,
            real_name=req.real_name,
            student_no=_empty_to_none(req.user_number),
        )
        db.add(s)
        db.flush()
        role_id = s.id
    else:
        # mentor（企业）身份注册单独走 /api/enterprise/register，有完整企业信息；
        # 这里如果直接走通用注册的话，只建 login_account，不建 enterprise_mentors，
        # 避免凭空挂企业。返回 acct.id 给前端。
        role_id = acct.id

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(500, f"注册失败：{str(e)}")

    return {
        "success": True,
        "message": "注册成功",
        "user_id": acct.id,
        "role_id": role_id,
        "role": _role_internal_to_external(internal_role),
    }


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    acct = db.query(LoginAccount).filter(LoginAccount.username == req.username).first()
    if not acct or not verify_password(req.password, acct.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    if acct.status != "active":
        raise HTTPException(401, "用户名或密码错误")

    ext_role = _role_internal_to_external(acct.role)
    if req.expected_role and req.expected_role in ("student", "teacher", "enterprise"):
        if ext_role != req.expected_role:
            raise HTTPException(401, "用户名或密码错误")

    # 从角色表取 real_name / user_number
    real_name = ""
    user_number = ""
    if acct.role == "teacher":
        t = db.query(Teacher).filter(Teacher.account_id == acct.id).first()
        if t:
            real_name = t.real_name or ""
            user_number = t.teacher_no or ""
    elif acct.role == "student":
        s = db.query(Student).filter(Student.account_id == acct.id).first()
        if s:
            real_name = s.real_name or ""
            user_number = s.student_no or ""
    # mentor 的 real_name 从 enterprise_mentors 取（但可能有多家，登录接口先取第一条）
    elif acct.role == "mentor":
        try:
            from app.models.enterprise_models import EnterpriseMentor
            em = db.query(EnterpriseMentor).filter(EnterpriseMentor.account_id == acct.id).first()
            if em:
                real_name = em.real_name or ""
        except Exception:
            pass

    token = create_token(acct.id, ext_role)
    return {
        "success": True,
        "token": token,
        "user": {
            "id": acct.id,
            "username": acct.username,
            "role": ext_role,
            "real_name": real_name,
            "user_number": user_number,
            "email": acct.email or "",
            "phone": acct.phone or "",
            "avatar": acct.avatar or "",
        }
    }
