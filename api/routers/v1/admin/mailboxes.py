import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.admin.email import EmailMailbox
from models.admin.user import Admin
from schemas.admin.email import MailboxCreate, MailboxUpdate, MailboxResponse, MailboxType
from schemas.admin.user import AdminPermission, AdminRole
from libs.deps import get_admin, require_admin_permission
from libs.audit import record_audit_log


router = APIRouter(prefix="/mailboxes", tags=["Admin Mailboxes"])


@router.get("", response_model=list[MailboxResponse])
async def list_mailboxes(
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    if admin.company_email:
        personal_mb = await db.scalar(
            select(EmailMailbox).where(
                (EmailMailbox.owner_admin_id == admin.admin_id)
                | (EmailMailbox.email == admin.company_email.lower())
            )
        )
        if not personal_mb:
            personal_mb = EmailMailbox(
                name=f"{admin.fullname} (Personal)",
                email=admin.company_email.lower(),
                type=MailboxType.PERSONAL,
                owner_admin_id=admin.admin_id,
                allowed_admin_ids=[str(admin.admin_id)],
            )
            db.add(personal_mb)
            await db.flush()
        elif personal_mb.owner_admin_id != admin.admin_id or personal_mb.type != MailboxType.PERSONAL:
            personal_mb.owner_admin_id = admin.admin_id
            personal_mb.type = MailboxType.PERSONAL
            await db.flush()

    stmt = select(EmailMailbox).order_by(EmailMailbox.created_at.asc())
    result = await db.scalars(stmt)
    mailboxes = result.all()

    if admin.role == AdminRole.SUPER_ADMIN or AdminPermission.MANAGE_ALL.value in admin.permission or AdminPermission.MANAGE_EMAILS.value in admin.permission:
        return mailboxes

    filtered = []
    admin_id_str = str(admin.admin_id)
    for mb in mailboxes:
        if mb.type == MailboxType.PERSONAL and (mb.owner_admin_id == admin.admin_id or mb.email.lower() == admin.company_email.lower()):
            filtered.append(mb)
        elif mb.type == MailboxType.SHARED and (not mb.allowed_admin_ids or admin_id_str in [str(x) for x in mb.allowed_admin_ids]):
            filtered.append(mb)
    return filtered


@router.post("", response_model=MailboxResponse)
async def create_mailbox(
    payload: MailboxCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    existing = await db.scalar(select(EmailMailbox).where(EmailMailbox.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mailbox with this email already exists")

    new_mailbox = EmailMailbox(
        name=payload.name,
        email=payload.email.lower(),
        type=payload.type,
        owner_admin_id=payload.owner_admin_id,
        allowed_admin_ids=[str(x) for x in payload.allowed_admin_ids],
    )
    db.add(new_mailbox)
    await db.flush()
    await db.refresh(new_mailbox)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="MAILBOX_CREATED",
        target_type="mailbox",
        target_id=new_mailbox.mailbox_id,
        details={"email": new_mailbox.email, "type": new_mailbox.type.value},
    )
    return new_mailbox


@router.put("/{mailbox_id}", response_model=MailboxResponse)
async def update_mailbox(
    mailbox_id: uuid.UUID,
    payload: MailboxUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    mailbox = await db.scalar(select(EmailMailbox).where(EmailMailbox.mailbox_id == mailbox_id))
    if not mailbox:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mailbox not found")

    if payload.name is not None:
        mailbox.name = payload.name
    if payload.allowed_admin_ids is not None:
        mailbox.allowed_admin_ids = [str(x) for x in payload.allowed_admin_ids]

    await db.flush()
    await db.refresh(mailbox)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="MAILBOX_UPDATED",
        target_type="mailbox",
        target_id=mailbox.mailbox_id,
    )
    return mailbox


@router.delete("/{mailbox_id}")
async def delete_mailbox(
    mailbox_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_EMAILS)),
):
    mailbox = await db.scalar(select(EmailMailbox).where(EmailMailbox.mailbox_id == mailbox_id))
    if not mailbox:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mailbox not found")

    await db.delete(mailbox)
    await db.flush()

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="MAILBOX_DELETED",
        target_type="mailbox",
        target_id=mailbox_id,
    )
    return {"status": "ok", "message": "Mailbox deleted successfully"}
