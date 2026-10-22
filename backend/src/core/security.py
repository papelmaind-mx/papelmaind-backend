"""Seguridad — hash de contraseñas + JWT access/refresh (canon <auth>).

- access 15min (HS256, claims {sub, tenant_id, role, rel_id, username})
- refresh OPACO (token_urlsafe 48 bytes) con hash SHA-256 en usuario_sesiones
- ROTACIÓN: cada refresh invalida el token anterior (one-time use)
"""
from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from src.core.config import settings
from src.core.exceptions import AuthenticationError


def uuid_v7() -> uuid.UUID:
    """UUID v7 (timestamp-based) — canon CONV-03: IDs UUID v7.

    Implementación compacta compatible con generate_uuid_v7() de PostgreSQL 16.
    """
    ts_ms = int(datetime.now(UTC).timestamp() * 1000)
    rand = secrets.randbits(62)
    b = bytearray(16)
    b[0] = (ts_ms >> 40) & 0xFF
    b[1] = (ts_ms >> 32) & 0xFF
    b[2] = (ts_ms >> 24) & 0xFF
    b[3] = (ts_ms >> 16) & 0xFF
    b[4] = (ts_ms >> 8) & 0xFF
    b[5] = ts_ms & 0xFF
    b[6] = 0x70 | ((rand >> 56) & 0x0F)  # version 7
    b[7] = (rand >> 48) & 0xFF
    variant = secrets.randbits(2)
    b[8] = 0x80 | (variant << 6) | ((rand >> 40) & 0x3F)  # variant 10xx
    b[9] = (rand >> 32) & 0xFF
    b[10] = (rand >> 24) & 0xFF
    b[11] = (rand >> 16) & 0xFF
    b[12] = (rand >> 8) & 0xFF
    b[13] = rand & 0xFF
    b[14] = secrets.randbits(8)
    b[15] = secrets.randbits(8)
    return uuid.UUID(bytes=bytes(b))


# --- Contraseñas (passlib bcrypt) ---
from passlib.context import CryptContext  # noqa: E402

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# --- JWT access ---
def create_access_token(
    *, sub: str, tenant_id: str, role: str, rel_id: str, username: str
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": sub,
        "tenant_id": tenant_id,
        "role": role,
        "rel_id": rel_id,
        "username": username,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp()),
        "typ": "access",
        "jti": str(uuid_v7()),  # único por emisión (rotación testeable)
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
    except jwt.ExpiredSignatureError as e:
        raise AuthenticationError("Token expirado") from e
    except jwt.InvalidTokenError as e:
        raise AuthenticationError("Token inválido") from e
    if payload.get("typ") != "access":
        raise AuthenticationError("Tipo de token inválido")
    return payload


# --- Refresh opaco con hash SHA-256 ---
def generate_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
