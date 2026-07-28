import random
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.models.database import SessionLocal
from app.models.class_models import Class, ClassMember
from app.models.tables import User

router = APIRouter(prefix="/api/classes", tags=["班级管理"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


class ClassCreate(BaseModel):
    name: str
    grade: str = ""
    major: str = ""
    semester: str = ""
    course_name: str = ""
    description: str = ""
    teacher_id: int = 0
    teacher_name: str = ""


class ClassUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None
    semester: Optional[str] = None
    course_name: Optional[str] = None
    description: Optional[str] = None


class JoinRequest(BaseModel):
    invite_code: str
    student_id: int
    student_name: str = ""
    student_number: str = ""


# 教师创建班级
@router.post("/")
def create_class(req: ClassCreate, db: Session = Depends(get_db)):
    code = generate_code()
    # 确保邀请码唯一
    while db.query(Class).filter(Class.invite_code == code).first():
        code = generate_code()

    c = Class(
        name=req.name, grade=req.grade, major=req.major,
        semester=req.semester, course_name=req.course_name,
        description=req.description, teacher_id=req.teacher_id,
        teacher_name=req.teacher_name, invite_code=code
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"success": True, "data": {"id": c.id, "invite_code": c.invite_code}}


# 教师查看自己创建的班级
@router.get("/")
def get_my_classes(teacher_id: int = 0, db: Session = Depends(get_db)):
    if teacher_id:
        classes = db.query(Class).filter(Class.teacher_id == teacher_id).all()
    else:
        classes = db.query(Class).all()
    return {
        "success": True,
        "data": [
            {"id": c.id, "name": c.name, "grade": c.grade, "major": c.major,
             "semester": c.semester, "course_name": c.course_name,
             "description": c.description, "teacher_name": c.teacher_name,
             "invite_code": c.invite_code, "student_count": c.student_count,
             "status": c.status, "created_at": str(c.created_at)}
            for c in classes
        ]
    }


# 学生查看已加入的班级
@router.get("/my")
def get_my_enrolled(student_id: int = 0, db: Session = Depends(get_db)):
    memberships = db.query(ClassMember).filter(ClassMember.student_id == student_id).all()
    class_ids = [m.class_id for m in memberships]
    classes = db.query(Class).filter(Class.id.in_(class_ids)).all() if class_ids else []
    return {
        "success": True,
        "data": [
            {"id": c.id, "name": c.name, "grade": c.grade, "major": c.major,
             "semester": c.semester, "course_name": c.course_name,
             "teacher_name": c.teacher_name, "student_count": c.student_count}
            for c in classes
        ]
    }


# 学生加入班级
@router.post("/join")
def join_class(req: JoinRequest, db: Session = Depends(get_db)):
    c = db.query(Class).filter(Class.invite_code == req.invite_code.strip().upper()).first()
    if not c:
        raise HTTPException(404, "班级不存在或邀请码错误")

    exist = db.query(ClassMember).filter(
        ClassMember.class_id == c.id,
        ClassMember.student_id == req.student_id
    ).first()
    if exist:
        raise HTTPException(400, "你已加入该班级")

    member = ClassMember(
        class_id=c.id, student_id=req.student_id,
        student_name=req.student_name, student_number=req.student_number
    )
    db.add(member)
    c.student_count += 1
    db.commit()
    return {"success": True, "data": {"class_name": c.name}}


# 班级详情
@router.get("/{class_id}/detail")
def class_detail(class_id: int, db: Session = Depends(get_db)):
    c = db.query(Class).filter(Class.id == class_id).first()
    if not c:
        raise HTTPException(404, "班级不存在")

    members = db.query(ClassMember).filter(ClassMember.class_id == class_id).all()
    students = [
        {"id": m.id, "student_id": m.student_id, "student_name": m.student_name,
         "student_number": m.student_number, "joined_at": str(m.joined_at)}
        for m in members
    ]

    return {
        "success": True,
        "data": {
            "id": c.id, "name": c.name, "grade": c.grade, "major": c.major,
            "semester": c.semester, "course_name": c.course_name,
            "description": c.description, "teacher_name": c.teacher_name,
            "invite_code": c.invite_code, "student_count": c.student_count,
            "status": c.status, "students": students
        }
    }


# 编辑班级
@router.put("/{class_id}")
def update_class(class_id: int, req: ClassUpdate, db: Session = Depends(get_db)):
    c = db.query(Class).filter(Class.id == class_id).first()
    if not c:
        raise HTTPException(404, "班级不存在")
    if req.name is not None: c.name = req.name
    if req.grade is not None: c.grade = req.grade
    if req.major is not None: c.major = req.major
    if req.semester is not None: c.semester = req.semester
    if req.course_name is not None: c.course_name = req.course_name
    if req.description is not None: c.description = req.description
    db.commit()
    return {"success": True, "message": "班级信息已更新"}


# 解散班级
@router.delete("/{class_id}")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    c = db.query(Class).filter(Class.id == class_id).first()
    if not c:
        raise HTTPException(404, "班级不存在")
    db.query(ClassMember).filter(ClassMember.class_id == class_id).delete()
    db.delete(c)
    db.commit()
    return {"success": True, "message": "班级已解散"}


# 移除学生
@router.delete("/{class_id}/students/{member_id}")
def remove_student(class_id: int, member_id: int, db: Session = Depends(get_db)):
    member = db.query(ClassMember).filter(
        ClassMember.id == member_id,
        ClassMember.class_id == class_id
    ).first()
    if not member:
        raise HTTPException(404, "学生不存在")
    c = db.query(Class).filter(Class.id == class_id).first()
    if c:
        c.student_count = max(0, c.student_count - 1)
    db.delete(member)
    db.commit()
    return {"success": True, "message": "已移除学生"}