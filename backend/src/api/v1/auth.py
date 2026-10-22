"""Router /auth — login multi-tenant, refresh con rotación, /me (canon Sección 6)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.auth import CurrentUser, get_current_user
from src.api.dependencies.db import get_db
from src.application.services.auth_service import AuthService
from src.core.exceptions import AuthenticationError
from src.core.logging import logger
from src.infrastructure.db.models import Papeleria
from src.schemas.auth import (
    LoginRequest,
    LoginTenantsResponse,
    MeResponse,
    RefreshRequest,
    TenantInfo,
    TokenResponse,
    UserInfo,
)

router = APIRouter(prefix="/auth", tags=["auth"])
bearer = HTTPBearer(auto_error=False)


@router.post(
    "/login",
    response_model=TokenResponse | LoginTenantsResponse,
    summary="Login multi-tenant: credenciales → (tokens | lista de tenants)",
    responses={401: {"description": "Credenciales inválidas"}},
)
async def login(
    payload: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse | LoginTenantsResponse:
    service = AuthService(db)
    result = await service.login(payload)
    if isinstance(result, TokenResponse):
        logger.info("login_ok", username=payload.username)
    else:
        logger.info("login_tenant_selection_required", username=payload.username)
    return result


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotación de refresh token (one-time use)",
    responses={401: {"description": "Refresh inválido/revocado/expirado"}},
)
async def refresh(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    service = AuthService(db)
    tokens = await service.refresh(payload.refresh_token)
    logger.info("refresh_rotated")
    return tokens


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Perfil del usuario autenticado + tenant activo",
    responses={401: {"description": "Token requerido/inválido"}},
)
async def me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MeResponse:
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Token de acceso requerido (Bearer)")
    service = AuthService(db)
    data = await service.me(credentials.credentials)
    user = data["user"]
    papeleria: Papeleria = data["tenant"]
    return MeResponse(
        user=UserInfo(
            user_id=user.id,
            username=user.username,
            display_name=user.display_name,
            email=None,
        ),
        tenant=TenantInfo(
            papeleria_id=papeleria.id,
            nombre=papeleria.nombre,
            slug=papeleria.slug,
            rol=data["role"],
        ),
    )
