"""Auth S1 — login multi-tenant + refresh + /me (RLS)."""
from __future__ import annotations

import uuid as uuid_mod
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, text

from src.api.dependencies import CurrentUser, get_current_user
from src.core.config import get_settings
from src.core.database import WorkerSessionLocal
from src.core.security import (
    create_access_token,
    create_pre_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from src.models import Papeleria, TUsuario, UsuarioPapeleriaRel, UsuarioSesion
from src.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RefreshRequest,
    SelectTenantRequest,
    TenantInfo,
    TokenPair,
)

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


async def _emitir_tokens(db, user, rel, tenants, auto: bool) -> LoginResponse:
    sesion = UsuarioSesion(
        papeleria_id=rel.papeleria_id,
        usuario_id=user.id,
        refresh_token_hash="pendiente",
        expires_at=datetime.now(timezone.utc)
        + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS),
    )
    db.add(sesion)
    await db.flush()
    refresh_jwt, raw = create_refresh_token(user.id, rel.papeleria_id, sesion.id)
    sesion.refresh_token_hash = hash_refresh_token(refresh_jwt)
    await db.commit()
    return LoginResponse(
        tenants=tenants,
        auto_selected=auto,
        access_token=create_access_token(user.id, rel.papeleria_id, rel.rol, rel.id),
        refresh_token=refresh_jwt,
    )


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    async with WorkerSessionLocal() as db:
        user = (
            await db.execute(
                select(TUsuario).where(
                    (TUsuario.username == payload.username)
                    | (TUsuario.email == payload.username)
                )
            )
        ).scalar_one_or_none()

        # Timing uniforme: siempre se verifica un hash
        dummy_hash = hash_password("dummy_password_timing_safe")
        stored = user.password_hash if user and user.password_hash else dummy_hash
        ok = verify_password(payload.password, stored)
        if not user or not ok:
            raise HTTPException(401, "Credenciales inválidas")
        if not user.activo:
            raise HTTPException(403, "Usuario inactivo")

        rels = (
            await db.execute(
                select(UsuarioPapeleriaRel, Papeleria)
                .join(Papeleria, Papeleria.id == UsuarioPapeleriaRel.papeleria_id)
                .where(
                    UsuarioPapeleriaRel.usuario_id == user.id,
                    UsuarioPapeleriaRel.activo.is_(True),
                    Papeleria.activa.is_(True),
                )
            )
        ).all()

        if not rels:
            raise HTTPException(403, "Usuario sin acceso a ningún tenant activo")

        user.ultimo_acceso = datetime.now(timezone.utc)
        await db.commit()

        tenants = [
            TenantInfo(
                rel_id=rel.id,
                papeleria_id=rel.papeleria_id,
                papeleria_nombre=p.nombre,
                rol=rel.rol,
            )
            for rel, p in rels
        ]

        if len(tenants) == 1:
            rel, _ = rels[0]
            return await _emitir_tokens(db, user, rel, tenants, auto=True)

        return LoginResponse(pre_token=create_pre_token(user.id), tenants=tenants)


@router.post("/select-tenant", response_model=TokenPair)
async def select_tenant(payload: SelectTenantRequest):
    claims = decode_token(payload.pre_token)
    if not claims or claims.get("type") != "pre":
        raise HTTPException(401, "pre_token inválido o expirado")
    user_id = uuid_mod.UUID(claims["sub"])

    async with WorkerSessionLocal() as db:
        rel = (
            await db.execute(
                select(UsuarioPapeleriaRel).where(
                    UsuarioPapeleriaRel.id == payload.rel_id,
                    UsuarioPapeleriaRel.usuario_id == user_id,
                    UsuarioPapeleriaRel.activo.is_(True),
                )
            )
        ).scalar_one_or_none()
        if not rel:
            raise HTTPException(403, "Relación no válida para este usuario")

        sesion = UsuarioSesion(
            papeleria_id=rel.papeleria_id,
            usuario_id=user_id,
            refresh_token_hash="pendiente",
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS),
        )
        db.add(sesion)
        await db.flush()
        refresh_jwt, raw = create_refresh_token(user_id, rel.papeleria_id, sesion.id)
        sesion.refresh_token_hash = hash_refresh_token(refresh_jwt)
        await db.commit()

        return TokenPair(
            access_token=create_access_token(
                user_id, rel.papeleria_id, rel.rol, rel.id
            ),
            refresh_token=refresh_jwt,
        )


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest):
    claims = decode_token(payload.refresh_token)
    if not claims or claims.get("type") != "refresh":
        raise HTTPException(401, "Refresh token inválido")

    user_id = uuid_mod.UUID(claims["sub"])
    sid = uuid_mod.UUID(claims["sid"])
    # El refresh JWT no incluye el raw; hasheamos el token completo como id de sesión
    token_hash = hash_refresh_token(payload.refresh_token)

    async with WorkerSessionLocal() as db:
        sesion = (
            await db.execute(select(UsuarioSesion).where(UsuarioSesion.id == sid))
        ).scalar_one_or_none()

        if not sesion or sesion.refresh_token_hash != token_hash or not sesion.activa:
            await db.execute(
                text("UPDATE usuario_sesiones SET activa = false WHERE usuario_id = :u"),
                {"u": str(user_id)},
            )
            await db.commit()
            raise HTTPException(401, "Refresh inválido — sesiones revocadas por seguridad")

        sesion.activa = False
        rel = (
            await db.execute(
                select(UsuarioPapeleriaRel).where(
                    UsuarioPapeleriaRel.usuario_id == user_id,
                    UsuarioPapeleriaRel.papeleria_id == sesion.papeleria_id,
                )
            )
        ).scalar_one()

        nueva = UsuarioSesion(
            papeleria_id=sesion.papeleria_id,
            usuario_id=user_id,
            refresh_token_hash="pendiente",
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS),
        )
        db.add(nueva)
        await db.flush()
        refresh_jwt, raw = create_refresh_token(
            user_id, sesion.papeleria_id, nueva.id
        )
        nueva.refresh_token_hash = hash_refresh_token(refresh_jwt)
        await db.commit()

        return TokenPair(
            access_token=create_access_token(
                user_id, sesion.papeleria_id, rel.rol, rel.id
            ),
            refresh_token=refresh_jwt,
        )


@router.get("/me", response_model=MeResponse)
async def me(user: CurrentUser = Depends(get_current_user)):
    from src.infrastructure.db.unit_of_work import TenantUnitOfWork

    async with TenantUnitOfWork(user.tenant_id) as db:
        rel = (
            await db.execute(
                select(UsuarioPapeleriaRel).where(
                    UsuarioPapeleriaRel.id == user.rel_id
                )
            )
        ).scalar_one_or_none()
        if not rel:
            raise HTTPException(401, "Sesión no válida para este tenant")

        tusu = (
            await db.execute(select(TUsuario).where(TUsuario.id == user.user_id))
        ).scalar_one()
        papeleria = (
            await db.execute(select(Papeleria).where(Papeleria.id == user.tenant_id))
        ).scalar_one()

        return MeResponse(
            user_id=user.user_id,
            tenant_id=user.tenant_id,
            rel_id=user.rel_id,
            rol=user.role,
            display_name=tusu.display_name,
            username=tusu.username,
            papeleria_nombre=papeleria.nombre,
        )
