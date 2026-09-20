from app.models.session import UserSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, func
from app.database import AsyncSessionLocal
import asyncio


async def cleanup_expired_sessions(db: AsyncSession):
    stmt = delete(UserSession).where(UserSession.expires_at <= func.current_timestamp())
    await db.execute(stmt)


async def main():
    async with AsyncSessionLocal() as db:
        result = await cleanup_expired_sessions(db)
        print(f"Deleted {result.rowcount} expired sessions")
        await db.commit()


if __name__ == "__main__":
    asyncio.run(main())
