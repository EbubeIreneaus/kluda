from typing import TYPE_CHECKING
from sqlalchemy.orm import MappedColumn, mapped_column, relationship
from models.config import Base
from sqlalchemy import Integer, Text, DateTime, String, Enum, Boolean, func
from datetime import datetime
from schemas.subscription import PlanStatus

if TYPE_CHECKING:
    from models.subscription import UserSubscription

class Plan(Base):
    __tablename__ = "subscription_plans"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    slug: MappedColumn[str] = mapped_column(String(50), unique=True, index=True)
    name: MappedColumn[str] = mapped_column(Text, unique=True, index=True)
    description: MappedColumn[str] = mapped_column(Text)
    subscriptions: MappedColumn[list["UserSubscription"]] = relationship(back_populates="plan")
    # this is the permissions 
    store_limit: MappedColumn[int | None] = mapped_column(Integer, nullable=True, default=0)
    product_limit: MappedColumn[int | None] = mapped_column(Integer, nullable=True, default=0)
    sales_limit_per_month: MappedColumn[int | None] = mapped_column(Integer, nullable=True, default=0)
    analytics_read_per_month: MappedColumn[int | None] = mapped_column(Integer, nullable=True, default=0)
    
    price: MappedColumn[int] = mapped_column(Integer, nullable=False)
    interval: MappedColumn[str] = mapped_column(String(20), default="monthly", nullable=False)
    has_trial: MappedColumn[bool] = mapped_column(Boolean, default=False, server_default="false", nullable=False)
    trial_duration_days: MappedColumn[int | None] = mapped_column(Integer, default=0, server_default="0", nullable=True)
    status: MappedColumn[PlanStatus] = mapped_column(Enum(PlanStatus), default=PlanStatus.AVAILABLE)
    paystack_planid: MappedColumn[str | None] = mapped_column(String, nullable=True)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now())

    