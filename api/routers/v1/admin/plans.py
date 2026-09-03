from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from models.config import get_db
from models.admin.plan import Plan
from models.admin.user import Admin
from schemas.admin.plan import PlanCreate, PlanUpdate, PlanResponse
from schemas.admin.user import AdminPermission
from schemas.subscription import PlanStatus
from libs.deps import require_admin_permission
from libs.audit import record_audit_log
from libs.payment import payment_manager, PaymentException
import structlog

logger = structlog.get_logger()

router = APIRouter(prefix="/plans", tags=["Admin Plan Management"])


@router.get("", response_model=list[PlanResponse])
async def list_plans(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_BILLINGS)),
):
    result = await db.scalars(select(Plan).order_by(Plan.price.asc()))
    return result.all()


@router.get("/{plan_id_or_slug}", response_model=PlanResponse)
async def get_plan(
    plan_id_or_slug: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_BILLINGS)),
):
    query = select(Plan).where(Plan.slug == plan_id_or_slug)
    if plan_id_or_slug.isdigit():
        query = select(Plan).where(or_(Plan.slug == plan_id_or_slug, Plan.id == int(plan_id_or_slug)))

    plan = await db.scalar(query)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")
    return plan


@router.post("", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: PlanCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_BILLINGS)),
):
    clean_slug = payload.slug.strip().lower()
    existing_slug = await db.scalar(select(Plan).where(Plan.slug == clean_slug))
    if existing_slug:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan with slug '{clean_slug}' already exists",
        )

    existing_name = await db.scalar(select(Plan).where(Plan.name == payload.name.strip()))
    if existing_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plan with name '{payload.name}' already exists",
        )

    paystack_plan_code = payload.paystack_planid
    plan_interval = (payload.interval or "monthly").strip().lower()
    ps_interval = "annually" if plan_interval in ("yearly", "annually") else "monthly"

    # Free and trial plans should not be created on Paystack
    if clean_slug not in ["free", "trial"] and not paystack_plan_code and payload.price > 0:
        try:
            # Paystack amounts are in subunit (kobo for NGN)
            ps_res = await payment_manager.paystack_create_plan(
                name=payload.name,
                amount=payload.price,
                interval=ps_interval,
                description=payload.description,
            )
            paystack_plan_code = ps_res.get("data", {}).get("plan_code")
        except PaymentException as pe:
            logger.warning("Failed to automatically create plan on Paystack", error=pe.message)

    plan = Plan(
        slug=clean_slug,
        name=payload.name.strip(),
        description=payload.description.strip(),
        price=payload.price,
        interval=plan_interval,
        has_trial=payload.has_trial,
        trial_duration_days=payload.trial_duration_days or 0,
        store_limit=payload.store_limit,
        product_limit=payload.product_limit,
        sales_limit_per_month=payload.sales_limit_per_month,
        analytics_read_per_month=payload.analytics_read_per_month,
        status=payload.status,
        paystack_planid=paystack_plan_code,
    )
    db.add(plan)
    await db.flush()
    await db.refresh(plan)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="PLAN_CREATED",
        target_type="plan",
        details={"slug": plan.slug, "name": plan.name, "price": plan.price, "interval": plan.interval, "has_trial": plan.has_trial, "trial_duration_days": plan.trial_duration_days},
    )
    await db.commit()
    return plan


@router.put("/{plan_id_or_slug}", response_model=PlanResponse)
async def update_plan(
    plan_id_or_slug: str,
    payload: PlanUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_BILLINGS)),
):
    query = select(Plan).where(Plan.slug == plan_id_or_slug)
    if plan_id_or_slug.isdigit():
        query = select(Plan).where(or_(Plan.slug == plan_id_or_slug, Plan.id == int(plan_id_or_slug)))

    plan = await db.scalar(query)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")

    old_values = {
        "name": plan.name,
        "price": plan.price,
        "interval": plan.interval,
        "status": plan.status.value if hasattr(plan.status, "value") else str(plan.status),
    }

    if payload.name is not None:
        plan.name = payload.name.strip()
    if payload.description is not None:
        plan.description = payload.description.strip()
    if payload.price is not None:
        plan.price = payload.price
    if payload.interval is not None:
        plan.interval = payload.interval.strip().lower()
    if payload.has_trial is not None:
        plan.has_trial = payload.has_trial
    if payload.trial_duration_days is not None:
        plan.trial_duration_days = payload.trial_duration_days
    if payload.store_limit is not None:
        plan.store_limit = payload.store_limit
    if payload.product_limit is not None:
        plan.product_limit = payload.product_limit
    if payload.sales_limit_per_month is not None:
        plan.sales_limit_per_month = payload.sales_limit_per_month
    if payload.analytics_read_per_month is not None:
        plan.analytics_read_per_month = payload.analytics_read_per_month
    if payload.status is not None:
        plan.status = payload.status
    if payload.paystack_planid is not None:
        plan.paystack_planid = payload.paystack_planid

    # Free and trial plans should not be updated on Paystack
    if plan.slug not in ["free", "trial"] and plan.paystack_planid and (payload.name is not None or payload.price is not None or payload.description is not None):
        try:
            # Paystack amounts are in subunit (kobo for NGN)
            await payment_manager.paystack_update_plan(
                plan_code_or_id=plan.paystack_planid,
                name=payload.name,
                amount=payload.price,
                description=payload.description,
            )
        except PaymentException as pe:
            logger.warning("Failed to sync plan update with Paystack", error=pe.message)

    await db.flush()
    await db.refresh(plan)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="PLAN_UPDATED",
        target_type="plan",
        details={"slug": plan.slug, "old": old_values, "new": {"name": plan.name, "price": plan.price}},
    )
    await db.commit()
    return plan


@router.delete("/{plan_id_or_slug}", response_model=PlanResponse)
async def deactivate_plan(
    plan_id_or_slug: str,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_BILLINGS)),
):
    query = select(Plan).where(Plan.slug == plan_id_or_slug)
    if plan_id_or_slug.isdigit():
        query = select(Plan).where(or_(Plan.slug == plan_id_or_slug, Plan.id == int(plan_id_or_slug)))

    plan = await db.scalar(query)
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription plan not found")

    plan.status = PlanStatus.UNAVAILABLE
    await db.flush()
    await db.refresh(plan)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="PLAN_DEACTIVATED",
        target_type="plan",
        details={"slug": plan.slug, "name": plan.name},
    )
    await db.commit()
    return plan
