from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from app.models.qr_code import QrCode
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.utils.url import redirect_to_frontend

router = APIRouter(tags=["Resolver"])


@router.get("/r/{slug}/")
async def resolve_qr(slug: str, db: AsyncSession = Depends(get_db)):
    stmt = select(QrCode.destination).where(QrCode.slug == slug)

    result = await db.execute(stmt)
    destination_url = result.scalar_one_or_none()

    if destination_url is None:
        return redirect_to_frontend(
            "/?error=qr_not_found",
            status_code=302,
        )

    return RedirectResponse(
        url=destination_url,
        status_code=302,
    )
