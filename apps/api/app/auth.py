import asyncio
from typing import Annotated, Any

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import settings


class CurrentUser(BaseModel):
    id: str
    email: str
    name: str


bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]
_keys: dict[str, Any] = {}
_keys_lock = asyncio.Lock()


async def _get_signing_key(key_id: str) -> Any:
    if key_id in _keys:
        return _keys[key_id]

    async with _keys_lock:
        if key_id in _keys:
            return _keys[key_id]
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.get(settings.auth_jwks_url)
            response.raise_for_status()
        for raw_key in response.json().get("keys", []):
            if raw_key.get("kid"):
                _keys[raw_key["kid"]] = jwt.PyJWK.from_dict(raw_key).key
        if key_id not in _keys:
            raise jwt.InvalidKeyError("Signing key not found")
        return _keys[key_id]


async def require_user(credentials: BearerCredentials) -> CurrentUser:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    try:
        header = jwt.get_unverified_header(credentials.credentials)
        key_id = header.get("kid")
        if not isinstance(key_id, str):
            raise jwt.InvalidTokenError("Missing key ID")
        signing_key = await _get_signing_key(key_id)
        payload = jwt.decode(
            credentials.credentials,
            signing_key,
            algorithms=["ES256"],
            audience=settings.auth_audience,
            issuer=settings.auth_issuer,
        )
        return CurrentUser(
            id=str(payload["id"]),
            email=str(payload["email"]),
            name=str(payload["name"]),
        )
    except (KeyError, ValueError, jwt.PyJWTError, httpx.HTTPError) as exc:
        raise unauthorized from exc


AuthenticatedUser = Annotated[CurrentUser, Depends(require_user)]
