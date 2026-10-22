"""Modelos de usuarios y sesiones — tusuarios, usuario_papeleria_rel, usuario_sesiones."""
from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy import Uuid as SAUuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.security import uuid_v7
from src.infrastructure.db.models.base import Base


class TUsuario(Base):
    __tablename__ = "tusuarios"

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    phone_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    pin_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    two_factor_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    relaciones: Mapped[list[UsuarioPapeleriaRel]] = relationship(back_populates="usuario")
    sesiones: Mapped[list[UsuarioSesion]] = relationship(back_populates="usuario")


class UsuarioPapeleriaRel(Base):
    """Relación usuario ↔ tenant con rol (canon <roles_canon>)."""
    __tablename__ = "usuario_papeleria_rel"
    __table_args__ = (
        CheckConstraint(
            "rol IN ('superadmin','admin','cajero','contador','cliente','system',"
            "'repartidor','proveedor')",
            name="ck_rel_rol",
        ),
        CheckConstraint(
            "nivel_cliente IN ('bronce','plata','oro','diamante')",
            name="ck_rel_nivel_cliente",
        ),
        UniqueConstraint("usuario_id", "papeleria_id", name="uq_usuario_papeleria"),
    )

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    usuario_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("tusuarios.id"), index=True, nullable=False
    )
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    rol: Mapped[str] = mapped_column(String(20), nullable=False)
    nivel_cliente: Mapped[str] = mapped_column(String(20), default="bronce")

    usuario: Mapped[TUsuario] = relationship(back_populates="relaciones")


class UsuarioSesion(Base):
    """Refresh tokens con hash SHA-256 — soporta ROTACIÓN (canon <auth>)."""
    __tablename__ = "usuario_sesiones"

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    usuario_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("tusuarios.id"), index=True, nullable=False
    )
    papeleria_id: Mapped[str | None] = mapped_column(SAUuid, nullable=True, index=True)
    refresh_token_hash: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    usuario: Mapped[TUsuario] = relationship(back_populates="sesiones")
