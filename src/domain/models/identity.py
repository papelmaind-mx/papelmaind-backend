"""Modelos de identidad y tenant — Sprint 1."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, Text, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.db.base import Base, uuid7


class Papeleria(Base):
    __tablename__ = "papelerias"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    rfc: Mapped[Optional[str]] = mapped_column(String(15))
    activa: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    sucursales: Mapped[list["Sucursal"]] = relationship(back_populates="papeleria")
    relaciones: Mapped[list["UsuarioPapeleriaRel"]] = relationship(back_populates="papeleria")


class Sucursal(Base):
    __tablename__ = "sucursales"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    papeleria_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papelerias.id"), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

    papeleria: Mapped["Papeleria"] = relationship(back_populates="sucursales")


class Usuario(Base):
    __tablename__ = "tusuarios"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    relaciones: Mapped[list["UsuarioPapeleriaRel"]] = relationship(back_populates="usuario")


class UsuarioPapeleriaRel(Base):
    __tablename__ = "usuario_papeleria_rel"
    __table_args__ = (UniqueConstraint("usuario_id", "papeleria_id", name="uq_user_papeleria"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    usuario_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tusuarios.id"), nullable=False)
    papeleria_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("papelerias.id"), nullable=False)
    rol: Mapped[str] = mapped_column(String(32), nullable=False)  # admin|cajero|supervisor|...
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    usuario: Mapped["Usuario"] = relationship(back_populates="relaciones")
    papeleria: Mapped["Papeleria"] = relationship(back_populates="relaciones")


class CatalogoClavesConfig(Base):
    """F24 — claves canónicas; seed/runtime no inventan claves."""
    __tablename__ = "catalogo_claves_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid7)
    clave: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    tipo: Mapped[str] = mapped_column(String(16), nullable=False)  # string|int|bool|json|decimal
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    valor_default: Mapped[Optional[str]] = mapped_column(Text)
    ambito: Mapped[str] = mapped_column(String(16), default="papeleria")
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
