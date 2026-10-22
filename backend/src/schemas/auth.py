"""Esquemas de autenticación — login multi-tenant, refresh con rotación, /me."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8, max_length=128)
    papeleria_id: UUID | None = Field(
        default=None,
        description="Tenant EXPLÍCITO. Requerido solo si el usuario pertenece a varios.",
    )


class TenantInfo(BaseModel):
    papeleria_id: UUID
    nombre: str
    slug: str
    rol: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class LoginTenantsResponse(BaseModel):
    """Login multi-tenant paso 1: selección EXPLÍCITA requerida."""

    requires_selection: bool = True
    tenants: list[TenantInfo]


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=20)


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    username: str
    display_name: str | None = None
    email: EmailStr | None = None


class MeResponse(BaseModel):
    user: UserInfo
    tenant: TenantInfo
    issued_at: datetime | None = None
