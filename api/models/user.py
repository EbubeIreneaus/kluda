from typing import TYPE_CHECKING, Any
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
    from .subscription import UserSubscription

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
    subscriptions: MappedColumn[list["UserSubscription"]] = relationship(
        "UserSubscription",
        back_populates="user",
        foreign_keys="UserSubscription.user_id",
        cascade="all, delete-orphan",
    )
    current_subscription_id: MappedColumn[uuid.UUID | None] = mapped_column(
        ForeignKey("user_subscriptions.subscription_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    current_subscription: MappedColumn["UserSubscription | None"] = relationship(
        "UserSubscription",
        foreign_keys=[current_subscription_id],
        post_update=True,
    )
    pin_hash: MappedColumn[str | None] = mapped_column(String(255), nullable=True)
    pin_salt: MappedColumn[str | None] = mapped_column(String(64), nullable=True)
    notification_subscription: MappedColumn[list['NotificationSubscription']] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    stores: MappedColumn[list['Store']] = relationship(back_populates="user")
    memberships: MappedColumn[list['StoreMember']] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    
    status: MappedColumn[UserStatus] = mapped_column(Enum(UserStatus), default=UserStatus.ACTIVE)
    sessions: MappedColumn[list["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    paystack_customer_code: MappedColumn[str | None] = mapped_column(String(100), unique=True, index=True, nullable=True)
    paystack_authorization: MappedColumn[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    referral_code: MappedColumn[str | None] = mapped_column(String(30), unique=True, index=True, nullable=True)
    referred_by_id: MappedColumn[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    referred_by: MappedColumn["User | None"] = relationship("User", remote_side=[id], foreign_keys=[referred_by_id])

    has_used_trial: MappedColumn[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)


class StoreMember(Base):
    __tablename__ = "store_members"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    store_id: MappedColumn[uuid.UUID] = mapped_column(ForeignKey("stores.store_id", ondelete="CASCADE"), index=True)
    user_id: MappedColumn[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    role: MappedColumn[str] = mapped_column(String(50), default="cashier")
    display_name: MappedColumn[str | None] = mapped_column(String(100), nullable=True)
    permission: MappedColumn[list[StaffPermission]] = mapped_column(JSON, default=list)
    status: MappedColumn[StaffStatus] = mapped_column(Enum(StaffStatus), default=StaffStatus.ACTIVE)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    store: MappedColumn["Store"] = relationship(back_populates="members")
    user: MappedColumn["User"] = relationship(back_populates="memberships")

Staff = StoreMember

class UserSession(Base):
    __tablename__ = "user_sessions"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    session_id: MappedColumn[uuid.UUID] = mapped_column(UUID, default=uuid.uuid4, unique=True, index=True)
    user_id: MappedColumn[uuid.UUID] = mapped_column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    refresh_token_hash: MappedColumn[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    previous_refresh_token_hash: MappedColumn[str | None] = mapped_column(String(64), nullable=True, index=True)
    ip_address: MappedColumn[str | None] = mapped_column(String(50), nullable=True)
    user_agent: MappedColumn[str | None] = mapped_column(String(255), nullable=True)
    active: MappedColumn[bool] = mapped_column(Boolean, default=True)
    expired_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: MappedColumn["User"] = relationship(back_populates="sessions")


    @property
    def has_pin(self) -> bool:
        return bool(self.pin_hash)

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

class NotificationSubscription(Base):
    __tablename__ = "notification_subscriptions"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    user_id: MappedColumn[uuid.UUID] = mapped_column(ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    user: MappedColumn['User'] = relationship(back_populates="notification_subscription")
    sub_info: MappedColumn[dict] = mapped_column(JSON)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


UserNotificationSubscription = NotificationSubscription

    
    