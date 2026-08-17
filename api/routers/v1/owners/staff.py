from sys import prefix
from fastapi import APIRouter, status, HTTPException, Depends, Request, Query
from libs.security import hash_password
from models.user import Staff
from routers.v1.business.staff import generate_staff_id
from schemas.user import StaffCreate, StaffResponse, StaffStatus, StaffUpdate
from schemas.business import  StoreResponseMini
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from datetime import datetime, timezone
from libs.deps import get_store
from models.config import get_db
from libs.ws_manager import manager as ws_manager
import uuid

router = APIRouter(prefix="/staff")

@router.post("/revoke-access")
async def reset_access_token(
    target_staff_id: str,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_store),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Staff).where(Staff.staff_id == target_staff_id, Staff.store_id== store.store_id))
    staff = res.scalar_one_or_none()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with ID '{target_staff_id}' not found",
        )

    staff.access_token = None
    staff.sessions.clear()
    await db.commit()

    await ws_manager.broadcast(
        store.store_id,
        {
            "event": "staff_status_changed",
            "data": {
                "staff_id": target_staff_id,
                "status": "revoked"
            }
        }
    )

    return {"message": f"Access token revoked for staff '{target_staff_id}'"}

@router.post("/{store_id}")
async def create_staff(
    staff_data: StaffCreate,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_store),
    db: AsyncSession = Depends(get_db)
):
    staff_id = await generate_staff_id(db, prefix=store.name[:3].strip().upper())
    
    new_staff = Staff(
        staff_id=staff_id,
        first_name=staff_data.first_name,
        last_name=staff_data.last_name,
        other_name=staff_data.other_name,
        role=staff_data.role,
        store_id = store.store_id,
        password=hash_password(staff_data.password),
        phone=staff_data.phone,
        email=staff_data.email,
        permission=staff_data.permission,
        status=staff_data.status,
    )

    db.add(new_staff)
    await db.flush()

    return new_staff

@router.get("/", response_model=list[StaffResponse])
async def get_staffs(
    store_id: uuid.UUID,
    status_filter: StaffStatus | None = Query(None, alias="status"),
    store: StoreResponseMini = Depends(get_store),
    db: AsyncSession = Depends(get_db),
):
    query = select(Staff)
    if status_filter:
        query = query.where(Staff.status == status_filter, Staff.store_id == store.store_id)

    res = await db.scalars(query)
    staffs = res.all()

    return staffs

@router.get("/{staff_id}")
async def get_staff(
    staff_id: str,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_store),
    db: AsyncSession = Depends(get_db),
) -> StaffResponse:
    res = await db.execute(select(Staff).where(Staff.staff_id == staff_id, Staff.store_id == store.store_id))
    staff = res.scalar_one_or_none()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with ID '{staff_id}' not found",
        )

    return staff

@router.put("/{staff_id}", response_model=StaffResponse)
@router.patch("/{staff_id}", response_model=StaffResponse)
async def update_staff(
    staff_id: str,
    update_data: StaffUpdate,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_store),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Staff).where(Staff.staff_id == staff_id, Staff.store_id == store.store_id))
    staff = res.scalar_one_or_none()
    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with ID '{staff_id}' not found",
        )

    values = update_data.model_dump(exclude_unset=True, exclude_none=True)
    if "permission" in values and values["permission"] is not None:
        values["permission"] = [p.value if hasattr(p, "value") else str(p) for p in values["permission"]]

    if values:
        await db.execute(update(Staff).values(**values).where(Staff.staff_id == staff_id))
        await db.commit()
        await db.refresh(staff)
        await ws_manager.broadcast(
            store.store_id,
            {
                "event": "staff_status_changed",
                "data": {
                    "staff_id": staff_id,
                    "status": staff.status.value if hasattr(staff.status, "value") else str(staff.status),
                    "role": staff.role,
                    "permission": staff.permission
                }
            }
        )

    return staff

@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str,
    store_id: uuid.UUID,
    store: StoreResponseMini = Depends(get_store),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(Staff).where(Staff.staff_id == staff_id, Staff.store_id == store.store_id))
    staff = res.scalar_one_or_none()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with ID '{staff_id}' not found",
        )

    staff.status = StaffStatus.TERMINATED
    staff.sessions.clear()
    staff.access_token = None
    await db.commit()

    await ws_manager.broadcast(
        store.store_id,
        {
            "event": "staff_status_changed",
            "data": {
                "staff_id": staff_id,
                "status": "terminated"
            }
        }
    )

    return {"message": f"Staff with ID '{staff_id}' has been terminated and deleted"}


