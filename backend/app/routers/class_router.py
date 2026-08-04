import random
import string
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from app.models.database import SessionLocal
from app.models.class_models import Class, ClassMember
from app.models.tables import LoginAccount, Teacher, Student
from app.models.class_models import Class, ClassMember  # noqa: F811 - 兼容已导入

router = APIRouter(prefix="/api/classes", tags=["班级管理"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))


def _account_to_teacher_id(db: Session, account_id: int) -> Optional[int]:
    if not account_id or account_id <= 0:
        return None
    t = db.query(Teacher).filter(Teacher.account_id == int(account_id)).first()
    return t.id if t else None


def _account_to_student_id(db: Session, account_id: int) -> Optional[int]:
    if not account_id or account_id <= 0:
        return None
    s = db.query(Student).filter(Student.account_id == int(account_id)).first()
    return s.id if s else None


def _resolve_teacher_name(db: Session, teacher_id: int) -> str:
    """teacher_id 约定优先取 teachers.id，找不到再按 login_accounts.id 回退。返回 real_name/username。"""
    if not teacher_id or teacher_id <= 0:
        return ""
    t = db.query(Teacher).filter(Teacher.id == int(teacher_id)).first()
    if t and t.real_name:
        return t.real_name or ""
    if t:
        acct = db.query(LoginAccount).filter(LoginAccount.id == t.account_id).first()
        if acct:
            return acct.username or ""
    # 回退：按 login_accounts.id 查
    acct = db.query(LoginAccount).filter(LoginAccount.id == int(teacher_id)).first()
    if acct:
        return acct.username or ""
    return ""


def _resolve_student_basic(db: Session, student_id: int):
    """student_id 约定优先 students.id，找不到回退 login_accounts.id。
    返回 (account_id_or_0, real_name, student_number/teacher_no)"""
    if not student_id or student_id <= 0:
        return 0, "", ""
    s = db.query(Student).filter(Student.id == int(student_id)).first()
    if s:
        name = s.real_name or ""
        if not name:
            acct = db.query(LoginAccount).filter(LoginAccount.id == s.account_id).first()
            if acct:
                name = acct.username or ""
        return s.account_id or 0, name, s.student_no or ""
    # 回退：按 login_accounts.id 查
    acct = db.query(LoginAccount).filter(LoginAccount.id == int(student_id)).first()
    if not acct:
        return 0, "", ""
    if acct.role == "student":
        s = db.query(Student).filter(Student.account_id == acct.id).first()
        if s:
            name = s.real_name or acct.username or ""
            return acct.id, name, s.student_no or ""
    return acct.id, acct.username or "", ""


class ClassCreate(BaseModel):
    name: str
    grade: str = ""
    major: str = ""
    semester: str = ""
    course_name: str = ""
    description: str = ""
    teacher_id: int = 0   # 前端约定传 login_accounts.id
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
    student_id: int   # 前端约定传 login_accounts.id
    student_name: str = ""
    student_number: str = ""


# 教师创建班级
@router.post("/")
def create_class(req: ClassCreate, db: Session = Depends(get_db)):
    code = generate_code()
    while db.query(Class).filter(Class.invite_code == code).first():
        code = generate_code()

    # teacher_id (login_accounts.id) -> teachers.id
    teacher_pk = _account_to_teacher_id(db, req.teacher_id) if req.teacher_id else None
    resolved_teacher_id = teacher_pk if teacher_pk else (req.teacher_id if req.teacher_id else None)

    teacher_name = req.teacher_name or ""
    if not teacher_name and resolved_teacher_id:
        teacher_name = _resolve_teacher_name(db, resolved_teacher_id)

    c = Class(
        name=req.name, grade=req.grade, major=req.major,
        semester=req.semester, course_name=req.course_name,
        description=req.description, teacher_id=resolved_teacher_id,
        teacher_name=teacher_name, invite_code=code
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"success": True, "data": {"id": c.id, "invite_code": c.invite_code}}


# 教师查看自己创建的班级
@router.get("/")
def get_my_classes(teacher_id: int = 0, db: Session = Depends(get_db)):
    if teacher_id:
        # 兼容两种：login_accounts.id（走映射）和 teachers.id（直接查）
        teacher_pk = _account_to_teacher_id(db, teacher_id)
        if teacher_pk:
            classes = db.query(Class).filter(Class.teacher_id == teacher_pk).all()
        else:
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
    # student_id 约定 login_accounts.id -> students.id
    stu_pk = _account_to_student_id(db, student_id) if student_id else None
    fk = stu_pk if stu_pk else student_id
    memberships = db.query(ClassMember).filter(ClassMember.student_id == fk).all() if fk else []
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

    # student_id (login_accounts.id) -> students.id
    stu_pk = _account_to_student_id(db, req.student_id) if req.student_id else None
    fk = stu_pk if stu_pk else req.student_id

    exist = db.query(ClassMember).filter(
        ClassMember.class_id == c.id,
        ClassMember.student_id == fk
    ).first() if fk else None
    if exist:
        raise HTTPException(400, "你已加入该班级")

    # 学生姓名/学号：入参填了就信任入参；没填就查学生表补
    name = req.student_name or ""
    number = req.student_number or ""
    if (not name or not number) and fk:
        _, res_name, res_no = _resolve_student_basic(db, fk)
        if not name:
            name = res_name
        if not number:
            number = res_no

    member = ClassMember(
        class_id=c.id, student_id=fk,
        student_name=name, student_number=number
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
    students = []
    for m in members:
        account_id, rname, rno = _resolve_student_basic(db, m.student_id)
        name = m.student_name or rname
        no = m.student_number or rno
        students.append({
            "id": m.id,
            "student_id": account_id if account_id else m.student_id,
            "student_pk": m.student_id,
            "student_name": name,
            "student_number": no,
            "joined_at": str(m.joined_at),
        })

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
