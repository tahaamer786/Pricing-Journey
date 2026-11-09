"""
Public: list plans (for pricing page).
Admin (Jubala team): full CRUD on plans + their features, including the
founding-client setup-fee dates which must be editable.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database import get_db
from models.plan import Plan, PlanFeature
from schemas.plan_schemas import PlanOut, PlanCreate, PlanUpdate, PlanFeatureCreate, PlanFeatureUpdate, PlanFeatureOut, SimpleMessage
from schemas.user_schemas import SelectPlanRequest
from auth.jwt_utils import verify_admin_token, verify_user_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/plans", tags=["Plans"])


# ── User: select a plan ────────────────────────────────────────────────────────

@router.post("/select", response_model=SimpleMessage, summary="User selects a plan")
async def select_plan(
    data: SelectPlanRequest,
    db: AsyncSession = Depends(get_db),
    payload: dict = Depends(verify_user_token),
):
    from models.user import User

    plan_stmt = select(Plan).where(Plan.id == data.plan_id)
    plan_result = await db.execute(plan_stmt)
    if not plan_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Plan not found")

    user_stmt = select(User).where(User.id == payload["user_id"])
    user_result = await db.execute(user_stmt)
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.selected_plan_id = data.plan_id
    await db.commit()
    return SimpleMessage(message="Plan selected successfully")


# ── PUBLIC ────────────────────────────────────────────────────────────────────

@router.get("", response_model=List[PlanOut], summary="Get all active plans (Public)")
async def list_plans(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(Plan)
        .options(selectinload(Plan.features))
        .where(Plan.is_active == True)  # noqa: E712
        .order_by(Plan.display_order)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.get("/{plan_id}", response_model=PlanOut, summary="Get single plan (Public)")
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Plan).options(selectinload(Plan.features)).where(Plan.id == plan_id)
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


# ── ADMIN (Auth required) ─────────────────────────────────────────────────────

@router.post("", response_model=PlanOut, summary="Create plan (Admin)")
async def create_plan(
    data: PlanCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    plan = Plan(
        name=data.name,
        price=data.price,
        price_label=data.price_label,
        minutes_included=data.minutes_included,
        minutes_label=data.minutes_label,
        setup_fee=data.setup_fee,
        is_free_for_founding_clients=data.is_free_for_founding_clients,
        founding_client_start_date=data.founding_client_start_date,
        founding_client_end_date=data.founding_client_end_date,
        is_custom=data.is_custom,
        is_most_popular=data.is_most_popular,
        button_text=data.button_text,
        display_order=data.display_order,
        icon=data.icon,
    )
    db.add(plan)
    await db.flush()

    for f in data.features:
        db.add(PlanFeature(
            plan_id=plan.id,
            feature_text=f.feature_text,
            is_included=f.is_included,
            display_order=f.display_order,
        ))

    await db.commit()

    stmt = select(Plan).options(selectinload(Plan.features)).where(Plan.id == plan.id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.post("/{plan_id}/update", response_model=PlanOut, summary="Update plan (Admin)")
async def update_plan(
    plan_id: str,
    data: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    """Update plan fields, including founding_client_start_date / end_date."""
    stmt = select(Plan).where(Plan.id == plan_id)
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan, key, value)

    await db.commit()

    stmt = select(Plan).options(selectinload(Plan.features)).where(Plan.id == plan_id)
    result = await db.execute(stmt)
    return result.scalar_one()


@router.post("/{plan_id}/delete", response_model=SimpleMessage, summary="Delete plan (Admin)")
async def delete_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    stmt = select(Plan).where(Plan.id == plan_id)
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    await db.delete(plan)
    await db.commit()
    return SimpleMessage(message="Plan deleted successfully")


# ── Features (Admin) ──────────────────────────────────────────────────────────

@router.post("/{plan_id}/features", response_model=PlanFeatureOut, summary="Add a feature to a plan (Admin)")
async def add_feature(
    plan_id: str,
    data: PlanFeatureCreate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    stmt = select(Plan).where(Plan.id == plan_id)
    result = await db.execute(stmt)
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Plan not found")

    feature = PlanFeature(
        plan_id=plan_id,
        feature_text=data.feature_text,
        is_included=data.is_included,
        display_order=data.display_order,
    )
    db.add(feature)
    await db.commit()
    await db.refresh(feature)
    return feature


@router.post("/features/{feature_id}/update", response_model=PlanFeatureOut, summary="Update a feature (Admin)")
async def update_feature(
    feature_id: str,
    data: PlanFeatureUpdate,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    stmt = select(PlanFeature).where(PlanFeature.id == feature_id)
    result = await db.execute(stmt)
    feature = result.scalar_one_or_none()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(feature, key, value)

    await db.commit()
    await db.refresh(feature)
    return feature


@router.post("/features/{feature_id}/delete", response_model=SimpleMessage, summary="Delete a feature (Admin)")
async def delete_feature(
    feature_id: str,
    db: AsyncSession = Depends(get_db),
    _: dict = Depends(verify_admin_token),
):
    stmt = select(PlanFeature).where(PlanFeature.id == feature_id)
    result = await db.execute(stmt)
    feature = result.scalar_one_or_none()
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")

    await db.delete(feature)
    await db.commit()
    return SimpleMessage(message="Feature deleted successfully")
