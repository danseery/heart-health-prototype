from datetime import UTC, datetime
from enum import StrEnum
from uuid import uuid4

from sqlalchemy import JSON, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def now_utc() -> datetime:
    return datetime.now(UTC)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    SENSITIVE_HEALTH = "sensitive_health"
    SECRET = "secret"


class AssessmentStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.INTERNAL,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    sessions: Mapped[list["AssessmentSession"]] = relationship(back_populates="user")


class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    consent_type: Mapped[str] = mapped_column(String, nullable=False)
    version: Mapped[str] = mapped_column(String, nullable=False)
    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.INTERNAL,
        nullable=False,
    )


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, default=AssessmentStatus.IN_PROGRESS)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.SENSITIVE_HEALTH,
        nullable=False,
    )

    user: Mapped[User] = relationship(back_populates="sessions")
    answers: Mapped[list["AssessmentAnswer"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    result: Mapped["RiskResult | None"] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    report: Mapped["AIReport | None"] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )
    heart_plan: Mapped["HeartPlanRecommendation | None"] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class AssessmentAnswer(Base):
    __tablename__ = "assessment_answers"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("assessment_sessions.id"), nullable=False)
    field_key: Mapped[str] = mapped_column(String, nullable=False)
    value: Mapped[dict] = mapped_column(JSON, nullable=False)
    unit: Mapped[str | None] = mapped_column(String)
    confidence: Mapped[str] = mapped_column(String, default="reported", nullable=False)
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.SENSITIVE_HEALTH,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)

    session: Mapped[AssessmentSession] = relationship(back_populates="answers")


class RiskResult(Base):
    __tablename__ = "risk_results"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("assessment_sessions.id"),
        unique=True,
        nullable=False,
    )
    ascvd_risk: Mapped[float] = mapped_column(Float, nullable=False)
    framingham_risk: Mapped[float] = mapped_column(Float, nullable=False)
    heart_age: Mapped[int] = mapped_column(nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    risk_factors: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    protective_signals: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.SENSITIVE_HEALTH,
        nullable=False,
    )

    session: Mapped[AssessmentSession] = relationship(back_populates="result")


class AIReport(Base):
    __tablename__ = "ai_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("assessment_sessions.id"),
        unique=True,
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.SENSITIVE_HEALTH,
        nullable=False,
    )

    session: Mapped[AssessmentSession] = relationship(back_populates="report")


class HeartPlanRecommendation(Base):
    __tablename__ = "heart_plan_recommendations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("assessment_sessions.id"),
        unique=True,
        nullable=False,
    )
    sections: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by: Mapped[str] = mapped_column(String, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.SENSITIVE_HEALTH,
        nullable=False,
    )

    session: Mapped[AssessmentSession] = relationship(back_populates="heart_plan")


class AssessmentSummaryCache(Base):
    __tablename__ = "assessment_summary_cache"

    cache_key: Mapped[str] = mapped_column(String, primary_key=True)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    disclaimer: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    prompt_version: Mapped[str] = mapped_column(String, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.SENSITIVE_HEALTH,
        nullable=False,
    )


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    content_type: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.PUBLIC,
        nullable=False,
    )


class ContentSummary(Base):
    __tablename__ = "content_summaries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    content_item_id: Mapped[str] = mapped_column(
        ForeignKey("content_items.id"),
        unique=True,
        nullable=False,
    )
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    generated_by: Mapped[str] = mapped_column(String, default="dummy", nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.PUBLIC,
        nullable=False,
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_type: Mapped[str] = mapped_column(String, nullable=False)
    entity_id: Mapped[str] = mapped_column(String, nullable=False)
    event_metadata: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc)
    data_classification: Mapped[str] = mapped_column(
        String,
        default=DataClassification.INTERNAL,
        nullable=False,
    )
