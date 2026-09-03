from schemas.subscription import PaymentChannel
from sqlalchemy.orm import MappedColumn, mapped_column, relationship
from models.config import Base
from sqlalchemy import UUID, Integer, Text, DateTime, String, Enum, ForeignKey, Boolean, func
from datetime import datetime
import uuid
from schemas.subscription import SubscriptionStatus
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models.admin.plan import Plan
    from models.user import User

class UserSubscription(Base):
    __tablename__ = "user_subscriptions"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    subscription_id: MappedColumn[uuid.UUID] = mapped_column(UUID, unique=True, index=True, default=uuid.uuid4)
    user_id: MappedColumn[uuid.UUID] = mapped_column(UUID, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    user: MappedColumn["User"] = relationship("User", back_populates="subscriptions", foreign_keys=[user_id])
    plan_id: MappedColumn[str] = mapped_column(ForeignKey("subscription_plans.slug"), index=True)
    plan: MappedColumn["Plan"] = relationship("Plan", back_populates="subscriptions")
    status: MappedColumn[SubscriptionStatus] = mapped_column(Enum(SubscriptionStatus), default=SubscriptionStatus.DUE)
    amount: MappedColumn[int] = mapped_column(Integer, nullable=False)
    is_trial: MappedColumn[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    reference: MappedColumn[str | None] = mapped_column(String, unique=True, index=True)
    idempotency_key: MappedColumn[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    paystack_subscription_code: MappedColumn[str | None] = mapped_column(String(100), index=True, nullable=True)
    payment_channel: MappedColumn[PaymentChannel] = mapped_column(Enum(PaymentChannel), default=PaymentChannel.PAYSTACK)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now())
    next_renewal: MappedColumn[datetime] = mapped_column(DateTime(timezone=True))
    analytics_used: MappedColumn[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    description: MappedColumn[str | None] = mapped_column(Text, nullable=True)

    