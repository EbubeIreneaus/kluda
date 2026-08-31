import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.config import get_db
from models.admin.email import EmailThread, EmailMessages, EmailMailbox
from models.admin.user import Admin
from schemas.admin.email import (
    EmailThreadResponse,
    EmailMessageCreate,
    EmailComposeRequest,
    EmailMessageResponse,
    EmailThreadStatus,
    MailboxType,
)
from schemas.admin.user import AdminPermission, AdminRole
from libs.deps import get_admin
from libs.resend import resend_client
from setting import settings
from worker.config import get_arq_pool


router = APIRouter(prefix="/inbox", tags=["Admin Email Inbox"])


@router.get("/threads", response_model=list[EmailThreadResponse])
async def list_threads(
    mailbox_id: uuid.UUID | None = Query(None),
    folder: str | None = Query("inbox"),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    stmt = select(EmailThread).options(selectinload(EmailThread.messages))

    if mailbox_id:
        stmt = stmt.where(EmailThread.mailbox_id == mailbox_id)
    elif (
        admin.role != AdminRole.SUPER_ADMIN
        and AdminPermission.MANAGE_ALL.value not in admin.permission
        and AdminPermission.MANAGE_EMAILS.value not in admin.permission
    ):
        user_mailboxes = await db.scalars(
            select(EmailMailbox.mailbox_id).where(
                (EmailMailbox.owner_admin_id == admin.admin_id)
                | (EmailMailbox.type == MailboxType.SHARED)
            )
        )
        accessible_ids = user_mailboxes.all()
        stmt = stmt.where(EmailThread.mailbox_id.in_(accessible_ids))

    if folder == "unread":
        stmt = stmt.where(EmailThread.status == EmailThreadStatus.UNREAD)
    elif folder == "archived":
        stmt = stmt.where(EmailThread.status == EmailThreadStatus.ARCHIVED)
    elif folder == "spam":
        stmt = stmt.where(EmailThread.status == EmailThreadStatus.SPAM)
    elif folder == "sent":
        stmt = stmt.where(EmailThread.status != EmailThreadStatus.SPAM)
    else:
        if status_filter:
            stmt = stmt.where(EmailThread.status == status_filter)
        else:
            stmt = stmt.where(
                EmailThread.status.notin_(
                    [EmailThreadStatus.ARCHIVED, EmailThreadStatus.SPAM]
                )
            )

    if search:
        stmt = stmt.where(
            (EmailThread.subject.ilike(f"%{search}%"))
            | (EmailThread.customer_email.ilike(f"%{search}%"))
            | (EmailThread.snippet.ilike(f"%{search}%"))
        )

    stmt = stmt.order_by(EmailThread.last_message_at.desc()).limit(limit).offset(offset)
    result = await db.scalars(stmt)
    return result.all()


@router.get("/threads/{thread_id}", response_model=EmailThreadResponse)
async def get_thread_detail(
    thread_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    stmt = (
        select(EmailThread)
        .options(selectinload(EmailThread.messages))
        .where(EmailThread.thread_id == thread_id)
    )
    thread = await db.scalar(stmt)
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )

    if thread.status == EmailThreadStatus.UNREAD:
        thread.status = EmailThreadStatus.READ
        await db.flush()

    return thread


@router.post("/compose", response_model=EmailThreadResponse)
async def compose_new_email(
    payload: EmailComposeRequest,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    mailbox = await db.scalar(
        select(EmailMailbox).where(EmailMailbox.mailbox_id == payload.mailbox_id)
    )
    if not mailbox:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Sender mailbox not found"
        )

    if mailbox.type == MailboxType.PERSONAL:
        if mailbox.owner_admin_id != admin.admin_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You cannot send emails from another admin's personal mailbox",
            )
    elif mailbox.type == MailboxType.SHARED:
        if (
            admin.role != AdminRole.SUPER_ADMIN
            and mailbox.allowed_admin_ids
            and str(admin.admin_id) not in [str(x) for x in mailbox.allowed_admin_ids]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to send from this shared mailbox",
            )

    resend_id = None
    
    try:
        send_res = resend_client.Emails.send(
            {
                "from": f"{mailbox.name} <{mailbox.email}>",
                "to": [payload.to_email],
                "subject": payload.subject,
                "html": payload.body,
            }
        )
        resend_id =  send_res.get("id", None)
    except Exception as e:
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )

    now = datetime.now(timezone.utc)
    new_thread = EmailThread(
        mailbox_id=mailbox.mailbox_id,
        customer_email=payload.to_email,
        to=mailbox.email,
        subject=payload.subject,
        snippet=(
            (payload.body[:150] + "...") if len(payload.body) > 150 else payload.body
        ),
        status=EmailThreadStatus.READ,
        last_message_at=now,
    )
    db.add(new_thread)
    await db.flush()
    await db.refresh(new_thread)

    new_message = EmailMessages(
        thread_id=new_thread.thread_id,
        resend_id=resend_id,
        recipients=payload.to_email,
        sender=mailbox.email,
        body=payload.body,
        direction="outgoing",
        created_at=now,
    )
    db.add(new_message)
    await db.flush()

    if resend_id:
        try:
            pool = await get_arq_pool()
            await pool.enqueue_job("sync_outgoing_email_message_id", resend_id)
        except Exception:
            pass

    recipient_mailbox = await db.scalar(
        select(EmailMailbox).where(EmailMailbox.email == payload.to_email.lower())
    )
    if recipient_mailbox:
        incoming_thread = EmailThread(
            mailbox_id=recipient_mailbox.mailbox_id,
            customer_email=mailbox.email,
            to=recipient_mailbox.email,
            subject=payload.subject,
            snippet=(
                (payload.body[:150] + "...")
                if len(payload.body) > 150
                else payload.body
            ),
            status=EmailThreadStatus.UNREAD,
            last_message_at=now,
        )
        db.add(incoming_thread)
        await db.flush()
        await db.refresh(incoming_thread)

        incoming_message = EmailMessages(
            thread_id=incoming_thread.thread_id,
            resend_id=resend_id,
            recipients=recipient_mailbox.email,
            sender=mailbox.email,
            body=payload.body,
            direction="incoming",
            created_at=now,
        )
        db.add(incoming_message)
        await db.flush()

    stmt = (
        select(EmailThread)
        .options(selectinload(EmailThread.messages))
        .where(EmailThread.thread_id == new_thread.thread_id)
    )
    return await db.scalar(stmt)


@router.post("/threads/{thread_id}/reply", response_model=EmailMessageResponse)
async def reply_to_thread(
    thread_id: uuid.UUID,
    payload: EmailMessageCreate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    thread = await db.scalar(
        select(EmailThread).where(EmailThread.thread_id == thread_id)
    )
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )

    sender_email = thread.to if thread.to else f"support@{settings.DOMAIN_NAME}"
    resend_id = None

    if hasattr(settings, "RESEND_API_KEY") and settings.RESEND_API_KEY:
        try:
            send_res = resend_client.Emails.send(
                {
                    "from": f"Kluda Support <{sender_email}>",
                    "to": [thread.customer_email],
                    "subject": (
                        f"Re: {thread.subject}"
                        if not thread.subject.startswith("Re:")
                        else thread.subject
                    ),
                    "html": payload.body,
                }
            )
            resend_id = (
                send_res.get("id")
                if isinstance(send_res, dict)
                else getattr(send_res, "id", None)
            )
        except Exception:
            pass

    now = datetime.now(timezone.utc)
    new_message = EmailMessages(
        thread_id=thread.thread_id,
        resend_id=resend_id,
        recipients=thread.customer_email,
        sender=sender_email,
        body=payload.body,
        direction="outgoing",
        created_at=now,
    )
    db.add(new_message)

    thread.snippet = (
        (payload.body[:150] + "...") if len(payload.body) > 150 else payload.body
    )
    thread.last_message_at = now
    await db.flush()
    await db.refresh(new_message)

    if resend_id:
        try:
            pool = await get_arq_pool()
            await pool.enqueue_job("sync_outgoing_email_message_id", resend_id)
        except Exception:
            pass

    return new_message


@router.put("/threads/{thread_id}/status")
async def update_thread_status(
    thread_id: uuid.UUID,
    status_val: EmailThreadStatus,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    thread = await db.scalar(
        select(EmailThread).where(EmailThread.thread_id == thread_id)
    )
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Thread not found"
        )

    thread.status = status_val
    await db.flush()
    return {"status": "ok", "message": "Thread status updated"}
