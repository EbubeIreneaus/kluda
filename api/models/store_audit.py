from sqlalchemy import DateTime, String, Integer, func, UUID, ForeignKey, JSON
from sqlalchemy.orm import MappedColumn, mapped_column, relationship
from .config import Base
from datetime import datetime
import uuid
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .business import Store


class StoreAuditLog(Base):
    __tablename__ = "store_audit_logs"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    log_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, index=True, unique=True)
    store_id: MappedColumn[uuid.UUID] = mapped_column(UUID, ForeignKey("stores.store_id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id: MappedColumn[uuid.UUID | None] = mapped_column(UUID, ForeignKey("users.user_id", ondelete="SET NULL"), nullable=True, index=True)
    actor_name: MappedColumn[str | None] = mapped_column(String(150), nullable=True)
    actor_email: MappedColumn[str | None] = mapped_column(String(150), nullable=True)
    actor_role: MappedColumn[str | None] = mapped_column(String(50), nullable=True)
    action: MappedColumn[str] = mapped_column(String(100), nullable=False, index=True)
    target_type: MappedColumn[str] = mapped_column(String(50), nullable=False, index=True)
    target_id: MappedColumn[str | None] = mapped_column(String(150), nullable=True, index=True)
    target_name: MappedColumn[str | None] = mapped_column(String(255), nullable=True)
    details: MappedColumn[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: MappedColumn[str | None] = mapped_column(String(50), nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

    store: MappedColumn["Store"] = relationship("Store", foreign_keys=[store_id], lazy="selectin")
    actor: MappedColumn["User | None"] = relationship("User", foreign_keys=[actor_id], lazy="selectin")
