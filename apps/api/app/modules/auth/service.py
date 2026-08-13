from app.core.security import decode_access_token
from app.modules.auth.schemas import CurrentUser


async def authenticate(token: str) -> CurrentUser:
    payload = await decode_access_token(token)
    return CurrentUser(
        id=str(payload["id"]),
        email=str(payload["email"]),
        name=str(payload["name"]),
    )
