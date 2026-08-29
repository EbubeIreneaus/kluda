from pydantic import BaseModel
from models.admin.ticket import TicketStatus, TicketPriority, TicketType
from datetime import datetime
import uuid


class SupportTicketCreate(BaseModel):
    store_id: uuid.UUID | None = None
    reporter_type: str = "staff"
    reporter_id: uuid.UUID
    type: TicketType = TicketType.BUG
    subject: str
    description: str
    device_diagnostics: dict | None = None
    priority: TicketPriority = TicketPriority.MEDIUM


class SupportTicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    assigned_admin_id: uuid.UUID | None = None
    resolution_notes: str | None = None


class SupportTicketResponse(BaseModel):
    id: int
    ticket_id: uuid.UUID
    store_id: uuid.UUID | None = None
    reporter_type: str
    reporter_id: uuid.UUID
    type: TicketType
    subject: str
    description: str
    device_diagnostics: dict | None = None
    status: TicketStatus
    priority: TicketPriority
    assigned_admin_id: uuid.UUID | None = None
    resolution_notes: str | None = None
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
