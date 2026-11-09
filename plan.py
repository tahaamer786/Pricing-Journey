from datetime import datetime, date
from typing import Optional
from decimal import Decimal
from sqlalchemy import String, DateTime, Date, Boolean, Integer, DECIMAL, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import secrets
import string

from database import Base


def gen_id() -> str:
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(8))


class Plan(Base):
    """Pricing plan (Starter, Essential, Professional, Custom)."""
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(8), primary_key=True, default=gen_id)
    name: Mapped[str] = mapped_column(String(100), nullable=False)                 # "Starter"
    price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)  # null for Custom
    price_label: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "Custom pricing" override
    minutes_included: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    minutes_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "Custom minute package"

    setup_fee: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 2), nullable=True)
    is_free_for_founding_clients: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    founding_client_start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    founding_client_end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    is_custom: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_most_popular: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    button_text: Mapped[str] = mapped_column(String(100), nullable=False, default="Start free")  # "Contact us" for custom
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # icon identifier for frontend

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    features: Mapped[list["PlanFeature"]] = relationship(
        "PlanFeature", back_populates="plan", cascade="all, delete-orphan",
        order_by="PlanFeature.display_order"
    )


class PlanFeature(Base):
    """A single feature line under a plan, toggleable true/false."""
    __tablename__ = "plan_features"

    id: Mapped[str] = mapped_column(String(8), primary_key=True, default=gen_id)
    plan_id: Mapped[str] = mapped_column(String(8), ForeignKey("plans.id", ondelete="CASCADE"), nullable=False, index=True)
    feature_text: Mapped[str] = mapped_column(String(300), nullable=False)
    is_included: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    plan: Mapped["Plan"] = relationship("Plan", back_populates="features")
