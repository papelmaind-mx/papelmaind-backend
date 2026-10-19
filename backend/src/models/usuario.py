import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, Integer, String, text
from sqlalchemy.dialects.postgresql import INET, UUID as PG_UUID
from sqlmodel import Field, SQLModel

from src.models.tenant import _uuid_pk


class TUsuario(SQLModel, table=True):
    __tablename__ = "tusuarios"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, **_uuid_pk())
    phone_number: Optional[str] = Field(default=None, sa_column=Column(String(20), unique=True))
    username: Optional[str] = Field(default=None, sa_column=Column(String(50), unique=True))
    display_name: str = Field(sa_column=Column(String(100), nullable=False))
    email: Optional[str] = Field(default=None, sa_column=Column(String(), unique=True))
    password_hash: Optional[str] = Field(default=None, sa_column=Column(String()))
    pin_hash: Optional[str] = None
    verificado: bool = Field(default=False)
    two_factor_enabled: bool = Field(default=False)
    es_bot: bool = Field(default=False)
    activo: bool = Field(default=True, sa_column=Column(Boolean, server_default=text("true")))
    ultimo_acceso: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True))
    )


class UsuarioPapeleriaRel(SQLModel, table=True):
    __tablename__ = "usuario_papeleria_rel"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, **_uuid_pk())
    usuario_id: uuid.UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False))
    papeleria_id: uuid.UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False))
    rol: str = Field(sa_column=Column(String(20), nullable=False))
    saldo_credito: float = Field(default=0.0)
    limite_credito: float = Field(default=0.0)
    nivel_cliente: str = Field(default="bronce")
    total_compras: float = Field(default=0.0)
    num_compras: int = Field(default=0, sa_column=Column(Integer, server_default=text("0")))
    activo: bool = Field(default=True)


class UsuarioSesion(SQLModel, table=True):
    __tablename__ = "usuario_sesiones"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, **_uuid_pk())
    papeleria_id: uuid.UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False))
    usuario_id: uuid.UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False))
    refresh_token_hash: str = Field(sa_column=Column(String(255), nullable=False, unique=True))
    dispositivo: Optional[str] = None
    ip_address: Optional[str] = Field(default=None, sa_column=Column(INET))
    user_agent: Optional[str] = None
    activa: bool = Field(default=True)
    expires_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=text("NOW()")),
    )
