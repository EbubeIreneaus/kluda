from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.config import get_db
from models.faq import FAQ
from schemas.faq import FAQResponse
from libs.cache import get_cache, set_cache

router = APIRouter(prefix="/faqs", tags=["FAQs"])

CACHE_KEY_PUBLIC_FAQS = "kluda:cache:public_faqs"


@router.get("", response_model=List[FAQResponse])
async def list_public_faqs(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all published FAQs. Cached in Redis for sub-millisecond retrieval."""
    cache_key = f"{CACHE_KEY_PUBLIC_FAQS}:{category or 'all'}"
    cached_data = await get_cache(cache_key)
    if cached_data is not None:
        return cached_data

    query = select(FAQ).where(FAQ.is_published.is_(True))
    if category:
        query = query.where(FAQ.category == category)

    query = query.order_by(FAQ.display_order.asc(), FAQ.id.asc())
    result = await db.scalars(query)
    faqs = result.all()

    response_data = [FAQResponse.model_validate(f).model_dump(mode="json") for f in faqs]
    # Cache in Redis for 1 hour
    await set_cache(cache_key, response_data, expire_seconds=3600)

    return response_data
