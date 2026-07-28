import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.models.database import SessionLocal
from app.models.tables import User, Submission, Evaluation
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


class ProfileUpdate(BaseModel):
    real_name: Optional[str] = None
    email: Optional[str] = None
    user_number: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


@router.get("/profile/{user_id}")
def get_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    return {
        "success": True,
        "data": {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name or "",
            "email": user.email or "",
            "role": user.role,
            "avatar": getattr(user, 'avatar', ''),
            "user_number": user.user_number or "",
            "created_at": str(user.created_at) if user.created_at else ""
        }
    }


@router.put("/profile/{user_id}")
def update_profile(user_id: int, req: ProfileUpdate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if req.real_name is not None:
        user.real_name = req.real_name
    if req.email is not None:
        user.email = req.email
    if req.user_number is not None:
        user.user_number = req.user_number
    db.commit()
    return {"success": True, "message": "资料已更新"}


@router.put("/password/{user_id}")
def change_password(user_id: int, req: PasswordChange, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")
    if not verify_password(req.old_password, user.password_hash):
        raise HTTPException(400, "旧密码不正确")
    user.password_hash = hash_password(req.new_password)
    db.commit()
    return {"success": True, "message": "密码已修改"}


@router.post("/avatar/{user_id}")
async def upload_avatar(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in {'.png', '.jpg', '.jpeg', '.gif'}:
        raise HTTPException(400, "仅支持 png/jpg/gif 格式")

    filename = f"avatar_{user_id}_{uuid.uuid4().hex[:8]}{ext}"
    save_path = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    if not hasattr(user, 'avatar'):
        setattr(user, 'avatar', filename)
    else:
        user.avatar = filename
    db.commit()

    return {"success": True, "avatar": filename}


@router.delete("/account/{user_id}")
def delete_account(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(404, "用户不存在")

    from app.models.class_models import ClassMember, Class
    db.query(ClassMember).filter(ClassMember.student_id == user_id).delete()

    submissions = db.query(Submission).filter(Submission.student_id == user_id).all()
    for sub in submissions:
        db.query(Evaluation).filter(Evaluation.submission_id == sub.id).delete()
        db.delete(sub)

    if user.role == "teacher":
        classes = db.query(Class).filter(Class.teacher_id == user_id).all()
        for c in classes:
            db.query(ClassMember).filter(ClassMember.class_id == c.id).delete()
            db.delete(c)

    from app.models.task_template import TaskTemplate
    db.query(TaskTemplate).filter(TaskTemplate.created_by == user_id).delete()

    db.delete(user)
    db.commit()
    return {"success": True, "message": "账号已注销"}