"""Modelos de tenancy — papelerias, sucursales, cajas, estaciones (canon Sección 2)."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy import Uuid as SAUuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.security import uuid_v7
from src.infrastructure.db.models.base import Base

UUID_PK = dict(primary_key=True, default=uuid_v7)


class Papeleria(Base):
    """Tenant raíz. Sin papeleria_id (es el tenant mismo)."""
    __tablename__ = "papelerias"
    __table_args__ = (UniqueConstraint("slug", name="uq_papeleria_slug"),)

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), nullable=False)
    plan: Mapped[str] = mapped_column(String(30), default="free")
    activa: Mapped[bool] = mapped_column(Boolean, default=True)

    sucursales: Mapped[list[Sucursal]] = relationship(back_populates="papeleria")


class Sucursal(Base):
    __tablename__ = "sucursales"
    __table_args__ = (UniqueConstraint("papeleria_id", "codigo", name="uq_sucursal_codigo"),)

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)

    papeleria: Mapped[Papeleria] = relationship(back_populates="sucursales")


class CajaRegistradora(Base):
    __tablename__ = "cajas_registradoras"

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    sucursal_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("sucursales.id"), index=True, nullable=False
    )
    codigo: Mapped[str] = mapped_column(String(20), nullable=False)
    tipo: Mapped[str] = mapped_column(String(20), default="fisica")
    fondo_fijo_default: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0.00"))


class Estacion(Base):
    """F26: estaciones.tipo usa MAYÚSCULAS (identificador de terminal, NO estado de dominio)."""
    __tablename__ = "estaciones"
    __table_args__ = (
        CheckConstraint(
            "tipo IN ('POS','WEB','MOVIL','API','KIOSCO','EMPAQUE')",
            name="ck_estacion_tipo_f26",
        ),
    )

    id: Mapped[str] = mapped_column(SAUuid, primary_key=True, default=uuid_v7)
    papeleria_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("papelerias.id"), index=True, nullable=False
    )
    sucursal_id: Mapped[str] = mapped_column(
        SAUuid, ForeignKey("sucursales.id"), index=True, nullable=False
    )
    codigo: Mapped[str] = mapped_column(String(3), nullable=False)
    tipo: Mapped[str] = mapped_column(String(10), nullable=False)
    caja_id: Mapped[str | None] = mapped_column(
        SAUuid, ForeignKey("cajas_registradoras.id"), nullable=True
    )
