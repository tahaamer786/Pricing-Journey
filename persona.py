from datetime import datetime
from typing import Optional
import enum
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import secrets
import string

from database import Base


def gen_id() -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(8))


class SourceType(str, enum.Enum):
    url = "url"
    questions = "questions"


class PersonaStatus(str, enum.Enum):
    pending_call = "pending_call"
    called = "called"


class PersonaReport(Base):
    """The AI-generated persona report for a user's business."""
    __tablename__ = "persona_reports"

    id: Mapped[str] = mapped_column(String(8), primary_key=True, default=gen_id)
    user_id: Mapped[str] = mapped_column(String(8), ForeignKey("onboarding_users.id", ondelete="CASCADE"), nullable=False, index=True)

    source_type: Mapped[SourceType] = mapped_column(SqlEnum(SourceType), nullable=False)
    company_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Full structured output from the LLM, stored as JSON
    persona_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    status: Mapped[PersonaStatus] = mapped_column(
        SqlEnum(PersonaStatus), default=PersonaStatus.pending_call, nullable=False, index=True
    )
    called_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    call_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    qa_pairs: Mapped[list["PersonaQA"]] = relationship(
        "PersonaQA", back_populates="persona", cascade="all, delete-orphan"
    )


class PersonaQA(Base):
    """Stores the raw question/answer pairs when the user went the 'no URL' route."""
    __tablename__ = "persona_qa"

    id: Mapped[str] = mapped_column(String(8), primary_key=True, default=gen_id)
    persona_id: Mapped[str] = mapped_column(String(8), ForeignKey("persona_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    persona: Mapped["PersonaReport"] = relationship("PersonaReport", back_populates="qa_pairs")
