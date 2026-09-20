from fastapi.responses import RedirectResponse
from app.config import config


def validate_return_to(return_to: str) -> str:
    if not return_to.startswith("/") or return_to.startswith("//"):
        return "/"
    return return_to


def redirect_to_frontend(return_to: str, status_code: int = 302):
    return RedirectResponse(
        url=f"{config('FRONTEND_URL')}{return_to}", status_code=status_code
    )
