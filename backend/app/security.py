from __future__ import annotations

from dataclasses import dataclass
from hmac import compare_digest

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader

from app.config import Settings

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


@dataclass(frozen=True)
class Principal:
    """Authenticated caller information used by future audit/tenant storage."""

    subject: str


def require_authenticated_principal(
    request: Request,
    supplied_api_key: str | None = Security(api_key_header),
) -> Principal:
    """Require the configured API key when authentication is enabled.

    Local development remains usable without a credential. Production settings
    validation guarantees this bypass cannot be enabled in production.
    """
    settings: Settings = request.app.state.settings
    if not settings.auth_required:
        principal = Principal(subject="local-development")
        request.state.principal = principal
        return principal

    expected = settings.api_key.get_secret_value() if settings.api_key else ""
    if not supplied_api_key or not compare_digest(supplied_api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A valid API key is required",
            headers={"WWW-Authenticate": "APIKey"},
        )
    principal = Principal(subject="authenticated-reviewer")
    request.state.principal = principal
    return principal
