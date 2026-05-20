"""FastAPI 依赖注入."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.database import get_db
from app.models.user import User
from sqlalchemy import select


DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    db: DbSession,
    authorization: str | None = Header(default=None),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise UnauthorizedError("missing or invalid Authorization header")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedError("invalid token")
    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError("user not found")
    if not user.is_active:
        raise UnauthorizedError("user disabled")
    return user


async def get_current_user_optional(
    db: DbSession,
    authorization: str | None = Header(default=None),
) -> User | None:
    if not authorization:
        return None
    try:
        return await get_current_user(db, authorization)
    except UnauthorizedError:
        return None


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
