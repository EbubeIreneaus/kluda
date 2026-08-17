from sqlalchemy.orm import selectinload
from schemas.business import StoreResponseMini
import re
import uuid
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import joinedload
from models.config import get_db
from models.user import Customer, Debt, Staff
from schemas.user import (
    CustomerCreate,
    CustomerUpdate,
    CustomerResponse,
    DebtCreate,
    DebtUpdate,
    DebtResponse,
    CustomerStatus,
    StaffPermission,
)
from libs.deps import require_permission, get_staff, get_staff_store
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from libs.ws_manager import manager as ws_manager

router = APIRouter(prefix="/{store_id}/customer", tags=["Customer"])


@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
async def create_customer(
    customer_data: CustomerCreate,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    existing = await db.execute(
        select(Customer).where(
            Customer.email == customer_data.email, Customer.store_id == store.store_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your customer with this email already exists",
        )

    new_customer = Customer(
        customer_id=uuid.uuid4(),
        store_id=store.store_id,
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
        {
            "event": "add_customer",
            "data": CustomerResponse.model_validate(new_customer).model_dump(),
        },
        exclude_staff_id=staff_id,
    )
    return new_customer


@router.get("/", response_model=list[CustomerResponse])
async def get_customers(
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    search: str | None = Query(
        None, description="Search customers by fullname, email, phone or address"
    ),
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(get_staff),
):
    stmt = select(Customer).where(Customer.store_id == store.store_id, Customer.status == CustomerStatus.ACTIVE)

    if search and search.strip():
        terms = [re.sub(r"[^\w]", "", term) for term in search.split() if term.strip()]
        terms = [t for t in terms if t]
        if terms:
            query_str = " | ".join([f"{term}:*" for term in terms])
            text_vector = func.to_tsvector(
                "english",
                func.coalesce(Customer.fullname, "")
                + " "
                + func.coalesce(Customer.email, "")
                + " "
                + func.coalesce(Customer.phone, "")
                + " "
                + func.coalesce(Customer.address, ""),
            )
            ts_query = func.to_tsquery("english", query_str)
            rank = func.ts_rank(text_vector, ts_query)

            stmt = stmt.where(text_vector.op("@@")(ts_query)).order_by(
                rank.desc(), Customer.created_at.desc()
            )
        else:
            stmt = stmt.order_by(Customer.created_at.desc())
    else:
        stmt = stmt.order_by(Customer.created_at.desc())

    results = (await db.scalars(stmt)).all()
    return results


@router.get("/{customer_id}", response_model=CustomerResponse)
async def get_customer(
    customer_id: uuid.UUID,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(get_staff),
):
    res = await db.execute(
        select(Customer).where(
            Customer.customer_id == customer_id, Customer.store_id == store.store_id, Customer.status != CustomerStatus.DELETED
        )
    )
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
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    res = await db.execute(
        select(Customer).where(
            Customer.customer_id == customer_id, Customer.store_id == store.store_id, Customer.status != CustomerStatus.DELETED
        )
    )
    customer = res.scalar_one_or_none()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found",
        )

    values = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if values:
        await db.execute(
            update(Customer).values(**values).where(Customer.customer_id == customer_id,Customer.status != CustomerStatus.DELETED)
        )

    await db.commit()
    await db.refresh(customer)
    await ws_manager.broadcast(
        {
            "event": "update_customer",
            "data": CustomerResponse.model_validate(customer).model_dump(),
        },
        exclude_staff_id=staff_id,
    )
    return {"success": True}


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: uuid.UUID,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    res = await db.execute(
        select(Customer).where(
            Customer.customer_id == customer_id, Customer.store_id == store.store_id, Customer.status != CustomerStatus.DELETED
        )
    )
    customer = res.scalar_one_or_none()

    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with ID '{customer_id}' not found",
        )

    customer.status = CustomerStatus.DELETED
    await db.commit()
    await ws_manager.broadcast(
        {"event": "delete_customer", "data": {"customer_id": str(customer_id)}},
        exclude_staff_id=staff_id,
    )
    return {"message": f"Customer '{customer_id}' deactivated successfully"}



router2 = APIRouter(prefix="/{store_id}/debt", tags=["Debt"])


@router2.post("/", response_model=DebtResponse, status_code=status.HTTP_201_CREATED)
async def create_debt(
    store_id: uuid.UUID,
    debt_data: DebtCreate,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    customer = None
    if debt_data.customer_id:
        res = await db.execute(
            select(Customer).where(
                Customer.customer_id == debt_data.customer_id,
                Customer.store_id == store.store_id,
            )
        )
        customer = res.scalar_one_or_none()
        if not customer:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Customer with ID '{debt_data.customer_id}' not found",
            )

    new_debt = Debt(
        debt_id=uuid.uuid4(),
        customer_id=debt_data.customer_id,
        amount=debt_data.amount,
        status=debt_data.status,
        staff_note=debt_data.staff_note,
    )

    db.add(new_debt)
    await db.flush()

    if customer:
        new_debt.customer = customer

    await db.commit()
    await db.refresh(new_debt)
    await ws_manager.broadcast(
        {
            "event": "add_debt",
            "data": DebtResponse.model_validate(new_debt).model_dump(),
        },
        exclude_staff_id=staff_id,
    )
    return new_debt


@router2.get("/", response_model=list[DebtResponse])
async def get_debts(
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    search: str | None = Query(
        None, description="Search debts by staff_note or status"
    ),
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(get_staff),
):
    stmt = (
        select(Debt)
        .options(joinedload(Debt.customer))
        .where(Customer.store_id == store.store_id)
    )

    if search and search.strip():
        terms = [re.sub(r"[^\w]", "", term) for term in search.split() if term.strip()]
        terms = [t for t in terms if t]
        if terms:
            query_str = " | ".join([f"{term}:*" for term in terms])
            text_vector = func.to_tsvector(
                "english",
                func.coalesce(Debt.staff_note, "")
                + " "
                + func.coalesce(Debt.status, ""),
            )
            ts_query = func.to_tsquery("english", query_str)
            rank = func.ts_rank(text_vector, ts_query)

            stmt = stmt.where(text_vector.op("@@")(ts_query)).order_by(
                rank.desc(), Debt.created_at.desc()
            )
        else:
            stmt = stmt.order_by(Debt.created_at.desc())
    else:
        stmt = stmt.order_by(Debt.created_at.desc())

    results = await db.scalars(stmt)
    return results.all()


@router2.get("/{debt_id}", response_model=DebtResponse)
async def get_debt(
    store_id: uuid.UUID,
    debt_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(get_staff),
):
    res = await db.execute(
        select(Debt)
        .options(joinedload(Debt.customer))
        .where(Debt.debt_id == debt_id, Customer.store_id == store.store_id)
    )
    debt = res.scalar_one_or_none()

    if not debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debt record with ID '{debt_id}' not found",
        )

    return debt


@router2.put("/{debt_id}")
async def update_debt(
    debt_id: uuid.UUID,
    update_data: DebtUpdate,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    res = await db.execute(
        select(Debt)
        .options(joinedload(Debt.customer))
        .where(Debt.debt_id == debt_id, Customer.store_id == store.store_id)
    )
    debt = res.scalar_one_or_none()
    if not debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debt record with ID '{debt_id}' not found",
        )

    values = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if values:
        await db.execute(update(Debt).values(**values).where(Debt.debt_id == debt_id))

    await db.commit()
    await db.refresh(debt)
    await ws_manager.broadcast(
        {
            "event": "update_debt",
            "data": DebtResponse.model_validate(debt).model_dump(),
        },
        exclude_staff_id=staff_id,
    )
    return {"success": True}


@router2.delete("/{debt_id}")
async def delete_debt(
    store_id: uuid.UUID,
    debt_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_USER)),
):
    res = await db.execute(
        select(Debt)
        .options(selectinload(Debt.customer))
        .where(Debt.debt_id == debt_id, Customer.store_id == store.store_id)
    )
    debt = res.scalar_one_or_none()

    if not debt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debt record with ID '{debt_id}' not found",
        )

    debt.status = "paid"
    await db.commit()
    await ws_manager.broadcast(
        {"event": "delete_debt", "data": {"debt_id": str(debt_id)}},
        exclude_staff_id=staff_id,
    )
    return {"message": f"Debt record '{debt_id}' marked as paid"}
