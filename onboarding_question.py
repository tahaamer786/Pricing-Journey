from datetime import datetime
from sqlalchemy import String, DateTime, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import secrets
import string

from database import Base


def gen_id() -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(8))


class OnboardingQuestion(Base):
    """
    Questions shown to a user who does NOT provide a company URL.
    Fully admin-editable — add/edit/remove/reorder anytime.
    """
    __tablename__ = "onboarding_questions"

    id: Mapped[str] = mapped_column(String(8), primary_key=True, default=gen_id)
    question_text: Mapped[str] = mapped_column(String(500), nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
