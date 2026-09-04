from sqlalchemy.orm import selectinload
from schemas.business import StoreResponseMini
import re
import uuid
from fastapi import APIRouter, HTTPException, Depends, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from sqlalchemy.orm import joinedload
from models.config import get_db
from models.user import Customer, Debt, User
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
from libs.deps import require_permission, get_staff_store, get_current_user
from libs.ws_manager import manager as ws_manager
from libs.audit import record_store_audit
from libs.security import get_client_ip

router = APIRouter(prefix="/{store_id}/customer", tags=["Customer"])


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_customer(
    customer_data: CustomerCreate,
    store_id: uuid.UUID,
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    actor: User = Depends(require_permission(StaffPermission.CREATE_CUSTOMER)),
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

    await record_store_audit(
        db=db,
        store_id=store.store_id,
        action="customer.create",
        target_type="customer",
        actor=actor,
        target_id=str(new_customer.customer_id),
        target_name=new_customer.fullname,
        details={
            "email": new_customer.email,
            "phone": new_customer.phone,
            "address": new_customer.address,
        },
        ip_address=get_client_ip(request),
    )

    await db.commit()
    await db.refresh(new_customer)
    await ws_manager.broadcast(
        store.store_id,
        {
            "event": "add_customer",
            "data": CustomerResponse.model_validate(new_customer).model_dump(mode="json"),
        },
    )
    return new_customer


@router.get("", response_model=list[CustomerResponse])
@router.get("/", response_model=list[CustomerResponse], include_in_schema=False)
async def get_customers(
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    search: str | None = Query(
        None, description="Search customers by fullname, email, phone or address"
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.VIEW_CUSTOMER)),
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
    _: User = Depends(require_permission(StaffPermission.VIEW_CUSTOMER)),
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
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    actor: User = Depends(require_permission(StaffPermission.EDIT_CUSTOMER)),
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
        old_values = {k: str(getattr(customer, k, "")) for k in values.keys()}
        changes = {k: {"old": old_values.get(k), "new": str(v)} for k, v in values.items()}
        await db.execute(
            update(Customer).values(**values).where(Customer.customer_id == customer_id,Customer.status != CustomerStatus.DELETED)
        )
        await record_store_audit(
            db=db,
            store_id=store.store_id,
            action="customer.update",
            target_type="customer",
            actor=actor,
            target_id=str(customer_id),
            target_name=customer.fullname,
            details={"changes": changes},
            ip_address=get_client_ip(request),
        )

    await db.commit()
    await db.refresh(customer)
    await ws_manager.broadcast(
        store.store_id,
        {
            "event": "update_customer",
            "data": CustomerResponse.model_validate(customer).model_dump(mode="json"),
        },
    )
    return {"success": True}


@router.delete("/{customer_id}")
async def delete_customer(
    customer_id: uuid.UUID,
    store_id: uuid.UUID,
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    actor: User = Depends(require_permission(StaffPermission.DELETE_CUSTOMER)),
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
    await record_store_audit(
        db=db,
        store_id=store.store_id,
        action="customer.delete",
        target_type="customer",
        actor=actor,
        target_id=str(customer_id),
        target_name=customer.fullname,
        details={"email": customer.email, "phone": customer.phone},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await ws_manager.broadcast(
        store.store_id,
        {"event": "delete_customer", "data": {"customer_id": str(customer_id)}},
    )
    return {"message": f"Customer '{customer_id}' deactivated successfully"}


router_debt = APIRouter(prefix="/{store_id}/debt", tags=["Debt"])


@router_debt.post("", response_model=DebtResponse, status_code=status.HTTP_201_CREATED)
@router_debt.post("/", response_model=DebtResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_debt(
    store_id: uuid.UUID,
    debt_data: DebtCreate,
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    actor: User = Depends(require_permission(StaffPermission.RECORD_DEBT)),
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

    await record_store_audit(
        db=db,
        store_id=store.store_id,
        action="debt.record",
        target_type="debt",
        actor=actor,
        target_id=str(new_debt.debt_id),
        target_name=customer.fullname if customer else "Unknown Customer",
        details={
            "amount": float(new_debt.amount) if new_debt.amount is not None else None,
            "status": new_debt.status,
            "staff_note": new_debt.staff_note,
        },
        ip_address=get_client_ip(request),
    )

    await db.commit()
    await db.refresh(new_debt)
    await ws_manager.broadcast(
        store.store_id,
        {
            "event": "add_debt",
            "data": DebtResponse.model_validate(new_debt).model_dump(mode="json"),
        },
    )
    return new_debt


@router_debt.get("", response_model=list[DebtResponse])
@router_debt.get("/", response_model=list[DebtResponse], include_in_schema=False)
async def get_debts(
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    search: str | None = Query(
        None, description="Search debts by staff_note or status"
    ),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.VIEW_DEBT)),
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


@router_debt.get("/{debt_id}", response_model=DebtResponse)
async def get_debt(
    store_id: uuid.UUID,
    debt_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission(StaffPermission.VIEW_DEBT)),
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


@router_debt.put("/{debt_id}")
async def update_debt(
    debt_id: uuid.UUID,
    update_data: DebtUpdate,
    store_id: uuid.UUID,
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    actor: User = Depends(require_permission(StaffPermission.SETTLE_DEBT)),
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
        old_values = {}
        for k in values.keys():
            old_val = getattr(debt, k, None)
            old_values[k] = float(old_val) if isinstance(old_val, (int, float)) or hasattr(old_val, "as_tuple") else str(old_val) if old_val is not None else None

        changes = {}
        for k, v in values.items():
            new_val = float(v) if isinstance(v, (int, float)) or hasattr(v, "as_tuple") else str(v) if v is not None else None
            changes[k] = {"old": old_values.get(k), "new": new_val}

        await db.execute(update(Debt).values(**values).where(Debt.debt_id == debt_id))

        await record_store_audit(
            db=db,
            store_id=store.store_id,
            action="debt.update",
            target_type="debt",
            actor=actor,
            target_id=str(debt_id),
            target_name=debt.customer.fullname if debt.customer else "Unknown Customer",
            details={"changes": changes},
            ip_address=get_client_ip(request),
        )

    await db.commit()
    await db.refresh(debt)
    await ws_manager.broadcast(
        store.store_id,
        {
            "event": "update_debt",
            "data": DebtResponse.model_validate(debt).model_dump(mode="json"),
        },
    )
    return {"success": True}


@router_debt.delete("/{debt_id}")
async def delete_debt(
    store_id: uuid.UUID,
    debt_id: uuid.UUID,
    request: Request,
    store: StoreResponseMini = Depends(get_staff_store),
    db: AsyncSession = Depends(get_db),
    staff_id: str = Query(
        default="unknown", description="Staff ID for WS broadcast exclusion"
    ),
    actor: User = Depends(require_permission(StaffPermission.SETTLE_DEBT)),
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
    await record_store_audit(
        db=db,
        store_id=store.store_id,
        action="debt.settle",
        target_type="debt",
        actor=actor,
        target_id=str(debt_id),
        target_name=debt.customer.fullname if debt.customer else "Unknown Customer",
        details={"amount": float(debt.amount) if debt.amount is not None else None, "status": "paid"},
        ip_address=get_client_ip(request),
    )
    await db.commit()
    await ws_manager.broadcast(
        store.store_id,
        {"event": "delete_debt", "data": {"debt_id": str(debt_id)}},
    )
    return {"message": f"Debt record '{debt_id}' marked as paid"}
