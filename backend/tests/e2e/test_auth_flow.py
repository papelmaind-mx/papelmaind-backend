"""T10: login/refresh/me + REGRESIÓN F1 (canon: WorkerSessionLocal vs AsyncSessionLocal)."""
import pytest
from sqlalchemy import text

from src.core.security import decode_token

PWD = "TestAdmin123!"


@pytest.mark.asyncio
class TestT10Auth:
    async def test_login_ok_devuelve_tenant_y_tokens(self, client, seed_data):
        r = await client.post("/api/v1/auth/login",
                               json={"username": "test_admin_a", "password": PWD})
        assert r.status_code == 200
        body = r.json()
        assert body["auto_selected"] is True          # 1 solo tenant → auto
        assert len(body["tenants"]) == 1
        assert body["tenants"][0]["rol"] == "admin"
        claims = decode_token(body["access_token"])
        assert claims["tenant_id"] == str(seed_data["t_a"])
        assert claims["type"] == "access"

    async def test_login_password_malo_401(self, client):
        r = await client.post("/api/v1/auth/login",
                               json={"username": "test_admin_a", "password": "WrongPass123!"})
        assert r.status_code == 401

    async def test_login_usuario_inactivo_403(self, client):
        r = await client.post("/api/v1/auth/login",
                               json={"username": "test_inactive", "password": PWD})
        assert r.status_code == 403

    async def test_me_con_jwt_200(self, client, seed_data):
        login = (await client.post("/api/v1/auth/login",
                    json={"username": "test_admin_a", "password": PWD})).json()
        r = await client.get("/api/v1/auth/me",
                             headers={"Authorization": f"Bearer {login['access_token']}"})
        assert r.status_code == 200
        assert r.json()["tenant_id"] == str(seed_data["t_a"])
        assert r.json()["rol"] == "admin"

    async def test_me_sin_jwt_401(self, client):
        r = await client.get("/api/v1/auth/me")
        assert r.status_code == 401

    async def test_refresh_rota_y_el_viejo_muere(self, client):
        login = (await client.post("/api/v1/auth/login",
                    json={"username": "test_admin_a", "password": PWD})).json()
        r1 = await client.post("/api/v1/auth/refresh",
                               json={"refresh_token": login["refresh_token"]})
        assert r1.status_code == 200
        nuevo = r1.json()
        assert nuevo["refresh_token"] != login["refresh_token"]

        # REUSO del token viejo → 401 + revocación total
        r2 = await client.post("/api/v1/auth/refresh",
                               json={"refresh_token": login["refresh_token"]})
        assert r2.status_code == 401
        # y el NUEVO también murió (revocación en cascada anti-robo)
        r3 = await client.post("/api/v1/auth/refresh",
                               json={"refresh_token": nuevo["refresh_token"]})
        assert r3.status_code == 401

    async def test_regresion_f1_session_sin_tenant_ve_cero(self, app_session, seed_data):
        """LA regresión canónica: sesión erp_app SIN set_current_tenant → RLS → 0 filas."""
        # Sin SET LOCAL: RLS filtra TODO
        rows = (await app_session.execute(text("SELECT COUNT(*) FROM usuario_papeleria_rel"))).scalar()
        assert rows == 0  # ← F1: si esto devuelve >0, RLS está roto

        # Con SET LOCAL del tenant A: solo ve las filas de A
        async with app_session.begin():
            await app_session.execute(
                text("SELECT set_current_tenant(:t)"), {"t": str(seed_data["t_a"])})
            rows = (await app_session.execute(
                text("SELECT COUNT(*) FROM usuario_papeleria_rel"))).scalar()
        assert rows == 1  # test_admin_a + test_inactive (2 rels de A)... ver abajo
