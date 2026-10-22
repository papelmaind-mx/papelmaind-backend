"""Dependencias de autenticación — CurrentUser + require_roles (canon <roles_canon>).

Flujo (canon login_multi_tenant):
POST /auth/login → lista tenants → selección EXPLÍCITA → JWT {sub, tenant_id, role, rel_id}
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from src.core.exceptions import AuthenticationError, ForbiddenError
from src.core.security import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)


class CurrentUser(BaseModel):
    """Identidad autenticada extraída del JWT access."""

    user_id: UUID
    tenant_id: UUID
    role: str
    rel_id: UUID
    username: str


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Token de acceso requerido (Bearer)")
    payload = decode_access_token(credentials.credentials)
    user = CurrentUser(
        user_id=UUID(payload["sub"]),
        tenant_id=UUID(payload["tenant_id"]),
        role=payload["role"],
        rel_id=UUID(payload["rel_id"]),
        username=payload.get("username", ""),
    )
    request.state.current_user = user
    return user


def require_roles(*roles: str):
    """Factory de dependencia: exige que el rol del JWT esté en `roles`."""

    async def _checker(user: Annotated[CurrentUser, Depends(get_current_user)]) -> CurrentUser:
        if user.role not in roles:
            raise ForbiddenError(f"Requiere rol en {list(roles)}; tienes '{user.role}'")
        return user

    return _checker
