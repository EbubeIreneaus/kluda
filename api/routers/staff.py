from sqlalchemy import update
import secrets
from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.config import get_db
from models.user import Staff
from schemas.user import (
    StaffCreate,
    StaffUpdate,
    StaffResponse,
    StaffPermission,
    StaffStatus,
)
from libs.security import hash_password
from libs.deps import require_permission

router = APIRouter(prefix="/staff", tags=["Staff"])


async def generate_staff_id(db: AsyncSession) -> str:
    for _ in range(10):
        code = None
        while True:
            code = f"STF{secrets.randbelow(8999) + 1000}"
            res = await db.execute(select(Staff).where(Staff.staff_id == code))
            if not res.scalar_one_or_none():
                break
        return code


@router.post("/", response_model=StaffResponse, status_code=status.HTTP_201_CREATED)
async def create_staff(
    staff_data: StaffCreate,
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
) -> StaffResponse:
    email_check = await db.execute(select(Staff).where(Staff.email == staff_data.email))
    if email_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Staff with this email already exists",
        )

    staff_id = await generate_staff_id(db)
    
    new_staff = Staff(
        staff_id=staff_id,
        first_name=staff_data.first_name,
        last_name=staff_data.last_name,
        other_name=staff_data.other_name,
        role=staff_data.role,
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
    status_filter: StaffStatus | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
):
    query = select(Staff)
    if status_filter:
        query = query.where(Staff.status == status_filter)

    res = await db.scalars(query)
    staffs = res.all()

    return staffs


@router.get("/{staff_id}")
async def get_staff(
    staff_id: str,
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
) -> StaffResponse:
    res = await db.execute(select(Staff).where(Staff.staff_id == staff_id))
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
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
):
    res = await db.execute(select(Staff).where(Staff.staff_id == staff_id))
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

    return staff


@router.delete("/{staff_id}")
async def delete_staff(
    staff_id: str,
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
):
    res = await db.execute(select(Staff).where(Staff.staff_id == staff_id))
    staff = res.scalar_one_or_none()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with ID '{staff_id}' not found",
        )

    staff.status = StaffStatus.TERMINATED
    staff.access_token = None

    return {"message": f"Staff with ID '{staff_id}' has been terminated and deleted"}


@router.post("/revoke-access")
async def reset_access_token(
    target_staff_id: str,
    db: AsyncSession = Depends(get_db),
    _: Staff = Depends(require_permission(StaffPermission.MANAGE_STAFF)),
):
    res = await db.execute(select(Staff).where(Staff.staff_id == target_staff_id))
    staff = res.scalar_one_or_none()

    if not staff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Staff with ID '{target_staff_id}' not found",
        )

    staff.access_token = None

    return {"message": f"Access token revoked for staff '{target_staff_id}'"}
