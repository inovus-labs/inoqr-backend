from app.models.user import User
from app.models.session import UserSession
from fastapi import Cookie, HTTPException, Depends
from app.config import SESSION_COOKIE_NAME
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.database import get_db
from app.utils.types import ErrorCode
import hashlib


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=SESSION_COOKIE_NAME),
) -> User:
    if session_token is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": ErrorCode.UNAUTHORIZED,
                "message": "Authentication required",
            },
        )
    stmt = select(UserSession).where(
        UserSession.session_token_hash
        == hashlib.sha256(session_token.encode("utf-8")).hexdigest(),
        UserSession.expires_at > func.current_timestamp(),
    )
    result = await db.execute(stmt)
    session: UserSession = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(
            status_code=401,
            detail={"code": ErrorCode.UNAUTHORIZED, "message": "Invalid session"},
        )
    stmt = select(User).where(User.id == session.user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=401,
            detail={
                "code": ErrorCode.UNAUTHORIZED,
                "message": "Invalid session",
            },
        )
    stmt = (
        update(UserSession)
        .where(UserSession.id == session.id)
        .values(last_used_at=func.current_timestamp())
    )
    await db.execute(stmt)
    return user
