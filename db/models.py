# db/models.py
import uuid, datetime as dt
from sqlalchemy import (Text, String, Boolean, Numeric, DateTime, TIMESTAMP)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from db.base import Base

class Job(Base):
    __tablename__ = "jobs"
    job_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str | None]
    region: Mapped[str | None]
    country: Mapped[str | None]
    remote_flag: Mapped[bool | None]
    salary_min: Mapped[float | None]
    salary_max: Mapped[float | None]
    salary_currency: Mapped[str | None]
    salary_period: Mapped[str | None]
    posted_at: Mapped[dt.datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    source: Mapped[str | None]
    url: Mapped[str | None] = mapped_column(String, unique=True)
    description_text: Mapped[str | None]
    desc_hash: Mapped[str | None]
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
