from fastapi import APIRouter, Request, Depends, Query, Cookie
from authlib.integrations.base_client.errors import MismatchingStateError, OAuthError
from app.config import config
from app.auth.oauth import oauth
from app.auth.dependencies import get_current_user
from app.schemas.user import UserEnvelope
from app.schemas.error import ErrorResponse
from app.models.user import User
from app.database import get_db
from app.utils.url import validate_return_to, redirect_to_frontend
from app.auth.service import (
    get_or_create_user,
    create_session,
    discard_session,
    delete_user,
)
from app.utils.types import AuthProvider
from sqlalchemy.ext.asyncio import AsyncSession
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


@router.get("/login/google/", status_code=302)
async def login_with_google(request: Request, return_to: str = Query("/")):
    request.session["return_to"] = validate_return_to(return_to)
    redirect_uri = request.url_for("google_auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback/", status_code=302)
async def google_auth_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.google.authorize_access_token(request)
        profile: dict = token["userinfo"]
        user = await get_or_create_user(profile, AuthProvider.google, db)
        session_token = await create_session(user, db)

    except MismatchingStateError:
        logger.exception("Google authentication failed")
        return redirect_to_frontend("/?error=authentication_failed")

    except OAuthError:
        logger.exception("Google authentication failed")
        return redirect_to_frontend("/?error=authentication_failed")

    except Exception:
        logger.exception("Unexpected error during Google OAuth callback")
        return redirect_to_frontend("/?error=server_error")

    redirect = redirect_to_frontend(request.session.pop("return_to", "/"))
    redirect.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=session_token,
        secure=True,
        httponly=True,
        path="/",
        samesite="strict",
        max_age=604800,
    )
    return redirect


@router.get("/login/github/", status_code=302)
async def login_with_github(request: Request, return_to: str = Query("/")):
    request.session["return_to"] = validate_return_to(return_to)
    redirect_uri = request.url_for("github_auth_callback")
    return await oauth.github.authorize_redirect(
        request, redirect_uri, prompt="select_account"
    )


@router.get("/github/callback/", status_code=302)
async def github_auth_callback(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        token = await oauth.github.authorize_access_token(request)
        profile_response = await oauth.github.get("user", token=token)
        email_response = await oauth.github.get(
            "user/emails",
            token=token,
        )

        verified_email = None
        for item in email_response.json():
            if item["primary"] and item["verified"]:
                verified_email = item["email"]
                break
        if verified_email is None:
            return redirect_to_frontend("/?error=authentication_failed")

        profile: dict = profile_response.json()
        profile["email"] = verified_email
        user = await get_or_create_user(profile, AuthProvider.github, db)
        session_token = await create_session(user, db)
    except MismatchingStateError:
        logger.exception("GitHub authentication failed")
        return redirect_to_frontend("/?error=authentication_failed")

    except OAuthError:
        logger.exception("GitHub authentication failed")
        return redirect_to_frontend("/?error=authentication_failed")

    except Exception:
        logger.exception("Unexpected error during GitHub OAuth callback")
        return redirect_to_frontend("/?error=server_error")

    redirect = redirect_to_frontend(request.session.pop("return_to", "/"))
    redirect.set_cookie(
        key=config.SESSION_COOKIE_NAME,
        value=session_token,
        secure=True,
        httponly=True,
        path="/",
        samesite="strict",
        max_age=604800,
    )
    return redirect


@router.get(
    "/me/",
    response_model=UserEnvelope,
    status_code=200,
    responses={
        401: {"model": ErrorResponse},
    },
)
async def get_me(current_user: User = Depends(get_current_user)):
    return {"data": current_user, "message": "User Found"}


@router.post("/logout/", status_code=303)
async def logout(
    db: AsyncSession = Depends(get_db),
    session_token: str | None = Cookie(default=None, alias=config.SESSION_COOKIE_NAME),
):
    if session_token is not None:
        await discard_session(session_token, db)
    redirect = redirect_to_frontend("/", status_code=303)
    redirect.delete_cookie(key=config.SESSION_COOKIE_NAME, path="/")
    return redirect


@router.delete("/account/", status_code=303)
async def delete_account(
    current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    await delete_user(current_user, db)
    redirect = redirect_to_frontend("/", status_code=303)
    redirect.delete_cookie(key=config.SESSION_COOKIE_NAME, path="/")
    return redirect
