from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum("teacher", "student", "enterprise"), nullable=False, default="student")
    real_name = Column(String(50))
    user_number = Column(String(30), default="")
    created_at = Column(DateTime, server_default=func.now())
    email = Column(String(100), default="")
    avatar = Column(String(255), default="")



class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    requirements = Column(Text)
    criteria = Column(String(500), default="代码质量,功能完整性,文档规范性,界面设计")
    criteria_weights = Column(String(500), default="")
    status = Column(Enum("draft", "published"), default="published")
    created_by = Column(Integer, ForeignKey("users.id"))
    class_id = Column(String(500), ForeignKey("classes.id"), nullable=True)
    total_score = Column(Integer, default=100)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    creator = relationship("User", foreign_keys=[created_by])
    template_path = Column(String(255), default=None)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    student_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String(200))
    file_path = Column(String(500))
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    task = relationship("Task", foreign_keys=[task_id])
    student = relationship("User", foreign_keys=[student_id])
    class_id = Column(String(500), nullable=True)

class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"))
    evaluator_type = Column(Enum("ai", "teacher"), default="ai")
    total_score = Column(Float)
    dimension_scores = Column(JSON)
    comment = Column(Text)
    step_completeness = Column(JSON)  # 步骤完整性核查
    logic_issues = Column(JSON)  # 逻辑漏洞
    created_at = Column(DateTime, server_default=func.now())

    submission = relationship("Submission", foreign_keys=[submission_id])


class EvaluationCriteria(Base):
    __tablename__ = "evaluation_criteria"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id"))
    name = Column(String(100))
    weight = Column(Float, default=25.0)
    description = Column(Text)

    task = relationship("Task", foreign_keys=[task_id])