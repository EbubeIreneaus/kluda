import re
import uuid
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import joinedload
from models.config import get_db
from models.user import Customer, Debtor
from schemas.user import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    DebtorCreate,
    DebtorUpdate,
    DebtorResponse,
    CustomerStatus,
    StaffPermission,
)
from models.user import Staff
from libs.deps import require_permission, get_staff
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from libs.ws_manager import manager as ws_manager

router = APIRouter(prefix="/customer", tags=["Customer"])


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    existing = await db.execute(select(Customer).where(Customer.email == customer_data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists",
        )

    new_customer = Customer(
        customer_id=uuid.uuid4(),
        fullname=customer_data.fullname,
        phone=customer_data.phone,
        address=customer_data.address,
        email=customer_data.email,
        status=customer_data.status,
    )

    db.add(new_customer)
    await db.flush()
    await db.commit()
    await db.refresh(new_customer)
    await ws_manager.broadcast(
        {"event": "add_customer", "data": CustomerResponse.model_validate(new_customer).model_dump()},
        exclude_staff_id=staff_id,
    )
    return new_customer


@router.get("/", response_model=list[CustomerResponse])
async def get_customers(
    search: str | None = Query(None, description="Search customers by fullname, email, phone or address"),
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(get_staff),
):
    stmt = select(Customer)

    if search and search.strip():
        terms = [re.sub(r'[^\w]', '', term) for term in search.split() if term.strip()]
        terms = [t for t in terms if t]
        if terms:
            query_str = " | ".join([f"{term}:*" for term in terms])
            text_vector = func.to_tsvector(
                'english',
                func.coalesce(Customer.fullname, '') + ' ' +
                func.coalesce(Customer.email, '') + ' ' +
                func.coalesce(Customer.phone, '') + ' ' +
                func.coalesce(Customer.address, '')
            )
            ts_query = func.to_tsquery('english', query_str)
            rank = func.ts_rank(text_vector, ts_query)

            stmt = stmt.where(text_vector.op('@@')(ts_query)).order_by(rank.desc(), Customer.created_at.desc())
        else:
            stmt = stmt.order_by(Customer.created_at.desc())
    else:
        stmt = stmt.order_by(Customer.created_at.desc())

    results = (await db.scalars(stmt)).all()
    return results


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(get_staff),
):
    res = await db.execute(select(Customer).where(Customer.customer_id == customer_id))
    customer = res.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found",
        )

    return customer


@router.put("/{customer_id}")
async def update_customer(
    customer_id: uuid.UUID,
    update_data: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    res = await db.execute(select(Customer).where(Customer.customer_id == customer_id))
    customer = res.scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found",
        )

    values = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if values:
        await db.execute(update(Customer).values(**values).where(Customer.customer_id == customer_id))

    await db.commit()
    await db.refresh(customer)
    await ws_manager.broadcast(
        {"event": "update_customer", "data": CustomerResponse.model_validate(customer).model_dump()},
        exclude_staff_id=staff_id,
    )
    return {"success": True}


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    res = await db.execute(select(Customer).where(Customer.customer_id == customer_id))
    customer = res.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found",
        )

    customer.status = CustomerStatus.INACTIVE
    await db.commit()
    await ws_manager.broadcast(
        {"event": "delete_customer", "data": {"customer_id": str(customer_id)}},
        exclude_staff_id=staff_id,
    )
    return {"message": f"Customer '{customer_id}' deactivated successfully"}


# --- Debtor Router ---

router2 = APIRouter(prefix="/debtor", tags=["Debt"])


@router2.post("/", response_model=DebtorResponse, status_code=status.HTTP_201_CREATED)
async def create_debtor(
    debtor_data: DebtorCreate,
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    customer = None
    if debtor_data.customer_id:
        res = await db.execute(select(Customer).where(Customer.customer_id == debtor_data.customer_id))
        customer = res.scalar_one_or_none()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID '{debtor_data.customer_id}' not found",
            )

    new_debtor = Debtor(
        debtor_id=uuid.uuid4(),
        customer_id=debtor_data.customer_id,
        amount=debtor_data.amount,
        status=debtor_data.status,
        staff_note=debtor_data.staff_note,
    )

    db.add(new_debtor)
    await db.flush()

    if customer:
        new_debtor.customer = customer

    await db.commit()
    await db.refresh(new_debtor)
    await ws_manager.broadcast(
        {"event": "add_debt", "data": DebtorResponse.model_validate(new_debtor).model_dump()},
        exclude_staff_id=staff_id,
    )
    return new_debtor


@router2.get("/", response_model=list[DebtorResponse])
async def get_debtors(
    search: str | None = Query(None, description="Search debtors by staff_note or status"),
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(get_staff),
):
    stmt = select(Debtor).options(joinedload(Debtor.customer))

    if search and search.strip():
        terms = [re.sub(r'[^\w]', '', term) for term in search.split() if term.strip()]
        terms = [t for t in terms if t]
        if terms:
            query_str = " | ".join([f"{term}:*" for term in terms])
            text_vector = func.to_tsvector(
                'english',
                func.coalesce(Debtor.staff_note, '') + ' ' +
                func.coalesce(Debtor.status, '')
            )
            ts_query = func.to_tsquery('english', query_str)
            rank = func.ts_rank(text_vector, ts_query)

            stmt = stmt.where(text_vector.op('@@')(ts_query)).order_by(rank.desc(), Debtor.created_at.desc())
        else:
            stmt = stmt.order_by(Debtor.created_at.desc())
    else:
        stmt = stmt.order_by(Debtor.created_at.desc())

    results = await db.scalars(stmt)
    return results.all()


@router2.get("/{debtor_id}", response_model=DebtorResponse)
async def get_debtor(
    debtor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(get_staff),
):
    res = await db.execute(
        select(Debtor).options(joinedload(Debtor.customer)).where(Debtor.debtor_id == debtor_id)
    )
    debtor = res.scalar_one_or_none()

    if not debtor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debtor record with ID '{debtor_id}' not found",
        )

    return debtor


@router2.put("/{debtor_id}")
async def update_debtor(
    debtor_id: uuid.UUID,
    update_data: DebtorUpdate,
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    res = await db.execute(
        select(Debtor).options(joinedload(Debtor.customer)).where(Debtor.debtor_id == debtor_id)
    )
    debtor = res.scalar_one_or_none()
    if not debtor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debtor record with ID '{debtor_id}' not found",
        )

    values = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if values:
        await db.execute(update(Debtor).values(**values).where(Debtor.debtor_id == debtor_id))

    await db.commit()
    await db.refresh(debtor)
    await ws_manager.broadcast(
        {"event": "update_debt", "data": DebtorResponse.model_validate(debtor).model_dump()},
        exclude_staff_id=staff_id,
    )
    return {"success": True}


@router2.delete("/{debtor_id}")
async def delete_debtor(
    debtor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(default="unknown", description="Staff ID for WS broadcast exclusion"),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    res = await db.execute(select(Debtor).where(Debtor.debtor_id == debtor_id))
    debtor = res.scalar_one_or_none()

    if not debtor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debtor record with ID '{debtor_id}' not found",
        )

    debtor.status = "paid"
    await db.commit()
    await ws_manager.broadcast(
        {"event": "delete_debt", "data": {"debtor_id": str(debtor_id)}},
        exclude_staff_id=staff_id,
    )
    return {"message": f"Debtor record '{debtor_id}' marked as paid"}