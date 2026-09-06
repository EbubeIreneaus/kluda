from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class CatalogItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    barcode: Optional[str] = None
    category: str = Field(default="General", max_length=100)
    suggested_price: int = Field(default=0, ge=0, description="Price in kobo")
    cost_price: int = Field(default=0, ge=0, description="Estimated wholesale cost in kobo")
    unit_in: Literal["piece", "kg", "g", "litre", "ml", "pack", "carton", "dozen", "bag", "sachet"] = "piece"
    description: Optional[str] = None
    is_active: bool = True


class CatalogItemCreate(CatalogItemBase):
    pass


class CatalogItemUpdate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    suggested_price: Optional[int] = Field(None, ge=0)
    cost_price: Optional[int] = Field(None, ge=0)
    unit_in: Optional[Literal["piece", "kg", "g", "litre", "ml", "pack", "carton", "dozen", "bag", "sachet"]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class CatalogItemResponse(CatalogItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    template_id: int
    created_at: datetime
    updated_at: datetime


class PaginatedCatalogItemsResponse(BaseModel):
    items: list[CatalogItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class CatalogTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    slug: str = Field(..., min_length=1, max_length=150)
    description: Optional[str] = None
    icon: Optional[str] = "package"
    is_active: bool = True
    sort_order: int = 0


class CatalogTemplateCreate(CatalogTemplateBase):
    pass


class CatalogTemplateUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class CatalogTemplateResponse(CatalogTemplateBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_imports: int = 0
    total_items: int = 0
    created_at: datetime
    updated_at: datetime
