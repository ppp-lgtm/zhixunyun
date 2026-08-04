from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Float, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.database import Base


class Enterprise(Base):
    __tablename__ = "enterprises"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False, unique=True)
    short_name = Column(String(50), default="")
    logo = Column(String(500), default="")
    industry = Column(String(100), default="")
    scale = Column(String(50), default="")
    contact_person = Column(String(50), default="")
    contact_phone = Column(String(30), default="")
    contact_email = Column(String(100), default="")
    address = Column(String(500), default="")
    description = Column(Text, default="")
    status = Column(Enum("active", "inactive"), default="active")
    created_at = Column(DateTime, server_default=func.now())
    extra = Column(JSON, nullable=True)


class EnterpriseMentor(Base):
    __tablename__ = "enterprise_mentors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    # user_id → account_id 指向 login_accounts.id
    account_id = Column(Integer, ForeignKey("login_accounts.id", ondelete="CASCADE"), nullable=False)
    # 兼容旧列 user_id（与 account_id 同值，便于老代码过渡）
    user_id = Column(Integer, nullable=True)
    real_name = Column(String(50), default="")
    title = Column(String(100), default="")
    department = Column(String(100), default="")
    is_admin = Column(Integer, default=0)
    status = Column(Enum("active", "inactive"), default="active")
    joined_at = Column(DateTime, server_default=func.now())
    extra = Column(JSON, nullable=True)

    enterprise = relationship("Enterprise", foreign_keys=[enterprise_id])
    account = relationship("LoginAccount", foreign_keys=[account_id])
    __table_args__ = (
        UniqueConstraint("account_id", "enterprise_id", name="uk_em_account_enterprise"),
    )


class JobPosition(Base):
    __tablename__ = "job_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    job_type = Column(String(50), default="技术岗")
    level = Column(String(50), default="初级")
    salary_range = Column(String(100), default="")
    city = Column(String(100), default="")
    description = Column(Text, default="")
    requirements = Column(Text, default="")
    responsibilities = Column(Text, default="")
    skill_requirements = Column(JSON, default=list)
    tags = Column(String(500), default="")
    # 兼容旧列（逻辑改为优先走 job_class_ref 关联表）
    linked_classes = Column(String(500), default="")
    class_id = Column(Integer, nullable=True)
    # created_by 改指向 enterprise_mentors.id
    created_by = Column(Integer, ForeignKey("enterprise_mentors.id", ondelete="SET NULL"), nullable=True)
    status = Column(Enum("draft", "open", "closed"), default="open")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    ai_generated = Column(Integer, default=0)
    ai_prompt_snapshot = Column(Text, default="")

    enterprise = relationship("Enterprise", foreign_keys=[enterprise_id])
    creator = relationship("EnterpriseMentor", foreign_keys=[created_by])


# ==============================================================
# 岗位 ↔ 班级 关联表（替代 job_positions.linked_classes + class_id）
# ==============================================================
class JobClassRef(Base):
    __tablename__ = "job_class_ref"
    job_id = Column(Integer, ForeignKey("job_positions.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True, nullable=False)


class EnterpriseEvaluation(Base):
    __tablename__ = "enterprise_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    # mentor_id 改指向 enterprise_mentors.id
    mentor_id = Column(Integer, ForeignKey("enterprise_mentors.id", ondelete="CASCADE"), nullable=False)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)

    total_score = Column(Float, default=0)
    dimension_scores = Column(JSON, default=dict)

    job_fit_score = Column(Float, default=0)
    strength_points = Column(Text, default="")
    improvement_points = Column(Text, default="")
    interview_suggest = Column(
        Enum("recommend", "maybe", "not_recommend"),
        default="maybe"
    )
    comment = Column(Text, default="")

    matched_job_id = Column(Integer, ForeignKey("job_positions.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    submission = relationship("Submission", foreign_keys=[submission_id])
    mentor = relationship("EnterpriseMentor", foreign_keys=[mentor_id])
    enterprise = relationship("Enterprise", foreign_keys=[enterprise_id])
    matched_job = relationship("JobPosition", foreign_keys=[matched_job_id])
    __table_args__ = (
        UniqueConstraint("submission_id", "enterprise_id", name="uk_ee_sub_enterprise"),
    )


class InterviewInvitation(Base):
    """面试邀约表：企业导师向学生发起的面试邀请。"""
    __tablename__ = "interview_invitations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False, index=True)
    mentor_id = Column(Integer, ForeignKey("enterprise_mentors.id", ondelete="CASCADE"), nullable=False, index=True)
    # 学生侧外键：用 students.id（内部 PK）
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    # 关联岗位（必选）
    job_id = Column(Integer, ForeignKey("job_positions.id", ondelete="SET NULL"), nullable=True)
    # 面试时间（必选）
    interview_time = Column(DateTime, nullable=False)
    # 面试形式：online 线上 / onsite 线下
    interview_type = Column(Enum("online", "onsite"), default="online", nullable=False)
    # 会议链接 / 地点（必选）
    location = Column(String(500), nullable=False, default="")
    # 邀约留言（可选）
    message = Column(Text, default="")
    # 状态：待回复 / 已接受 / 已拒绝 / 企业已撤回 / 已完成
    status = Column(
        Enum("pending", "accepted", "declined", "cancelled", "completed"),
        default="pending",
        nullable=False,
        index=True,
    )
    # 学生回复留言（可选）
    student_reply = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    enterprise = relationship("Enterprise", foreign_keys=[enterprise_id])
    mentor = relationship("EnterpriseMentor", foreign_keys=[mentor_id])
    job = relationship("JobPosition", foreign_keys=[job_id])
