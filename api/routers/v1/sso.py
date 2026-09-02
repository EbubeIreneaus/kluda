from datetime import datetime, timezone, timedelta
import secrets
import time
import uuid
from typing import Annotated
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from models.config import get_db
from models.user import User, UserSession
from models.business import Store
from schemas.user import UserResponseMini
from schemas.business import StoreResponseMini
from libs.security import (
    create_access_token,
    hash_token,
    generate_refresh_token,
    get_cookie_settings,
    get_client_ip,
)
from libs.deps import get_staff, get_user

router = APIRouter(prefix="/auth/sso", tags=["SSO"])

sso_tickets: dict[str, dict] = {}


def prune_expired_tickets():
    now = time.time()
    expired = [k for k, v in sso_tickets.items() if v.get("expires_at", 0) < now]
    for k in expired:
        sso_tickets.pop(k, None)


class SSOExchangeRequest(BaseModel):
    ticket: str


class SSOTicketResponse(BaseModel):
    ticket: str
    expires_in: int


@router.post("/ticket", response_model=SSOTicketResponse)
async def generate_sso_ticket(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    prune_expired_tickets()
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to generate SSO ticket"
        )

    token = auth_header.split(" ")[1]
    ticket = f"sso_{secrets.token_urlsafe(32)}"
    expires_at = time.time() + 60

    user = await get_user(request=request, token=token, db=db)
    sso_tickets[ticket] = {
        "type": "user",
        "user_id": str(user.user_id),
        "email": user.email,
        "expires_at": expires_at
    }
    return {"ticket": ticket, "expires_in": 60}


@router.post("/exchange")
async def exchange_sso_ticket(
    body: SSOExchangeRequest,
    request: Request,
    response: Response,
    user_agent: Annotated[str | None, Header()] = None,
    db: AsyncSession = Depends(get_db),
):
    prune_expired_tickets()
    ticket_data = sso_tickets.pop(body.ticket, None)

    if not ticket_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired SSO ticket"
        )

    if ticket_data.get("expires_at", 0) < time.time():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SSO ticket has expired"
        )

    user_id_str = ticket_data.get("user_id")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No associated owner account found for this ticket"
        )

    target_user_id = uuid.UUID(user_id_str)
    result = await db.execute(
        select(User)
        .options(selectinload(User.stores))
        .where(User.user_id == target_user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Associated owner account not found"
        )

    now = datetime.now(timezone.utc)
    user.last_login = now

    raw_refresh_token = generate_refresh_token()
    r_hash = hash_token(raw_refresh_token)
    access_token_expired_at = now + timedelta(hours=1)
    refresh_token_expired_at = now + timedelta(days=30)
    client_ip = get_client_ip(request)

    new_session = UserSession(
        user_id=user.user_id,
        refresh_token_hash=r_hash,
        ip_address=client_ip,
        user_agent=user_agent,
        expired_at=refresh_token_expired_at,
    )
    db.add(new_session)
    await db.flush()

    token_payload = {
        "sub": str(user.user_id),
        "session_id": str(new_session.session_id),
    }
    access_token = create_access_token(
        token_payload, expires_delta=timedelta(hours=1)
    )
    user_payload = UserResponseMini.model_validate(user).model_dump(mode="json")
    from routers.v1.auth import get_user_stores
    stores_payload = await get_user_stores(user.user_id, db)

    await db.commit()

    cookie_settings = get_cookie_settings()
    response.set_cookie(
        key="refresh_token",
        value=raw_refresh_token,
        expires=refresh_token_expired_at,
        **cookie_settings,
    )

    return {
        "success": True,
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "user": user_payload,
        "stores": stores_payload,
    }
