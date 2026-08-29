import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.config import get_db
from models.admin.ticket import SupportTicket
from models.admin.user import Admin
from schemas.admin.ticket import SupportTicketCreate, SupportTicketUpdate, SupportTicketResponse, TicketStatus, TicketPriority
from schemas.admin.user import AdminPermission
from libs.deps import require_admin_permission, get_admin
from libs.audit import record_audit_log


router = APIRouter(prefix="/tickets", tags=["Admin Support Tickets"])


@router.get("", response_model=list[SupportTicketResponse])
async def list_tickets(
    status_filter: str | None = Query(None, alias="status"),
    priority_filter: str | None = Query(None, alias="priority"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    stmt = select(SupportTicket)
    if status_filter:
        stmt = stmt.where(SupportTicket.status == status_filter)
    if priority_filter:
        stmt = stmt.where(SupportTicket.priority == priority_filter)

    stmt = stmt.order_by(SupportTicket.created_at.desc()).limit(limit).offset(offset)
    result = await db.scalars(stmt)
    return result.all()


@router.post("", response_model=SupportTicketResponse)
async def create_support_ticket(
    payload: SupportTicketCreate,
    db: AsyncSession = Depends(get_db),
):
    new_ticket = SupportTicket(
        reporter_type=payload.reporter_type,
        reporter_id=payload.reporter_id,
        store_id=payload.store_id,
        type=payload.type,
        subject=payload.subject,
        description=payload.description,
        priority=payload.priority,
        status=TicketStatus.OPEN,
        device_diagnostics=payload.device_diagnostics,
    )
    db.add(new_ticket)
    await db.flush()
    await db.refresh(new_ticket)
    return new_ticket


@router.get("/{ticket_id}", response_model=SupportTicketResponse)
async def get_ticket_detail(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(get_admin),
):
    ticket = await db.scalar(select(SupportTicket).where(SupportTicket.ticket_id == ticket_id))
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    return ticket


@router.put("/{ticket_id}", response_model=SupportTicketResponse)
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: SupportTicketUpdate,
    db: AsyncSession = Depends(get_db),
    admin: Admin = Depends(require_admin_permission(AdminPermission.MANAGE_SUPPORT)),
):
    ticket = await db.scalar(select(SupportTicket).where(SupportTicket.ticket_id == ticket_id))
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    if payload.status is not None:
        ticket.status = payload.status
        if payload.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            ticket.resolved_at = datetime.now(timezone.utc)
    if payload.priority is not None:
        ticket.priority = payload.priority
    if payload.assigned_admin_id is not None:
        ticket.assigned_admin_id = payload.assigned_admin_id
    if payload.resolution_notes is not None:
        ticket.resolution_notes = payload.resolution_notes

    await db.flush()
    await db.refresh(ticket)

    await record_audit_log(
        db=db,
        admin_id=admin.admin_id,
        action="TICKET_UPDATED",
        target_type="ticket",
        target_id=ticket.ticket_id,
        details={"status": ticket.status.value, "priority": ticket.priority.value},
    )
    return ticket
