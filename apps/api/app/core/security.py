import asyncio
from typing import Any

import httpx
import jwt

from app.core.config import settings

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


async def decode_access_token(token: str) -> dict[str, Any]:
    header = jwt.get_unverified_header(token)
    key_id = header.get("kid")
    if not isinstance(key_id, str):
        raise jwt.InvalidTokenError("Missing key ID")
    signing_key = await _get_signing_key(key_id)
    return jwt.decode(
        token,
        signing_key,
        algorithms=["ES256"],
        audience=settings.auth_audience,
        issuer=settings.auth_issuer,
    )
