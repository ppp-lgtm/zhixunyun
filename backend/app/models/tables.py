from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Float, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base


# ==============================================================
# 登录凭据（三角色共享）
# ==============================================================
class LoginAccount(Base):
    __tablename__ = "login_accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    # 注意：SQL 里是 mentor，这里也用 mentor 保持与数据库一致；
    # 对外 token/role 仍然兼容返回 "enterprise"（auth 层做映射）
    role = Column(Enum("teacher", "student", "mentor"), nullable=False, default="student")
    email = Column(String(100), default="")
    phone = Column(String(30), default="")
    avatar = Column(String(255), default="")
    status = Column(Enum("active", "disabled"), default="active")
    extra = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


# ==============================================================
# 教师身份
# ==============================================================
class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("login_accounts.id", ondelete="CASCADE"), nullable=False, unique=True)
    real_name = Column(String(50), default="")
    teacher_no = Column(String(30), nullable=True, default=None)
    title = Column(String(100), default="")
    department = Column(String(100), default="")
    status = Column(Enum("active", "inactive"), default="active")
    joined_at = Column(DateTime, server_default=func.now())
    extra = Column(JSON, nullable=True)

    account = relationship("LoginAccount", foreign_keys=[account_id])


# ==============================================================
# 学生身份
# ==============================================================
class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("login_accounts.id", ondelete="CASCADE"), nullable=False, unique=True)
    real_name = Column(String(50), default="")
    student_no = Column(String(30), nullable=True, default=None)
    grade = Column(String(20), default="")
    major = Column(String(100), default="")
    class_name = Column(String(100), default="")
    enrollment_year = Column(Integer, nullable=True)
    status = Column(Enum("active", "graduated", "dropped"), default="active")
    joined_at = Column(DateTime, server_default=func.now())
    extra = Column(JSON, nullable=True)

    account = relationship("LoginAccount", foreign_keys=[account_id])


# ==============================================================
# 实训任务
# ==============================================================
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    requirements = Column(Text)
    criteria = Column(String(500), default="代码质量,功能完整性,文档规范性,界面设计")
    criteria_weights = Column(String(500), default="")
    status = Column(Enum("draft", "published"), default="published")
    # created_by 现在指向 teachers.id（不再是 users.id）
    created_by = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    # 兼容旧字段（upgrade 后仍存在，新版逻辑优先走 task_class_ref）
    class_id = Column(String(500), nullable=True)
    total_score = Column(Integer, default=100)
    deadline = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    template_path = Column(String(255), default=None)
    steps = Column(JSON, nullable=True)
    extra = Column(JSON, nullable=True)
    origin = Column(String(30), default="teacher_manual")
    linked_job_id = Column(Integer, ForeignKey("job_positions.id", ondelete="SET NULL"), nullable=True)
    is_enterprise_project = Column(Integer, default=0)
    ai_generated_job_title = Column(String(200), default="")

    creator = relationship("Teacher", foreign_keys=[created_by])
    # 任务 ↔ 班级 多对多（通过 task_class_ref）
    class_refs = relationship("TaskClassRef", cascade="all, delete-orphan")


# ==============================================================
# 任务 ↔ 班级 关联表（替代 tasks.class_id 逗号列）
# ==============================================================
class TaskClassRef(Base):
    __tablename__ = "task_class_ref"
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True, nullable=False)


# ==============================================================
# 学生提交
# ==============================================================
class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    # student_id 现在指向 students.id
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"))
    filename = Column(String(200))
    file_path = Column(String(500))
    content = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    step_evidences = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)
    # 兼容旧字段
    class_id = Column(String(500), nullable=True)

    task = relationship("Task", foreign_keys=[task_id])
    student = relationship("Student", foreign_keys=[student_id])
    __table_args__ = (
        UniqueConstraint("task_id", "student_id", name="uk_sub_task_student"),
    )


# ==============================================================
# AI / 教师评价
# ==============================================================
class Evaluation(Base):
    __tablename__ = "evaluations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"))
    evaluator_type = Column(Enum("ai", "teacher"), default="ai")
    # evaluator_type=teacher 时为 teachers.id
    evaluator_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)
    total_score = Column(Float)
    dimension_scores = Column(JSON)
    comment = Column(Text)
    step_completeness = Column(JSON)
    logic_issues = Column(JSON)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    submission = relationship("Submission", foreign_keys=[submission_id])
    evaluator = relationship("Teacher", foreign_keys=[evaluator_id])
    __table_args__ = (
        UniqueConstraint("submission_id", "evaluator_type", name="uk_eval_sub_type"),
    )


# ==============================================================
# 评价维度库
# ==============================================================
class EvaluationCriteria(Base):
    __tablename__ = "evaluation_criteria"
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"))
    name = Column(String(100))
    weight = Column(Float, default=25.0)
    description = Column(Text)

    task = relationship("Task", foreign_keys=[task_id])


# ==============================================================
# 兼容旧别名 User → LoginAccount + 角色表
# （对只做简单查询的旧代码做最小侵入兼容；复杂逻辑请直接用新模型）
# ==============================================================
try:
    User = LoginAccount
except Exception:
    pass
