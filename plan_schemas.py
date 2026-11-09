from pydantic import BaseModel, model_validator
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime


# ── Features ──────────────────────────────────────────────────────────────────

class PlanFeatureCreate(BaseModel):
    feature_text: str
    is_included: bool = True
    display_order: int = 0


class PlanFeatureUpdate(BaseModel):
    feature_text: Optional[str] = None
    is_included: Optional[bool] = None
    display_order: Optional[int] = None


class PlanFeatureOut(BaseModel):
    id: str
    feature_text: str
    is_included: bool
    display_order: int

    model_config = {"from_attributes": True}


# ── Plans ─────────────────────────────────────────────────────────────────────

class PlanCreate(BaseModel):
    name: str
    price: Optional[Decimal] = None
    price_label: Optional[str] = None
    minutes_included: Optional[int] = None
    minutes_label: Optional[str] = None
    setup_fee: Optional[Decimal] = None
    is_free_for_founding_clients: bool = False
    founding_client_start_date: Optional[date] = None
    founding_client_end_date: Optional[date] = None
    is_custom: bool = False
    is_most_popular: bool = False
    button_text: str = "Start free"
    display_order: int = 0
    icon: Optional[str] = None
    features: List[PlanFeatureCreate] = []

    @model_validator(mode="after")
    def validate_min_features(self):
        if len(self.features) < 5 and not self.is_custom:
            raise ValueError("Each non-custom plan must have at least 5 features")
        return self


class PlanUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[Decimal] = None
    price_label: Optional[str] = None
    minutes_included: Optional[int] = None
    minutes_label: Optional[str] = None
    setup_fee: Optional[Decimal] = None
    is_free_for_founding_clients: Optional[bool] = None
    founding_client_start_date: Optional[date] = None
    founding_client_end_date: Optional[date] = None
    is_most_popular: Optional[bool] = None
    button_text: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    icon: Optional[str] = None


class PlanOut(BaseModel):
    id: str
    name: str
    price: Optional[Decimal]
    price_label: Optional[str]
    minutes_included: Optional[int]
    minutes_label: Optional[str]
    setup_fee: Optional[Decimal]
    is_free_for_founding_clients: bool
    founding_client_start_date: Optional[date]
    founding_client_end_date: Optional[date]
    is_custom: bool
    is_most_popular: bool
    button_text: str
    display_order: int
    is_active: bool
    icon: Optional[str]
    features: List[PlanFeatureOut] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SimpleMessage(BaseModel):
    message: str
