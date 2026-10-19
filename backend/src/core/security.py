import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from src.core.config import get_settings

settings = get_settings()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.now(timezone.utc) + expires_delta
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_pre_token(user_id: UUID) -> str:
    return _create_token(
        {"sub": str(user_id), "type": "pre", "scope": "tenant_selection"},
        timedelta(minutes=settings.PRE_TOKEN_EXPIRE_MINUTES),
    )


def create_access_token(user_id: UUID, tenant_id: UUID, role: str, rel_id: UUID) -> str:
    return _create_token(
        {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "role": role,
            "rel_id": str(rel_id),
            "type": "access",
        },
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: UUID, tenant_id: UUID, session_id: UUID):
    raw = secrets.token_urlsafe(48)
    token = _create_token(
        {
            "sub": str(user_id),
            "tenant_id": str(tenant_id),
            "sid": str(session_id),
            "type": "refresh",
        },
        timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS),
    )
    return token, raw


def hash_refresh_token(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def decode_token(token: str) -> Optional[dict[str, Any]]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
