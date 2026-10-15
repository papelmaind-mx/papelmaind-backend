"""JWT + hash de password — Sprint 1."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
import uuid

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.infrastructure.db.settings import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(
    *,
    user_id: uuid.UUID,
    papeleria_id: uuid.UUID,
    rol: str,
    extra: Optional[dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "papeleria_id": str(papeleria_id),
        "rol": rol,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_expire_minutes)).timestamp()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])


def get_context_from_jwt(token: str) -> dict[str, Any]:
    try:
        data = decode_token(token)
        return {
            "user_id": uuid.UUID(data["sub"]),
            "papeleria_id": uuid.UUID(data["papeleria_id"]),
            "rol": data.get("rol"),
        }
    except (JWTError, KeyError, ValueError) as e:
        raise ValueError(f"Token inválido: {e}") from e
