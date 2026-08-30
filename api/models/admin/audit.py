from sqlalchemy import DateTime, String, Integer, func, UUID, ForeignKey, JSON
from sqlalchemy.orm import MappedColumn, mapped_column, relationship
from ..config import Base
from datetime import datetime
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import Admin


class AdminAuditLog(Base):
    __tablename__ = "admin_audit_logs"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    log_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, index=True, unique=True)
    admin_id: MappedColumn[uuid.UUID | None] = mapped_column(UUID, ForeignKey("admins.admin_id", ondelete="SET NULL"), nullable=True, index=True)
    action: MappedColumn[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: MappedColumn[str] = mapped_column(String(50), nullable=False, index=True)
    target_id: MappedColumn[uuid.UUID | None] = mapped_column(UUID, nullable=True, index=True)
    details: MappedColumn[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: MappedColumn[str | None] = mapped_column(String(50), nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    admin: MappedColumn["Admin | None"] = relationship("Admin", foreign_keys=[admin_id], lazy="selectin")
