"""
Onboarding flow — business info collection.

POST /business-info:
  - has_url=true  -> saves company_url on the user, ready for persona generation
  - has_url=false -> returns the active questions for the user to answer

POST /submit-answers:
  - saves the user's answers (creates the PersonaReport shell + PersonaQA rows)

Admin endpoints manage the question bank itself.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models.user import User
from models.onboarding_question import OnboardingQuestion
from models.persona import PersonaReport, PersonaQA, SourceType
from schemas.onboarding_schemas import (
    BusinessInfoRequest, BusinessInfoResponse, OnboardingQuestionOut,
    OnboardingQuestionCreate, OnboardingQuestionUpdate, SubmitAnswersRequest,
)
from schemas.plan_schemas import SimpleMessage
from auth.jwt_utils import verify_user_token, verify_admin_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/onboarding", tags=["Onboarding"])


async def _get_current_user(db: AsyncSession, payload: dict) -> User:
    stmt = select(User).where(User.id == payload["user_id"])
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# ── User-facing ────────────────────────────────────────────────────────────────

@router.post("/business-info", response_model=BusinessInfoResponse, summary="Submit URL or request questions")
async def submit_business_info(
    data: BusinessInfoRequest,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(verify_user_token),
):
    user = await _get_current_user(db, payload)

    if data.has_url:
        user.company_url = data.company_url
        await db.commit()
        return BusinessInfoResponse(
            has_url=True,
            questions=None,
            message="URL saved. Call /persona/generate next to build the persona report.",
        )

    # No URL — return active questions
    stmt = select(OnboardingQuestion).where(OnboardingQuestion.is_active == True).order_by(OnboardingQuestion.display_order)  # noqa: E712
    result = await db.execute(stmt)
    questions = list(result.scalars().all())

    return BusinessInfoResponse(
        has_url=False,
        questions=questions,
        message="Answer these questions, then call /submit-answers.",
    )


@router.post("/submit-answers", response_model=SimpleMessage, summary="Submit answers to onboarding questions")
async def submit_answers(
    data: SubmitAnswersRequest,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(verify_user_token),
):
    user = await _get_current_user(db, payload)

    # Create a placeholder persona shell to attach QA rows to — the real
    # persona_json gets filled in when /persona/generate runs.
    stmt = select(PersonaReport).where(PersonaReport.user_id == user.id, PersonaReport.source_type == SourceType.questions)
    result = await db.execute(stmt)
    persona = result.scalar_one_or_none()

    if not persona:
        persona = PersonaReport(
            user_id=user.id,
            source_type=SourceType.questions,
            persona_json={},  # filled in later by /persona/generate
        )
        db.add(persona)
        await db.flush()

    for item in data.answers:
        q_stmt = select(OnboardingQuestion).where(OnboardingQuestion.id == item.question_id)
        q_result = await db.execute(q_stmt)
        question = q_result.scalar_one_or_none()
        question_text = question.question_text if question else item.question_id

        db.add(PersonaQA(
            persona_id=persona.id,
            question=question_text,
            answer=item.answer,
        ))

    await db.commit()
    return SimpleMessage(message="Answers submitted. Call /persona/generate next.")


# ── Admin: manage question bank ─────────────────────────────────────────────

@router.get("/questions", response_model=List[OnboardingQuestionOut], summary="Get all questions (Admin)")
async def list_questions(
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    stmt = select(OnboardingQuestion).order_by(OnboardingQuestion.display_order)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/questions", response_model=OnboardingQuestionOut, summary="Add a question (Admin)")
async def create_question(
    data: OnboardingQuestionCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    question = OnboardingQuestion(
        question_text=data.question_text,
        display_order=data.display_order,
    )
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return question


@router.post("/questions/{question_id}/update", response_model=OnboardingQuestionOut, summary="Update a question (Admin)")
async def update_question(
    question_id: str,
    data: OnboardingQuestionUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    stmt = select(OnboardingQuestion).where(OnboardingQuestion.id == question_id)
    result = await db.execute(stmt)
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(question, key, value)

    await db.commit()
    await db.refresh(question)
    return question


@router.post("/questions/{question_id}/delete", response_model=SimpleMessage, summary="Delete a question (Admin)")
async def delete_question(
    question_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    stmt = select(OnboardingQuestion).where(OnboardingQuestion.id == question_id)
    result = await db.execute(stmt)
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    await db.delete(question)
    await db.commit()
    return SimpleMessage(message="Question deleted successfully")
