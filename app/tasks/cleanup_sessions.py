from app.models.session import UserSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, func
from app.database import AsyncSessionLocal
import asyncio


async def cleanup_expired_sessions(db: AsyncSession):
    stmt = delete(UserSession).where(UserSession.expires_at <= func.current_timestamp())
    result = await db.execute(stmt)
    return result.rowcount


async def main():
    async with AsyncSessionLocal() as db:
        deleted_count = await cleanup_expired_sessions(db)
        if deleted_count > 0:
            print(f"Deleted {deleted_count} expired sessions")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
