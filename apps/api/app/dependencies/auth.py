from typing import Annotated

import httpx
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.modules.auth.schemas import CurrentUser
from app.modules.auth.service import authenticate

bearer_scheme = HTTPBearer(auto_error=False)
BearerCredentials = Annotated[
    HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
]


async def require_user(credentials: BearerCredentials) -> CurrentUser:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise unauthorized

    try:
        return await authenticate(credentials.credentials)
    except (KeyError, ValueError, jwt.PyJWTError, httpx.HTTPError) as exc:
        raise unauthorized from exc


AuthenticatedUser = Annotated[CurrentUser, Depends(require_user)]
