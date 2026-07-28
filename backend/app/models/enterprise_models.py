from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, Float, JSON, ForeignKey
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


class EnterpriseMentor(Base):
    __tablename__ = "enterprise_mentors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    real_name = Column(String(50), default="")
    title = Column(String(100), default="")
    department = Column(String(100), default="")
    is_admin = Column(Integer, default=0)
    status = Column(Enum("active", "inactive"), default="active")
    joined_at = Column(DateTime, server_default=func.now())

    enterprise = relationship("Enterprise", foreign_keys=[enterprise_id])
    user = relationship("User", foreign_keys=[user_id])


class JobPosition(Base):
    __tablename__ = "job_positions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False)
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
    linked_classes = Column(String(500), default="")
    created_by = Column(Integer, ForeignKey("users.id"))
    status = Column(Enum("draft", "open", "closed"), default="open")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    enterprise = relationship("Enterprise", foreign_keys=[enterprise_id])
    creator = relationship("User", foreign_keys=[created_by])


class EnterpriseEvaluation(Base):
    __tablename__ = "enterprise_evaluations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    mentor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"), nullable=False)

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

    matched_job_id = Column(Integer, ForeignKey("job_positions.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    submission = relationship("Submission", foreign_keys=[submission_id])
    mentor = relationship("User", foreign_keys=[mentor_id])
    enterprise = relationship("Enterprise", foreign_keys=[enterprise_id])
    matched_job = relationship("JobPosition", foreign_keys=[matched_job_id])
