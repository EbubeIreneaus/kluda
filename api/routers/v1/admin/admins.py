import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.admin.user import Admin
from schemas.admin.auth import AdminProfileResponse, AdminInviteRequest, AdminUpdateRequest
from schemas.admin.user import AdminPermission, AdminRole, AdminStatus
from libs.deps import require_admin_permission, get_admin
from libs.email_generator import generate_unique_company_email
from libs.security import hash_password
from libs.audit import record_audit_log
from libs.resend import resend_client
from setting import settings
from worker.config import get_arq_pool


router = APIRouter(prefix="/admins", tags=["Admin Team Management"])


@router.get("", response_model=list[AdminProfileResponse])
async def list_admins(
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_ADMINS)),
):
    result = await db.scalars(select(Admin).order_by(Admin.created_at.desc()))
    return result.all()


@router.post("", response_model=AdminProfileResponse)
async def invite_admin(
    payload: AdminInviteRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_ADMINS)),
):
    is_current_super_admin = (
        current_admin.role == AdminRole.SUPER_ADMIN or
        getattr(current_admin.role, "value", str(current_admin.role)) == AdminRole.SUPER_ADMIN.value or
        str(current_admin.role) == "SUPER_ADMIN"
    )

    if (payload.role == AdminRole.SUPER_ADMIN or getattr(payload.role, "value", str(payload.role)) == AdminRole.SUPER_ADMIN.value) and not is_current_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can invite another super admin",
        )

    existing = await db.scalar(
        select(Admin).where(Admin.personal_email == payload.personal_email.lower())
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An admin with this personal email already exists",
        )

    company_email = await generate_unique_company_email(db, payload.fullname)
    temp_password = "KludaAdmin@" + uuid.uuid4().hex[:6]
    hashed_password = hash_password(temp_password)

    new_admin = Admin(
        fullname=payload.fullname,
        company_email=company_email,
        personal_email=payload.personal_email.lower(),
        phone=payload.phone,
        password=hashed_password,
        role=payload.role,
        permission=[p.value if hasattr(p, 'value') else p for p in payload.permission],
        status=AdminStatus.ACTIVE,
    )
    db.add(new_admin)
    await db.flush()
    await db.refresh(new_admin)

    await record_audit_log(
        db=db,
        admin_id=current_admin.admin_id,
        action="ADMIN_INVITED",
        target_type="admin",
        target_id=new_admin.admin_id,
        details={"company_email": company_email, "role": payload.role.value if hasattr(payload.role, 'value') else str(payload.role)},
    )

    arq_pool = await get_arq_pool()
    if arq_pool:
        await arq_pool.enqueue_job(
            "send_admin_welcome_email",
            new_admin.fullname,
            new_admin.personal_email,
            new_admin.company_email,
            new_admin.role.value if hasattr(new_admin.role, 'value') else str(new_admin.role),
            temp_password,
        )

    return new_admin


@router.get("/{admin_id}", response_model=AdminProfileResponse)
async def get_admin_detail(
    admin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_ADMINS)),
):
    admin = await db.scalar(select(Admin).where(Admin.admin_id == admin_id))
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")
    return admin


@router.put("/{admin_id}", response_model=AdminProfileResponse)
async def update_admin(
    admin_id: uuid.UUID,
    payload: AdminUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_ADMINS)),
):
    admin = await db.scalar(select(Admin).where(Admin.admin_id == admin_id))
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")

    is_current_super_admin = (
        current_admin.role == AdminRole.SUPER_ADMIN or
        getattr(current_admin.role, "value", str(current_admin.role)) == AdminRole.SUPER_ADMIN.value or
        str(current_admin.role) == "SUPER_ADMIN"
    )
    is_self = (current_admin.admin_id == admin.admin_id)
    is_target_super_admin = (
        admin.role == AdminRole.SUPER_ADMIN or
        getattr(admin.role, "value", str(admin.role)) == AdminRole.SUPER_ADMIN.value or
        str(admin.role) == "SUPER_ADMIN"
    )

    if is_self and not is_current_super_admin:
        if payload.permission is not None or payload.role is not None or payload.status is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admins are not allowed to modify their own permissions, role, or status",
            )

    if is_target_super_admin and not is_current_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can modify super admin accounts",
        )

    if payload.role is not None:
        is_assigning_super_admin = (
            payload.role == AdminRole.SUPER_ADMIN or
            getattr(payload.role, "value", str(payload.role)) == AdminRole.SUPER_ADMIN.value or
            str(payload.role) == "SUPER_ADMIN"
        )
        if is_assigning_super_admin and not is_current_super_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can assign the super admin role",
            )
        admin.role = payload.role

    if payload.fullname is not None:
        admin.fullname = payload.fullname
    if payload.personal_email is not None:
        admin.personal_email = payload.personal_email.lower()
    if payload.phone is not None:
        admin.phone = payload.phone
    if payload.permission is not None:
        admin.permission = [p.value if hasattr(p, 'value') else p for p in payload.permission]
    if payload.status is not None:
        admin.status = payload.status

    await db.flush()
    await db.refresh(admin)

    await record_audit_log(
        db=db,
        admin_id=current_admin.admin_id,
        action="ADMIN_UPDATED",
        target_type="admin",
        target_id=admin.admin_id,
        details={"updated_fields": payload.model_dump(exclude_unset=True)},
    )
    return admin


@router.delete("/{admin_id}")
async def delete_admin(
    admin_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_ADMINS)),
):
    if current_admin.admin_id == admin_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="You cannot delete your own admin account")

    admin = await db.scalar(select(Admin).where(Admin.admin_id == admin_id))
    if not admin:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Admin not found")

    is_current_super_admin = (
        current_admin.role == AdminRole.SUPER_ADMIN or
        getattr(current_admin.role, "value", str(current_admin.role)) == AdminRole.SUPER_ADMIN.value or
        str(current_admin.role) == "SUPER_ADMIN"
    )
    is_target_super_admin = (
        admin.role == AdminRole.SUPER_ADMIN or
        getattr(admin.role, "value", str(admin.role)) == AdminRole.SUPER_ADMIN.value or
        str(admin.role) == "SUPER_ADMIN"
    )

    if is_target_super_admin and not is_current_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can delete super admin accounts",
        )

    await db.delete(admin)
    await db.flush()

    await record_audit_log(
        db=db,
        admin_id=current_admin.admin_id,
        action="ADMIN_DELETED",
        target_type="admin",
        target_id=admin_id,
    )
    return {"status": "ok", "message": "Admin deleted successfully"}
