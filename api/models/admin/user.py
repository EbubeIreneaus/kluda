from pydantic import EmailStr
from ..config import Base
from sqlalchemy.orm import MappedColumn, mapped_column, relationship
from sqlalchemy import DateTime, String, Enum, Integer, func, UUID, ForeignKey, Boolean, JSON
from datetime import datetime
import uuid
from schemas.admin.user import AdminPermission, AdminStatus, AdminRole


class Admin(Base):
    __tablename__ = "admins"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    admin_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, index=True, unique=True)
    fullname: MappedColumn[str] = mapped_column(String(255), nullable=False)
    company_email: MappedColumn[EmailStr] = mapped_column(String(255), unique=True, index=True, nullable=False)
    personal_email: MappedColumn[EmailStr] = mapped_column(String(255), unique=True, index=True, nullable=False)
    phone: MappedColumn[str | None] = mapped_column(String(20), nullable=True)
    last_login: MappedColumn[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    otp_token: MappedColumn[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    otp_expires_at: MappedColumn[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password: MappedColumn[str] = mapped_column(String(255), nullable=False)
    role: MappedColumn[AdminRole] = mapped_column(Enum(AdminRole), default=AdminRole.MODERATOR)
    permission: MappedColumn[list[AdminPermission]] = mapped_column(JSON, default=list)
    status: MappedColumn[AdminStatus] = mapped_column(Enum(AdminStatus), default=AdminStatus.ACTIVE)
    sessions: MappedColumn[list["AdminSession"]] = relationship(back_populates="admin", cascade="all, delete-orphan")
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AdminSession(Base):
    __tablename__ = "admin_sessions"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    session_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, unique=True, index=True)
    admin_id: MappedColumn[uuid.UUID] = mapped_column(UUID, ForeignKey("admins.admin_id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token_hash: MappedColumn[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    ip_address: MappedColumn[str | None] = mapped_column(String(50), nullable=True)
    user_agent: MappedColumn[str | None] = mapped_column(String(255), nullable=True)
    active: MappedColumn[bool] = mapped_column(Boolean, default=True)
    expired_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    admin: MappedColumn["Admin"] = relationship(back_populates="sessions")
