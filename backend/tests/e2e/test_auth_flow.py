"""E2E Sprint 1 — Auth + Multi-tenant (canon: test_auth_flow.py).

Cubre: login exitoso, credenciales inválidas, acceso sin token,
GET /auth/me con token válido, rotación de refresh, rol insuficiente.
"""
from __future__ import annotations

import pytest

from tests.conftest import bearer, login

pytestmark = pytest.mark.asyncio


class TestLogin:
    async def test_login_exitoso_devuelve_access_y_refresh(self, app_client, admin_a):
        data = await login(app_client, "admin_a", "AdminA123!")
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["token_type"] == "bearer"
        assert data["expires_in"] > 0

    async def test_login_credenciales_invalidas_401(self, app_client, admin_a):
        resp = await app_client.post(
            "/api/v1/auth/login", json={"username": "admin_a", "password": "Incorrecta99!"}
        )
        assert resp.status_code == 401

    async def test_login_usuario_inexistente_401(self, app_client):
        resp = await app_client.post(
            "/api/v1/auth/login", json={"username": "nadie", "password": "Nadie12345!"}
        )
        assert resp.status_code == 401

    async def test_login_usuario_multitenant_exige_seleccion(
        self, app_client, db_session, tenant_a, tenant_b, admin_a
    ):
        """Canon login_multi_tenant: lista tenants → selección EXPLÍCITA."""
        from src.infrastructure.db import models

        db_session.add(
            models.UsuarioPapeleriaRel(
                usuario_id=admin_a[0].id, papeleria_id=tenant_b.id, rol="cajero"
            )
        )
        await db_session.flush()

        resp = await app_client.post(
            "/api/v1/auth/login", json={"username": "admin_a", "password": "AdminA123!"}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body.get("requires_selection") is True
        assert len(body["tenants"]) == 2

        # Selección explícita → tokens con tenant correcto
        resp2 = await app_client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin_a",
                "password": "AdminA123!",
                "papeleria_id": str(tenant_b.id),
            },
        )
        assert resp2.status_code == 200
        assert resp2.json()["access_token"]

    async def test_login_seleccion_tenant_ajeno_401(
        self, app_client, db_session, tenant_a, tenant_b, admin_a, admin_b
    ):
        resp = await app_client.post(
            "/api/v1/auth/login",
            json={
                "username": "admin_a",
                "password": "AdminA123!",
                "papeleria_id": str(tenant_b.id),
            },
        )
        assert resp.status_code == 401


class TestMe:
    async def test_me_sin_token_401(self, app_client, admin_a):
        resp = await app_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    async def test_me_con_token_valido(self, app_client, admin_a, tenant_a):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        resp = await app_client.get(
            "/api/v1/auth/me", headers=bearer(tokens["access_token"])
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["user"]["username"] == "admin_a"
        assert body["tenant"]["papeleria_id"] == str(tenant_a.id)
        assert body["tenant"]["slug"] == "central-a"
        assert body["tenant"]["rol"] == "admin"

    async def test_me_token_basura_401(self, app_client, admin_a):
        resp = await app_client.get("/api/v1/auth/me", headers=bearer("token-basura"))
        assert resp.status_code == 401


class TestRefreshRotation:
    async def test_refresh_rota_y_anterior_queda_invalido(self, app_client, admin_a):
        """Canon <auth>: refresh ROTACIÓN — one-time use."""
        tokens = await login(app_client, "admin_a", "AdminA123!")
        old_refresh = tokens["refresh_token"]

        resp = await app_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert resp.status_code == 200
        new_tokens = resp.json()
        assert new_tokens["access_token"] != tokens["access_token"]
        assert new_tokens["refresh_token"] != old_refresh

        # El refresh YA USADO debe rechazarse (rotación estricta)
        resp2 = await app_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": old_refresh}
        )
        assert resp2.status_code == 401

        # El nuevo refresh funciona
        resp3 = await app_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": new_tokens["refresh_token"]}
        )
        assert resp3.status_code == 200

    async def test_refresh_token_inventado_401(self, app_client, admin_a):
        resp = await app_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": "x" * 64}
        )
        assert resp.status_code == 401

    async def test_me_con_access_viejo_tras_rotar(self, app_client, admin_a):
        """El access viejo sigue válido hasta expirar (15min) — por diseño."""
        tokens = await login(app_client, "admin_a", "AdminA123!")
        await app_client.post(
            "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
        )
        resp = await app_client.get(
            "/api/v1/auth/me", headers=bearer(tokens["access_token"])
        )
        assert resp.status_code == 200


class TestRoles:
    async def test_rol_insuficiente_para_crear_catalogo(self, app_client, db_session, tenant_a):
        """Un cajero NO puede crear unidades de medida (solo admin)."""
        from src.core.security import get_password_hash
        from src.infrastructure.db import models

        cajero = models.TUsuario(
            username="cajero01", password_hash=get_password_hash("Cajero123!")
        )
        db_session.add(cajero)
        await db_session.flush()
        db_session.add(
            models.UsuarioPapeleriaRel(
                usuario_id=cajero.id, papeleria_id=tenant_a.id, rol="cajero"
            )
        )
        await db_session.flush()

        tokens = await login(app_client, "cajero01", "Cajero123!")
        resp = await app_client.post(
            "/api/v1/catalog/unidades-medida",
            json={"clave": "LT", "nombre": "Litro", "permite_decimales": True},
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 403
