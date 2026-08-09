from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    grade = Column(String(20), default="")
    major = Column(String(100), default="")
    semester = Column(String(20), default="")
    course_name = Column(String(100), default="")
    description = Column(Text, default="")
    # teacher_id 改指向 teachers.id（不再是 users.id）
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    teacher_name = Column(String(50), default="")
    enterprise_id = Column(Integer, ForeignKey("enterprises.id", ondelete="SET NULL"), nullable=True)
    invite_code = Column(String(10), unique=True, nullable=False)
    student_count = Column(Integer, default=0)
    status = Column(Enum("active", "archived"), default="active")
    created_at = Column(DateTime, server_default=func.now())
    # MySQL JSON 不接受空串；默认 NULL
    extra = Column(JSON, nullable=True, default=None)

    enterprise = relationship("Enterprise", foreign_keys=[enterprise_id])
    teacher = relationship("Teacher", foreign_keys=[teacher_id])


class ClassMember(Base):
    __tablename__ = "class_members"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    # student_id 改指向 students.id（不再是 users.id）
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    student_name = Column(String(50), default="")
    student_number = Column(String(30), default="")
    joined_at = Column(DateTime, server_default=func.now())

    klass = relationship("Class", foreign_keys=[class_id])
    student = relationship("Student", foreign_keys=[student_id])
