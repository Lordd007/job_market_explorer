# db/models.py
from __future__ import annotations

import uuid
import datetime as dt
from sqlalchemy import (
    Text, String, Boolean, Numeric, DateTime, ForeignKey,
    Integer, Float, LargeBinary, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ARRAY
from db.base import Base
from pgvector.sqlalchemy import Vector

class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(Text, nullable=False)

    city: Mapped[str | None] = mapped_column(Text, default="N/A", server_default="N/A")
    region: Mapped[str | None] = mapped_column(Text, default="N/A", server_default="N/A")
    country: Mapped[str | None] = mapped_column(Text, default="N/A", server_default="N/A")

    remote_flag: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    salary_min: Mapped[float] = mapped_column(Numeric, default=0.0, server_default="0")
    salary_max: Mapped[float] = mapped_column(Numeric, default=0.0, server_default="0")
    salary_currency: Mapped[str] = mapped_column(Text, default="USD", server_default="USD")
    salary_period: Mapped[str] = mapped_column(Text, default="yearly", server_default="yearly")

    posted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    source: Mapped[str] = mapped_column(Text, default="manual", server_default="manual")
    url: Mapped[str | None] = mapped_column(String, unique=True)

    description_text: Mapped[str] = mapped_column(Text, default="", server_default="")

    url_hash: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    desc_hash: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)

    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, server_default="now()")
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, server_default="now()")

    __table_args__ = (
        UniqueConstraint("url_hash", name="jobs_url_hash_uq"),
        Index("jobs_desc_hash_idx", "desc_hash"),
    )


class Skill(Base):
    __tablename__ = "skills"

    skill_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_canonical: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(Text, default=None)
    aliases_json: Mapped[str] = mapped_column(Text, default="[]")  # JSON text for now


class JobSkill(Base):
    __tablename__ = "job_skills"

    # keep UUID to match jobs.job_id
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.9)
    source: Mapped[str] = mapped_column(Text, default="dict_v1")


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_sub: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default="now()")

class Resume(Base):
    __tablename__ = "resumes"
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"))
    file_mime: Mapped[str | None] = mapped_column(Text)
    file_size: Mapped[int | None] = mapped_column(Integer)
    text_content: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default="now()")
    embedding: Mapped[list[float] | None] = mapped_column(Vector(384))
    parsed_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True))

class ResumeSkill(Base):
    __tablename__ = "resume_skills"
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.resume_id", ondelete="CASCADE"), primary_key=True)
    skill: Mapped[str] = mapped_column(Text, primary_key=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.9)

class UserPreferences(Base):
    __tablename__ = "user_preferences"
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    cities: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    remote_mode: Mapped[str] = mapped_column(Text, default="any")      # remote|hybrid|office|any
    target_skills: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    companies: Mapped[list[str]] = mapped_column(ARRAY(Text), default=list)
    seniority: Mapped[str] = mapped_column(Text, default="any")
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default="now()")



class ResumeParsed(Base):
    __tablename__ = "resume_parsed"
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.resume_id", ondelete="CASCADE"), primary_key=True)
    full_name: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(Text)
    phone: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text)
    region: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(Text)
    postal_code: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    years_experience: Mapped[float | None]

class ResumeLink(Base):
    __tablename__ = "resume_links"
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.resume_id", ondelete="CASCADE"), primary_key=True)
    kind: Mapped[str] = mapped_column(Text, primary_key=True)
    url: Mapped[str]  = mapped_column(Text, primary_key=True)

class ResumeExperience(Base):
    __tablename__ = "resume_experience"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.resume_id", ondelete="CASCADE"))
    title: Mapped[str | None] = mapped_column(Text)
    company: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    start_text: Mapped[str | None] = mapped_column(Text)
    end_text: Mapped[str | None] = mapped_column(Text)
    bullets_json: Mapped[str] = mapped_column(Text, default="[]")

class ResumeEducation(Base):
    __tablename__ = "resume_education"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("resumes.resume_id", ondelete="CASCADE"))
    degree: Mapped[str | None] = mapped_column(Text)
    school: Mapped[str | None] = mapped_column(Text)
    year: Mapped[str | None] = mapped_column(Text)