from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class GeneratePersonaRequest(BaseModel):
    """Called after business-info step. Empty body — backend pulls stored
    company_url / answers for the current user and calls the LLM."""
    pass


class PersonaReportOut(BaseModel):
    id: str
    user_id: str
    source_type: str
    company_url: Optional[str]
    persona_json: Dict[str, Any]
    status: str
    called_at: Optional[datetime]
    call_notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class PersonaListItem(BaseModel):
    id: str
    user_id: str
    user_email: str
    user_name: str
    company_name: Optional[str] = None
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdatePersonaStatusRequest(BaseModel):
    status: str  # "pending_call" | "called"
    call_notes: Optional[str] = None
