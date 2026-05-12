from datetime import datetime, timezone

def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)
import json
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy import TypeDecorator
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class JSONList(TypeDecorator):
    """Stores a list of strings as a JSON-encoded TEXT column.

    Works transparently on both SQLite (tests) and PostgreSQL (production).
    Using JSON-encoded text avoids the PostgreSQL-only ARRAY type, which
    aiosqlite cannot handle during test table creation.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return "[]"
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return []
        return json.loads(value)


class CVProfile(Base):
    __tablename__ = "cv_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_text: Mapped[str] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(JSONList)
    job_titles: Mapped[list[str]] = mapped_column(JSONList)
    keywords: Mapped[list[str]] = mapped_column(JSONList)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

class SavedJob(Base):
    __tablename__ = "saved_jobs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    company: Mapped[str] = mapped_column(String)
    location: Mapped[str] = mapped_column(String)
    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    url: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(Text)
    match_score: Mapped[int] = mapped_column(Integer, default=0)
    matched_skills: Mapped[list[str]] = mapped_column(JSONList, nullable=True, default=None)
    missing_skills: Mapped[list[str]] = mapped_column(JSONList, nullable=True, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    application: Mapped["Application | None"] = relationship(
        "Application", back_populates="job", uselist=False, cascade="all, delete-orphan"
    )

class CoverLetter(Base):
    __tablename__ = "cover_letters"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    external_id: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    job_title: Mapped[str] = mapped_column(String)
    company: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

class Application(Base):
    __tablename__ = "applications"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_id: Mapped[int] = mapped_column(Integer, ForeignKey("saved_jobs.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String, default="saved")
    applied_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)
    job: Mapped["SavedJob"] = relationship("SavedJob", back_populates="application")
