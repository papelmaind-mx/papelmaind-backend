from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=150)
    password: str = Field(min_length=8, max_length=128)

class TenantInfo(BaseModel):
    rel_id: UUID
    papeleria_id: UUID
    papeleria_nombre: str
    rol: str

class LoginResponse(BaseModel):
    pre_token: Optional[str] = None
    tenants: list[TenantInfo]
    auto_selected: bool = False
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

class SelectTenantRequest(BaseModel):
    pre_token: str
    rel_id: UUID

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

class MeResponse(BaseModel):
    user_id: UUID
    tenant_id: UUID
    rel_id: UUID
    rol: str
    display_name: str
    username: Optional[str] = None
    papeleria_nombre: str
