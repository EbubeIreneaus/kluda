from datetime import datetime
from sqlalchemy.orm import MappedColumn, mapped_column
from models.config import Base
from sqlalchemy import Integer, Text, DateTime, String, Boolean, func


class FAQ(Base):
    __tablename__ = "faqs"

    id: MappedColumn[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    question: MappedColumn[str] = mapped_column(Text, nullable=False)
    answer: MappedColumn[str] = mapped_column(Text, nullable=False)
    category: MappedColumn[str] = mapped_column(String(50), default="general", index=True, nullable=False)
    display_order: MappedColumn[int] = mapped_column(Integer, default=0, nullable=False)
    is_published: MappedColumn[bool] = mapped_column(Boolean, default=True, server_default="true", nullable=False)
    created_at: MappedColumn[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: MappedColumn[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now()
    )
