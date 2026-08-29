from sqlalchemy import DateTime, Integer, func, BigInteger
from sqlalchemy.orm import MappedColumn, mapped_column
from ..config import Base
from datetime import datetime


class DailyPlatformMetric(Base):
    __tablename__ = "daily_platform_metrics"
    id: MappedColumn[int] = mapped_column(Integer, primary_key=True)
    date: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), unique=True, index=True, nullable=False)
    total_stores: MappedColumn[int] = mapped_column(Integer, default=0)
    active_stores: MappedColumn[int] = mapped_column(Integer, default=0)
    total_sales_count: MappedColumn[int] = mapped_column(Integer, default=0)
    total_revenue_amount: MappedColumn[int] = mapped_column(BigInteger, default=0)
    total_offline_synced_sales: MappedColumn[int] = mapped_column(Integer, default=0)
    new_users_registered: MappedColumn[int] = mapped_column(Integer, default=0)
    new_staff_created: MappedColumn[int] = mapped_column(Integer, default=0)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
