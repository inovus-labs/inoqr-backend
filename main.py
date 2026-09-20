from fastapi import FastAPI
import logging
from starlette.middleware.sessions import SessionMiddleware as OAuthMiddleware
from app.config import config
from app.routers import auth
from fastapi import HTTPException
from starlette.exceptions import HTTPException as StareletteHttpException
from app.logger import setup_logging
from fastapi.exceptions import RequestValidationError
from app.exceptions import (
    fhttp_exception_handler,
    validation_exception_handler,
    shttp_exception_handler,
    internal_server_error_handler,
)

setup_logging()

app = FastAPI()
app.add_middleware(OAuthMiddleware, secret_key=config("SECRET_KEY"))
app.add_exception_handler(HTTPException, fhttp_exception_handler)
app.add_exception_handler(StareletteHttpException, shttp_exception_handler)
app.add_exception_handler(Exception, internal_server_error_handler)
app.add_exception_handler(
    RequestValidationError,
    validation_exception_handler,
)

app.include_router(auth.router)

if __name__ == "__main__":
    import uvicorn as uv

    logging.getLogger(__name__).info("Application has Started")

    uv.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_excludes=["**/logs/*"],
    )
