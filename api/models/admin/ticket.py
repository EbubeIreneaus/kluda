from enum import Enum as TypeEnum
from sqlalchemy import Text, DateTime, String, Enum, Integer, func, UUID, ForeignKey, JSON
from sqlalchemy.orm import MappedColumn, mapped_column
from ..config import Base
from datetime import datetime
import uuid


class TicketStatus(str, TypeEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class TicketPriority(str, TypeEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketType(str, TypeEnum):
    BUG = "bug"
    HARDWARE = "hardware"
    FEATURE = "feature"
    GENERAL = "general"


class SupportTicket(Base):
    __tablename__ = "support_tickets"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    ticket_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, index=True, unique=True)
    store_id: MappedColumn[uuid.UUID | None] = mapped_column(UUID, ForeignKey("stores.store_id", ondelete="SET NULL"), nullable=True, index=True)
    reporter_type: MappedColumn[str] = mapped_column(String(20), nullable=False, index=True)
    reporter_id: MappedColumn[uuid.UUID] = mapped_column(UUID, nullable=False, index=True)
    type: MappedColumn[TicketType] = mapped_column(Enum(TicketType), default=TicketType.BUG, index=True)
    subject: MappedColumn[str] = mapped_column(String(255), nullable=False)
    description: MappedColumn[str] = mapped_column(Text, nullable=False)
    device_diagnostics: MappedColumn[dict | None] = mapped_column(JSON, nullable=True)
    status: MappedColumn[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.OPEN, index=True)
    priority: MappedColumn[TicketPriority] = mapped_column(Enum(TicketPriority), default=TicketPriority.MEDIUM, index=True)
    assigned_admin_id: MappedColumn[uuid.UUID | None] = mapped_column(UUID, ForeignKey("admins.admin_id", ondelete="SET NULL"), nullable=True, index=True)
    resolution_notes: MappedColumn[str | None] = mapped_column(Text, nullable=True)
    resolved_at: MappedColumn[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
