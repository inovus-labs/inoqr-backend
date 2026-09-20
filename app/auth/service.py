import secrets
import hashlib
from app.models.user import User
from app.models.session import UserSession
from app.utils.types import AuthProvider
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone


async def get_or_create_user(
    profile: dict, provider: AuthProvider, db: AsyncSession
) -> User:
    if provider == AuthProvider.google:
        name = profile["name"]
        provider_user_id = profile["sub"]
        email = profile["email"]
        image_url = profile["picture"]
    elif provider == AuthProvider.github:
        name = profile["name"]
        provider_user_id = str(profile["id"])
        email = profile["email"]
        image_url = profile["avatar_url"]

    stmt = select(User).where(
        User.provider == provider, User.provider_user_id == provider_user_id
    )
    result = await db.execute(stmt)
    exsisting_user = result.scalars().first()
    if exsisting_user:
        return exsisting_user
    new_user = User(
        name=name,
        provider=provider,
        provider_user_id=provider_user_id,
        email=email,
        image_url=image_url,
    )
    db.add(new_user)
    await db.flush()
    return new_user


async def delete_user(current_user: User, db: AsyncSession) -> None:
    stmt = delete(User).where(User.id == current_user.id)
    await db.execute(stmt)


async def create_session(user: User, db: AsyncSession) -> str:
    session_token = secrets.token_urlsafe(32)
    session_token_hash = hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    new_session = UserSession(
        user_id=user.id,
        session_token_hash=session_token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(new_session)
    await db.flush()
    return session_token


async def discard_session(session_token: str, db: AsyncSession) -> None:
    stmt = delete(UserSession).where(
        UserSession.session_token_hash
        == hashlib.sha256(session_token.encode("utf-8")).hexdigest()
    )
    await db.execute(stmt)
