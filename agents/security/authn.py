"""Authentication hooks — OIDC for humans, service identity for agents."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from config.settings import get_settings

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> dict[str, str]:
    """Placeholder OIDC auth — replace with real token validation in production."""
    settings = get_settings()
    if settings.environment.value == "local" and credentials is None:
        return {"sub": "local-dev", "role": "admin"}
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing credentials")
    return {"sub": "authenticated-user", "role": "user", "token": credentials.credentials}
