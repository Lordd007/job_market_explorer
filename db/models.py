# db/models.py
from __future__ import annotations

import uuid
import datetime as dt
from sqlalchemy import Text, String, Boolean, Numeric, DateTime, ForeignKey, Integer, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base


class Job(Base):
    __tablename__ = "jobs"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Required fields
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(Text, nullable=False)

    # Location defaults
    city: Mapped[str | None] = mapped_column(Text, default="N/A", server_default="N/A")
    region: Mapped[str | None] = mapped_column(Text, default="N/A", server_default="N/A")
    country: Mapped[str | None] = mapped_column(Text, default="N/A", server_default="N/A")

    # Remote flag
    remote_flag: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    # Salary info
    salary_min: Mapped[float] = mapped_column(Numeric, default=0.0, server_default="0")
    salary_max: Mapped[float] = mapped_column(Numeric, default=0.0, server_default="0")
    salary_currency: Mapped[str] = mapped_column(Text, default="USD", server_default="USD")
    salary_period: Mapped[str] = mapped_column(Text, default="yearly", server_default="yearly")

    # Dates
    posted_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), default=None)

    # Source + URLs
    source: Mapped[str] = mapped_column(Text, default="manual", server_default="manual")
    url: Mapped[str | None] = mapped_column(String, unique=True)

    # Text fields
    description_text: Mapped[str] = mapped_column(Text, default="", server_default="")
    desc_hash: Mapped[str] = mapped_column(Text, default="", server_default="")

    # Audit fields
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, server_default="now()")
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, server_default="now()")


class Skill(Base):
    __tablename__ = "skills"

    skill_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name_canonical: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    category: Mapped[str | None] = mapped_column(Text, default=None)
    aliases_json: Mapped[str] = mapped_column(Text, default="[]")  # JSON text for now


class JobSkill(Base):
    __tablename__ = "job_skills"

    # NOTE: keep this a UUID to match jobs.job_id (no text/str)
    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("jobs.job_id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.skill_id", ondelete="CASCADE"), primary_key=True
    )
    confidence: Mapped[float] = mapped_column(Float, default=0.9)
    source: Mapped[str] = mapped_column(Text, default="dict_v1")
