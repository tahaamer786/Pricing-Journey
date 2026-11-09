from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserOut(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    profile_picture_url: Optional[str]
    company_url: Optional[str]
    selected_plan_id: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class SelectPlanRequest(BaseModel):
    plan_id: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
