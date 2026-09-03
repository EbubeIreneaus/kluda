from datetime import datetime
from pydantic import BaseModel, ConfigDict


class FAQBase(BaseModel):
    question: str
    answer: str
    category: str = "general"
    display_order: int = 0
    is_published: bool = True


class FAQCreate(FAQBase):
    pass


class FAQUpdate(BaseModel):
    question: str | None = None
    answer: str | None = None
    category: str | None = None
    display_order: int | None = None
    is_published: bool | None = None


class FAQResponse(FAQBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
