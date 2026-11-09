from pydantic import BaseModel, model_validator
from typing import Optional, List
from datetime import datetime


# ── Business info submission ─────────────────────────────────────────────────

class BusinessInfoRequest(BaseModel):
    """Step: user either gives a URL, or explicitly says they have none."""
    has_url: bool
    company_url: Optional[str] = None

    @model_validator(mode="after")
    def validate_url_present(self):
        if self.has_url and not self.company_url:
            raise ValueError("company_url is required when has_url=true")
        return self


class BusinessInfoResponse(BaseModel):
    """
    If has_url=true  -> persona generation kicks off immediately (call /persona/generate next)
    If has_url=false -> questions are returned for the user to answer
    """
    has_url: bool
    questions: Optional[List["OnboardingQuestionOut"]] = None
    message: str


# ── Questions (admin-editable) ───────────────────────────────────────────────

class OnboardingQuestionCreate(BaseModel):
    question_text: str
    display_order: int = 0


class OnboardingQuestionUpdate(BaseModel):
    question_text: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None


class OnboardingQuestionOut(BaseModel):
    id: str
    question_text: str
    display_order: int
    is_active: bool

    model_config = {"from_attributes": True}


# ── Answers submission ───────────────────────────────────────────────────────

class AnswerItem(BaseModel):
    question_id: str
    answer: str


class SubmitAnswersRequest(BaseModel):
    answers: List[AnswerItem]
