from sqlalchemy import Text, JSON, DateTime, String, Enum, Integer, func, UUID, ForeignKey
from sqlalchemy.orm import MappedColumn, mapped_column
from schemas.notification import NotificationScope
from .config import Base
from datetime import datetime
import uuid


class Notification(Base):
    __tablename__ = "notifications"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    notification_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, index=True, unique=True)
    scope: MappedColumn[NotificationScope] = mapped_column(Enum(NotificationScope), default=NotificationScope.PERSONAL, index=True)
    target_id: MappedColumn[uuid.UUID | None] = mapped_column(UUID, nullable=True, index=True)
    title: MappedColumn[str] = mapped_column(String(255), nullable=False)
    message: MappedColumn[str] = mapped_column(Text, nullable=False)
    data: MappedColumn[dict | None] = mapped_column(JSON, nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class NotificationRead(Base):
    __tablename__ = "notification_reads"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    user_id: MappedColumn[uuid.UUID] = mapped_column(UUID, nullable=False, index=True)
    notification_id: MappedColumn[uuid.UUID] = mapped_column(UUID, ForeignKey("notifications.notification_id", ondelete="CASCADE"), nullable=False, index=True)
    read_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
