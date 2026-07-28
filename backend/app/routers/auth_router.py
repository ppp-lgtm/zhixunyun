from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.database import SessionLocal
from app.models.tables import User
from app.utils.auth import hash_password, verify_password, create_token

router = APIRouter(prefix="/api/auth", tags=["用户认证"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "student"
    real_name: str = ""
    user_number: str = ""


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    exist = db.query(User).filter(User.username == req.username).first()
    if exist:
        raise HTTPException(400, "用户名已存在")

    user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        role=req.role if req.role in ("teacher", "student", "enterprise") else "student",
        real_name=req.real_name,
        user_number=req.user_number
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"success": True, "message": "注册成功", "user_id": user.id}


@router.post("/login")
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")

    token = create_token(user.id, user.role)
    return {
        "success": True,
        "token": token,
        "user": {"id": user.id, "username": user.username, "role": user.role, "real_name": user.real_name}
    }