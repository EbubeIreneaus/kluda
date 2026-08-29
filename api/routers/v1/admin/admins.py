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
        details={"company_email": company_email, "role": payload.role.value},
    )

    if hasattr(settings, "RESEND_API_KEY") and settings.RESEND_API_KEY:
        try:
            resend_client.Emails.send({
                "from": f"Kluda Team <team@{settings.DOMAIN_NAME}>",
                "to": [new_admin.personal_email],
                "subject": "You have been invited to Kluda Admin Portal",
                "html": f"""
                    <p>Hello {new_admin.fullname},</p>
                    <p>You have been assigned an administrator account on Kluda Platform.</p>
                    <p><strong>Company Email:</strong> {new_admin.company_email}</p>
                    <p><strong>Temporary Password:</strong> {temp_password}</p>
                    <p><a href="https://administration.{settings.DOMAIN_NAME}/login">Click here to log into Admin Portal</a></p>
                """,
            })
        except Exception:
            pass

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

    if payload.fullname is not None:
        admin.fullname = payload.fullname
    if payload.personal_email is not None:
        admin.personal_email = payload.personal_email.lower()
    if payload.phone is not None:
        admin.phone = payload.phone
    if payload.role is not None:
        admin.role = payload.role
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
