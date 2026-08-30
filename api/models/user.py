from typing import TYPE_CHECKING
from sqlalchemy import Text
from sqlalchemy import JSON
from typing import Literal
from schemas.user import CustomerStatus
from pydantic import EmailStr
from .config import Base
from sqlalchemy.orm import MappedColumn, mapped_column, relationship
from sqlalchemy import DateTime, String, Enum, Integer, func, UUID, ForeignKey, Boolean
from schemas.user import StaffStatus, StaffPermission, UserStatus
from datetime import datetime
import uuid

if TYPE_CHECKING:
    from .business import Store

class User(Base):
    __tablename__ = "users"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    user_id: MappedColumn[uuid.UUID] = mapped_column(UUID,  default=uuid.uuid4, index=True, unique=True)
    fullname: MappedColumn[str] = mapped_column(String)
    email: MappedColumn[EmailStr] = mapped_column(String, unique=True, index=True)
    phone: MappedColumn[str | None] = mapped_column(String(15), nullable=True)
    access_token: MappedColumn[str | None] = mapped_column(String(500), nullable=True, unique=True, index=True)
    last_login: MappedColumn[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    otp_token: MappedColumn[str | None] = mapped_column(String(255), unique=True, index=True)
    otp_expires_at: MappedColumn[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    password: MappedColumn[str] = mapped_column(String(255), nullable=False)
    notification_subscription: MappedColumn[list['UserNotificationSubscription']] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    stores: MappedColumn[list['Store']] = relationship(back_populates="user")
    status: MappedColumn[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE)
    sessions: MappedColumn[list["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class UserSession(Base):
    __tablename__ = "user_sessions"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    session_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, unique=True, index=True)
    user_id: MappedColumn[uuid.UUID] = mapped_column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash: MappedColumn[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    ip_address: MappedColumn[str | None] = mapped_column(String(50), nullable=True)
    user_agent: MappedColumn[str | None] = mapped_column(String(255), nullable=True)
    active: MappedColumn[bool] = mapped_column(Boolean, default=True)
    expired_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: MappedColumn["User"] = relationship(back_populates="sessions")


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
    pin_hash: MappedColumn[str | None] = mapped_column(String(255), nullable=True)
    pin_salt: MappedColumn[str | None] = mapped_column(String(64), nullable=True)
    phone: MappedColumn[str | None] = mapped_column(String(100), nullable=True)
    store_id: MappedColumn[uuid.UUID] = mapped_column(ForeignKey("stores.store_id", ondelete="CASCADE"), index=True)
    store: MappedColumn["Store"] = relationship(back_populates="staffs")
    email: MappedColumn[EmailStr] = mapped_column(String, nullable=False)
    permission: MappedColumn[list[StaffPermission]] = mapped_column(JSON)
    status: MappedColumn[StaffStatus] = mapped_column(Enum(StaffStatus), default=StaffStatus.ACTIVE)
    sessions: MappedColumn[list["StaffSession"]] = relationship(back_populates="staff", cascade="all, delete-orphan")
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def has_pin(self) -> bool:
        return bool(self.pin_hash)


class StaffSession(Base):
    __tablename__ = "staff_sessions"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    session_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, index=True, unique=True)
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
    store_id: MappedColumn[uuid.UUID] = mapped_column(ForeignKey("stores.store_id", ondelete="CASCADE"), index=True)
    store: MappedColumn['Store'] = relationship(back_populates="customers")
    fullname: MappedColumn[str | None] = mapped_column(String(100), nullable=True)
    phone: MappedColumn[str | None] = mapped_column(String(100), nullable=True)
    address: MappedColumn[str | None] = mapped_column(String(100), nullable=True)
    email: MappedColumn[EmailStr] = mapped_column(String, nullable=False, unique=True)
    debts: MappedColumn[list['Debt']] = relationship(back_populates="customer", cascade="all, delete-orphan")
    status: MappedColumn[CustomerStatus] = mapped_column(Enum(CustomerStatus), default=CustomerStatus.ACTIVE)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class Debt(Base):
    __tablename__ = "debt"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    debt_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4)
    customer_id: MappedColumn[str | None] = mapped_column(ForeignKey("customers.customer_id"), nullable=True)
    customer: MappedColumn['Customer'] = relationship()
    amount: MappedColumn[int] = mapped_column(Integer)
    note: MappedColumn[str | None] = mapped_column(Text, nullable=True)
    status: MappedColumn[Literal['paid', 'unpaid']] = mapped_column(String(10), default="unpaid")
    staff_note: MappedColumn[str | None] = mapped_column(String, nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_onupdate=func.now(), server_default=func.now())

class StaffNotificationSubscription(Base):
    __tablename__ = "staff_notification_subscriptions"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    staff_id: MappedColumn[str] = mapped_column(String(100), nullable=False, index=True)
    sub_info: MappedColumn[dict] = mapped_column(JSON)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class UserNotificationSubscription(Base):
    __tablename__ = "owner_notification_subscriptions"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    user_id: MappedColumn[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    user: MappedColumn['User'] = relationship(back_populates="notification_subscription")
    sub_info: MappedColumn[dict] = mapped_column(JSON)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    
    