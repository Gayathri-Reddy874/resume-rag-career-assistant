"""Shared FastAPI dependencies, e.g. lightweight API-key auth."""
from fastapi import Header, HTTPException, status

from app.core.config import get_settings

settings = get_settings()


async def verify_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Simple shared-secret auth.

    This is intentionally minimal — enough to keep a demo/portfolio
    deployment from being wide open on the public internet. For real
    multi-tenant production use, replace with proper user auth (OAuth2 /
    JWT) and per-user authorization, not a single shared key.
    """
    if not settings.require_api_key:
        return
    if not settings.api_key or x_api_key != settings.api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or missing API key.")
