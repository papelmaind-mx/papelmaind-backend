import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, Column, DateTime, String, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlmodel import Field, SQLModel


def _uuid_pk() -> dict:
    return {
        "sa_column": Column(
            PG_UUID(as_uuid=True),
            primary_key=True,
            server_default=text("generate_uuid_v7()"),
        )
    }


class Papeleria(SQLModel, table=True):
    __tablename__ = "papelerias"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, **_uuid_pk())
    nombre: str = Field(sa_column=Column(String(150), nullable=False))
    slug: str = Field(sa_column=Column(String(50), nullable=False, unique=True))
    rfc_emisor: Optional[str] = Field(default=None, sa_column=Column(String(15)))
    razon_social: Optional[str] = Field(default=None, sa_column=Column(String(200)))
    plan: str = Field(default="free", sa_column=Column(String(30), server_default=text("'free'")))
    activa: bool = Field(default=True, sa_column=Column(Boolean, server_default=text("true")))
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=text("NOW()")),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=text("NOW()")),
    )


class Sucursal(SQLModel, table=True):
    __tablename__ = "sucursales"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, **_uuid_pk())
    papeleria_id: uuid.UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False))
    nombre: str = Field(sa_column=Column(String(100), nullable=False))
    codigo: str = Field(sa_column=Column(String(20), nullable=False))
    direccion: Optional[str] = None
    telefono: Optional[str] = None
    es_default: bool = Field(default=False)
    activa: bool = Field(default=True)


class PapeleriaConfiguracion(SQLModel, table=True):
    __tablename__ = "papeleria_configuracion"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, **_uuid_pk())
    papeleria_id: uuid.UUID = Field(sa_column=Column(PG_UUID(as_uuid=True), nullable=False))
    clave: str = Field(sa_column=Column(String(100), nullable=False))
    valor: str = Field(sa_column=Column(String(), nullable=False))
    descripcion: Optional[str] = None
