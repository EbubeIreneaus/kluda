from sqlalchemy import Text
from sqlalchemy import JSON
from typing import Literal
from schemas.user import CustomerStatus
from pydantic import EmailStr
from .config import Base
from sqlalchemy.orm import MappedColumn, mapped_column, relationship
from sqlalchemy import DateTime, String, Enum, Integer, func, UUID, ForeignKey
from schemas.user import StaffStatus, StaffPermission
from datetime import datetime
import uuid

class Staff(Base):
    __tablename__ = "staffs"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    staff_id: MappedColumn[str] = mapped_column(String(10), nullable=False, unique=True)
    first_name: MappedColumn[str] = mapped_column(String(100), nullable=False)
    last_name: MappedColumn[str] = mapped_column(String(100), nullable=False)
    other_name: MappedColumn[str | None] = mapped_column(String(100), nullable=True)
    role: MappedColumn[str] = mapped_column(String(100))
    access_token: MappedColumn[str | None] = mapped_column(String(500), nullable=True, unique=True, index=True)
    last_login: MappedColumn[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    otp_token: MappedColumn[str | None] = mapped_column(String(255), unique=True, index=True)
    otp_expires_at: MappedColumn[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password: MappedColumn[str] = mapped_column(String(255), nullable=False)
    phone: MappedColumn[str | None] = mapped_column(String(100), nullable=True)
    email: MappedColumn[EmailStr] = mapped_column(String, nullable=False)
    permission: MappedColumn[list[StaffPermission]] = mapped_column(JSON)
    status: MappedColumn[StaffStatus] = mapped_column(Enum(StaffStatus), default=StaffStatus.ACTIVE)
    sessions: MappedColumn[list["StaffSession"]] = relationship(back_populates="staff", cascade="all, delete-orphan")
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class StaffSession(Base):
    __tablename__ = "staff_sessions"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    staff_id: MappedColumn[str] = mapped_column(String(10), ForeignKey("staffs.staff_id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash: MappedColumn[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    ip_address: MappedColumn[str | None] = mapped_column(String(50), nullable=True)
    user_agent: MappedColumn[str | None] = mapped_column(String(255), nullable=True)
    expired_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    staff: MappedColumn["Staff"] = relationship(back_populates="sessions")

class Customer(Base):
    __tablename__ = "customers"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    customer_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, unique=True)
    fullname: MappedColumn[str | None] = mapped_column(String(100), nullable=True)
    phone: MappedColumn[str | None] = mapped_column(String(100), nullable=True)
    address: MappedColumn[str | None] = mapped_column(String(100), nullable=True)
    email: MappedColumn[EmailStr] = mapped_column(String, nullable=False, unique=True)
    debts: MappedColumn[list['Debtor']] = relationship(back_populates="customer", cascade="all, delete-orphan")
    status: MappedColumn[CustomerStatus] = mapped_column(Enum(CustomerStatus), default=CustomerStatus.ACTIVE)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Debtor(Base):
    __tablename__ = "debtors"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    debtor_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4)
    customer_id: MappedColumn[str | None] = mapped_column(ForeignKey("customers.customer_id"), nullable=True)
    customer: MappedColumn['Customer'] = relationship()
    amount: MappedColumn[int] = mapped_column(Integer)
    note: MappedColumn[str | None] = mapped_column(Text, nullable=True)
    status: MappedColumn[Literal['paid', 'unpaid']] = mapped_column(String(10), default="unpaid")
    staff_note: MappedColumn[str | None] = mapped_column(String, nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_onupdate=func.now(), server_default=func.now())
    