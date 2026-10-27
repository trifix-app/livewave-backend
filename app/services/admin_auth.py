import time
from typing import Optional
import jwt
from fastapi import HTTPException, Security, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings

security = HTTPBearer(auto_error=False)


def create_admin_token(username: str) -> str:
    """Generates a signed JWT session token for the admin."""
    payload = {
        "sub": username,
        "role": "admin",
        "exp": int(time.time()) + 86400 * 7,  # 7 days expiration
        "iat": int(time.time()),
    }
    return jwt.encode(payload, settings.admin_jwt_secret, algorithm="HS256")


def verify_admin_token(token: str) -> Optional[dict]:
    """Validates JWT token and checks admin subject."""
    try:
        payload = jwt.decode(token, settings.admin_jwt_secret, algorithms=["HS256"])
        if payload.get("sub") == settings.admin_username:
            return payload
    except Exception:
        pass
    return None


def verify_admin_credentials(username: str, password: str) -> bool:
    """Constant-time-friendly credential check."""
    return username == settings.admin_username and password == settings.admin_password


async def get_current_admin(
    request: Request,
    auth: Optional[HTTPAuthorizationCredentials] = Security(security),
) -> dict:
    """Dependency to enforce admin authentication via Bearer token or Cookie."""
    # 1. Check Authorization Bearer header
    if auth and auth.credentials:
        payload = verify_admin_token(auth.credentials)
        if payload:
            return payload

    # 2. Check Cookie for Web Dashboard
    token = request.cookies.get("admin_token")
    if token:
        payload = verify_admin_token(token)
        if payload:
            return payload

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Unauthorized: Admin access required",
        headers={"WWW-Authenticate": "Bearer"},
    )
