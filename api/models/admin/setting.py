from sqlalchemy import DateTime, String, Integer, func, UUID, JSON
from sqlalchemy.orm import MappedColumn, mapped_column
from ..config import Base
from datetime import datetime
import uuid


class SystemSetting(Base):
    __tablename__ = "system_settings"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    key: MappedColumn[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    value: MappedColumn[dict] = mapped_column(JSON, nullable=False, default=dict)
    description: MappedColumn[str | None] = mapped_column(String(255), nullable=True)
    updated_by: MappedColumn[uuid.UUID | None] = mapped_column(UUID, nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
