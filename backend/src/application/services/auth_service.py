"""Servicio de autenticación — login multi-tenant + refresh ROTACIÓN (canon <auth>).

Flujo canon: POST /auth/login → lista tenants → selección EXPLÍCITA →
JWT {sub, tenant_id, role, rel_id} + refresh opaco (hash SHA-256 en usuario_sesiones).

Rotación: cada POST /auth/refresh invalida el refresh presentado (one-time use)
y emite un par nuevo. Los refresh expirados se purgan.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.exceptions import AuthenticationError
from src.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_refresh_token,
    verify_password,
)
from src.infrastructure.db.models import (
    Papeleria,
    TUsuario,
    UsuarioPapeleriaRel,
    UsuarioSesion,
)
from src.schemas.auth import LoginRequest, LoginTenantsResponse, TenantInfo, TokenResponse


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _load_user_with_relations(
        self, username: str
    ) -> tuple[TUsuario, list[tuple[UsuarioPapeleriaRel, Papeleria]]]:
        user = (
            await self.session.execute(
                select(TUsuario).where(TUsuario.username == username, TUsuario.is_active.is_(True))
            )
        ).scalar_one_or_none()
        if user is None or not user.password_hash:
            raise AuthenticationError("Usuario o contraseña incorrectos")
        rows = (
            await self.session.execute(
                select(UsuarioPapeleriaRel, Papeleria)
                .join(Papeleria, Papeleria.id == UsuarioPapeleriaRel.papeleria_id)
                .where(UsuarioPapeleriaRel.usuario_id == user.id, Papeleria.activa.is_(True))
            )
        ).all()
        return user, rows

    async def _issue_tokens(
        self, user: TUsuario, rel: UsuarioPapeleriaRel
    ) -> TokenResponse:
        access = create_access_token(
            sub=str(user.id),
            tenant_id=str(rel.papeleria_id),
            role=rel.rol,
            rel_id=str(rel.id),
            username=user.username,
        )
        refresh = generate_refresh_token()
        expires_at = datetime.now(UTC) + timedelta(hours=settings.refresh_token_expire_hours)
        self.session.add(
            UsuarioSesion(
                usuario_id=user.id,
                papeleria_id=rel.papeleria_id,
                refresh_token_hash=hash_refresh_token(refresh),
                expires_at=expires_at,
            )
        )
        await self.session.flush()
        return TokenResponse(
            access_token=access,
            refresh_token=refresh,
            expires_in=settings.access_token_expire_minutes * 60,
        )

    async def login(self, payload: LoginRequest) -> TokenResponse | LoginTenantsResponse:
        user, rows = await self._load_user_with_relations(payload.username)
        if not verify_password(payload.password, user.password_hash):
            raise AuthenticationError("Usuario o contraseña incorrectos")
        if not rows:
            raise AuthenticationError("Usuario sin acceso a ninguna papelería activa")

        if payload.papeleria_id is not None:
            # Selección EXPLÍCITA de tenant
            match = [r for r in rows if r[0].papeleria_id == payload.papeleria_id]
            if not match:
                raise AuthenticationError("El usuario no pertenece a esa papelería")
            rel, _ = match[0]
            return await self._issue_tokens(user, rel)

        if len(rows) == 1:
            rel, _ = rows[0]
            return await self._issue_tokens(user, rel)

        # Multi-tenant: devolver lista para selección explícita
        return LoginTenantsResponse(
            tenants=[
                TenantInfo(
                    papeleria_id=rel.papeleria_id, nombre=p.nombre, slug=p.slug, rol=rel.rol
                )
                for rel, p in rows
            ]
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        """ROTACIÓN: valida + invalida el refresh actual y emite par nuevo."""
        token_hash = hash_refresh_token(refresh_token)
        sesion = (
            await self.session.execute(
                select(UsuarioSesion).where(UsuarioSesion.refresh_token_hash == token_hash)
            )
        ).scalar_one_or_none()
        now = datetime.now(UTC)

        def _aware(dt: datetime) -> datetime:
            """SQLite devuelve naive; se asume UTC."""
            return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)

        if (
            sesion is None
            or sesion.revoked_at is not None
            or _aware(sesion.expires_at) < now
        ):
            raise AuthenticationError("Refresh token inválido, revocado o expirado")

        # One-time use: revocar el presentado
        sesion.revoked_at = now
        await self.session.flush()

        user = await self.session.get(TUsuario, sesion.usuario_id)
        if user is None or not user.is_active:
            raise AuthenticationError("Usuario inactivo")
        rel_row = (
            await self.session.execute(
                select(UsuarioPapeleriaRel).where(
                    UsuarioPapeleriaRel.usuario_id == user.id,
                    UsuarioPapeleriaRel.papeleria_id == sesion.papeleria_id,
                )
            )
        ).scalar_one_or_none()
        if rel_row is None:
            raise AuthenticationError("Relación usuario-tenant ya no existe")

        # Purga de sesiones expiradas del usuario
        expired_filter = UsuarioSesion.expires_at < now.replace(tzinfo=None)
        await self.session.execute(
            delete(UsuarioSesion).where(UsuarioSesion.usuario_id == user.id, expired_filter)
        )
        return await self._issue_tokens(user, rel_row)

    async def me(self, access_token: str) -> dict:
        payload = decode_access_token(access_token)
        user = await self.session.get(TUsuario, UUID(payload["sub"]))
        if user is None or not user.is_active:
            raise AuthenticationError("Usuario ya no existe o inactivo")
        papeleria = await self.session.get(Papeleria, UUID(payload["tenant_id"]))
        if papeleria is None:
            raise AuthenticationError("Tenant ya no existe")
        return {
            "user": user,
            "tenant": papeleria,
            "role": payload["role"],
            "issued_at": payload.get("iat"),
        }
