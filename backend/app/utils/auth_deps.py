"""
共享的 FastAPI 认证依赖函数。
所有 router 统一从此模块导入，避免每个 router 重复定义相同的 token 提取/校验逻辑。
"""
from typing import Optional
from fastapi import Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session

from app.models.database import SessionLocal
from app.models.tables import LoginAccount, Teacher, Student
from app.models.enterprise_models import EnterpriseMentor
from app.utils.auth import decode_token


def get_db():
    """获取数据库会话（FastAPI 依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _extract_token(
    token_query: Optional[str] = Query(None, alias="token", description="登录 token（URL 查询参数）"),
    authorization: Optional[str] = Header(None, description="Authorization: Bearer <token>"),
) -> Optional[str]:
    """从 URL 查询参数或 Authorization 头中提取 JWT token。"""
    if token_query:
        return token_query
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(None, 1)[1].strip()
    if authorization:
        return authorization.strip()
    return None


def _get_token_role(token: Optional[str]) -> Optional[str]:
    """从 token 中提取 role 字段（不解码数据库）。"""
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    return payload.get("role")


def get_current_user(
    token: Optional[str] = Depends(_extract_token),
    db: Session = Depends(get_db),
) -> LoginAccount:
    """验证 token 并返回当前登录用户。未登录返回 401。"""
    if not token:
        raise HTTPException(401, "缺少登录凭据，请先登录")
    payload = decode_token(token)
    if not payload or not payload.get("user_id"):
        raise HTTPException(401, "登录已过期，请重新登录")
    user = db.query(LoginAccount).filter(LoginAccount.id == int(payload["user_id"])).first()
    if not user:
        raise HTTPException(401, "用户不存在")
    return user


def require_teacher(
    user: LoginAccount = Depends(get_current_user),
    token: Optional[str] = Depends(_extract_token),
) -> LoginAccount:
    """要求当前用户为教师角色，否则返回 403。"""
    token_role = _get_token_role(token)
    if user.role == "teacher" or token_role == "teacher":
        return user
    raise HTTPException(403, "仅教师可访问此接口")


def require_enterprise(
    user: LoginAccount = Depends(get_current_user),
    token: Optional[str] = Depends(_extract_token),
) -> LoginAccount:
    """要求当前用户为企业导师角色，否则返回 403。"""
    token_role = _get_token_role(token)
    if user.role == "mentor" or token_role == "enterprise":
        return user
    raise HTTPException(403, "仅企业导师可访问此接口")


def get_teacher_id(user: LoginAccount, db: Session) -> Optional[int]:
    """从 LoginAccount 获取 teachers.id（教师 PK）。"""
    if not user or user.role != "teacher":
        return None
    t = db.query(Teacher).filter(Teacher.account_id == user.id).first()
    return t.id if t else None


def get_student_pk(user: LoginAccount, db: Session) -> Optional[int]:
    """从 LoginAccount 获取 students.id（学生 PK）。"""
    if not user or user.role != "student":
        return None
    s = db.query(Student).filter(Student.account_id == user.id).first()
    return s.id if s else None


def get_mentor_enterprise_id(user: LoginAccount, db: Session) -> Optional[int]:
    """从 LoginAccount 获取 mentor 所属的 enterprise_id。"""
    if not user or user.role != "mentor":
        return None
    mentor = (
        db.query(EnterpriseMentor)
        .filter(EnterpriseMentor.account_id == user.id)
        .filter(EnterpriseMentor.status == "active")
        .first()
    )
    return mentor.enterprise_id if mentor else None


def _account_to_student_id(db: Session, account_id: int) -> Optional[int]:
    """login_accounts.id → students.id"""
    if not account_id:
        return None
    row = db.query(Student).filter(Student.account_id == int(account_id)).first()
    return row.id if row else None


def _account_to_teacher_id(db: Session, account_id: int) -> Optional[int]:
    """login_accounts.id → teachers.id"""
    if not account_id:
        return None
    row = db.query(Teacher).filter(Teacher.account_id == int(account_id)).first()
    return row.id if row else None
