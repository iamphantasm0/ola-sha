import uuid
from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import decode_token
from app.models.user import User


def _token_from_header(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return parts[1]
    return None


async def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = _token_from_header(authorization)
    user_id = decode_token(token) if token else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        user = await db.get(User, uuid.UUID(user_id))
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_optional_user(
    authorization: Optional[str] = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Like get_current_user but returns None instead of 401 — for routes that work
    both logged-in and anonymous (e.g. chat)."""
    token = _token_from_header(authorization)
    user_id = decode_token(token) if token else None
    if not user_id:
        return None
    try:
        return await db.get(User, uuid.UUID(user_id))
    except (ValueError, TypeError):
        return None
