"""Generate persona report (user-triggered) and list/view reports (admin)."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from models.persona import PersonaReport
from schemas.persona_schemas import PersonaReportOut, PersonaListItem, UpdatePersonaStatusRequest
from services.persona_service import generate_and_save_persona
from auth.jwt_utils import verify_user_token, verify_admin_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/persona", tags=["Persona"])


# ── User-facing ────────────────────────────────────────────────────────────────

@router.post("/generate", response_model=PersonaReportOut, summary="Generate the persona report")
async def generate_persona_endpoint(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(verify_user_token),
):
    stmt = select(User).where(User.id == payload["user_id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.company_url:
        # Ensure the questions route has actually collected answers first
        qa_stmt = select(PersonaReport).where(PersonaReport.user_id == user.id)
        qa_result = await db.execute(qa_stmt)
        if not qa_result.scalar_one_or_none():
            raise HTTPException(
                status_code=400,
                detail="No company_url and no answers submitted yet. "
                       "Call /onboarding/business-info first.",
            )

    persona = await generate_and_save_persona(db, user)
    return persona


@router.get("/mine", response_model=PersonaReportOut, summary="Get my own persona report")
async def get_my_persona(
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(verify_user_token),
):
    stmt = select(PersonaReport).where(PersonaReport.user_id == payload["user_id"]).order_by(PersonaReport.created_at.desc())
    result = await db.execute(stmt)
    persona = result.scalars().first()
    if not persona:
        raise HTTPException(status_code=404, detail="No persona report found yet")
    return persona


# ── Admin ─────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[PersonaListItem], summary="List all persona reports (Admin)")
async def list_personas(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    stmt = (
        select(PersonaReport, User)
        .join(User, PersonaReport.user_id == User.id)
        .order_by(PersonaReport.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    items = []
    for persona, user in rows:
        company_name = None
        if persona.persona_json:
            company_name = persona.persona_json.get("business_summary", {}).get("company_name")
        items.append(PersonaListItem(
            id=persona.id,
            user_id=user.id,
            user_email=user.email,
            user_name=f"{user.first_name or ''} {user.last_name or ''}".strip(),
            company_name=company_name,
            status=persona.status,
            created_at=persona.created_at,
        ))
    return items


@router.get("/{persona_id}", response_model=PersonaReportOut, summary="Get a single persona report (Admin)")
async def get_persona(
    persona_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    stmt = select(PersonaReport).where(PersonaReport.id == persona_id)
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona report not found")
    return persona


@router.post("/{persona_id}/status", response_model=PersonaReportOut, summary="Update call status (Admin)")
async def update_persona_status(
    persona_id: str,
    data: UpdatePersonaStatusRequest,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    from datetime import datetime

    stmt = select(PersonaReport).where(PersonaReport.id == persona_id)
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()
    if not persona:
        raise HTTPException(status_code=404, detail="Persona report not found")

    persona.status = data.status
    if data.call_notes is not None:
        persona.call_notes = data.call_notes
    if data.status == "called":
        persona.called_at = datetime.utcnow()

    await db.commit()
    await db.refresh(persona)
    return persona
