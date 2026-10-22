"""E2E Sprint 2 — Catálogo + Inventario + FEFO.

Incluye tests de matriz canon:
- T2 fefo_orden: 2 lotes (vence 30d vs 365d) + venta 15 → cercano agotado, lejano parcial
- T5 rls_disjoint: Admin A vs B listan artículos → conjuntos disjuntos; A GET id de B → 404
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select

from src.infrastructure.db import models
from tests.conftest import bearer, login

pytestmark = pytest.mark.asyncio


class TestCatalogFlow:
    async def test_crear_unidad_medida(self, app_client, admin_a):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        resp = await app_client.post(
            "/api/v1/catalog/unidades-medida",
            json={"clave": "PZA", "nombre": "Pieza", "permite_decimales": False},
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 201
        assert resp.json()["clave"] == "PZA"

    async def test_unidad_duplicada_409(self, app_client, admin_a):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        payload = {"clave": "PZA", "nombre": "Pieza", "permite_decimales": False}
        first = await app_client.post(
            "/api/v1/catalog/unidades-medida", json=payload, headers=bearer(tokens["access_token"])
        )
        assert first.status_code == 201
        dup = await app_client.post(
            "/api/v1/catalog/unidades-medida", json=payload, headers=bearer(tokens["access_token"])
        )
        assert dup.status_code == 409

    async def test_crear_impuesto_iva16(self, app_client, admin_a):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        resp = await app_client.post(
            "/api/v1/catalog/impuestos",
            json={"nombre": "IVA 16%", "tipo": "iva", "tasa": "0.1600"},
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 201
        assert float(resp.json()["tasa"]) == 0.16

    async def test_crear_articulo_y_listar(self, app_client, admin_a, catalog_a):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        um_resp = await app_client.get(
            "/api/v1/catalog/unidades-medida", headers=bearer(tokens["access_token"])
        )
        um_id = um_resp.json()[0]["id"]
        resp = await app_client.post(
            "/api/v1/catalog/articulos",
            json={
                "sku": "PLUMON-01",
                "descripcion": "Plumón permanente negro",
                "unidad_medida_id": um_id,
                "precio_base": "18.5000",
            },
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["sku"] == "PLUMON-01"
        assert body["stock_actual"] == "0.000"

        listing = await app_client.get(
            "/api/v1/catalog/articulos", headers=bearer(tokens["access_token"])
        )
        assert listing.status_code == 200
        skus = [a["sku"] for a in listing.json()]
        assert "PLUMON-01" in skus
        assert "CUADERNO-100" in skus

    async def test_articulo_con_unidad_de_otro_tenant_404(
        self, app_client, admin_a, admin_b, catalog_a, catalog_b_for_tenant_b
    ):
        """El admin A no puede usar la unidad de medida del tenant B."""
        tokens_a = await login(app_client, "admin_a", "AdminA123!")
        tokens_b = await login(app_client, "admin_b", "AdminB123!")
        um_b = (
            await app_client.get(
                "/api/v1/catalog/unidades-medida", headers=bearer(tokens_b["access_token"])
            )
        ).json()[0]["id"]

        resp = await app_client.post(
            "/api/v1/catalog/articulos",
            json={
                "sku": "ESPIA-01",
                "descripcion": "Intento de cruzar tenant",
                "unidad_medida_id": um_b,
                "precio_base": "1.0000",
            },
            headers=bearer(tokens_a["access_token"]),
        )
        assert resp.status_code == 404


class TestInventoryFlow:
    async def test_recibir_lote_incrementa_stock(self, app_client, admin_a, catalog_a):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        art_id = str(catalog_a["art"].id)
        from datetime import date, timedelta

        resp = await app_client.post(
            "/api/v1/inventory/lotes",
            json={
                "articulo_id": art_id,
                "numero_lote": "L-NUEVO-1",
                "fecha_vencimiento": (date.today() + timedelta(days=90)).isoformat(),
                "cantidad_actual": "50.000",
                "costo_unitario": "20.0000",
            },
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 201
        art_resp = await app_client.get(
            f"/api/v1/catalog/articulos/{art_id}", headers=bearer(tokens["access_token"])
        )
        assert art_resp.json()["stock_actual"] == "80.000"  # 30 seed + 50 nuevo

    async def test_listar_lotes_por_articulo_orden_fefo(
        self, app_client, admin_a, catalog_a
    ):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        resp = await app_client.get(
            "/api/v1/inventory/lotes",
            params={"articulo_id": str(catalog_a["art"].id)},
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 200
        lotes = resp.json()
        assert len(lotes) == 2
        # Orden FEFO: el más cercano a vencer primero
        assert lotes[0]["numero_lote"] == "L-30D"
        assert lotes[1]["numero_lote"] == "L-365D"


class TestT2FefoOrden:
    """T2 fefo_orden: 2 lotes (vence 30d vs 365d) + venta 15 → cercano agotado, lejano parcial."""

    async def test_allocate_15_agota_cercano_y_deja_lejano_parcial(
        self, app_client, db_session, admin_a, catalog_a
    ):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        art_id = str(catalog_a["art"].id)

        resp = await app_client.post(
            "/api/v1/inventory/allocate",
            json={"articulo_id": art_id, "cantidad": "15.000"},
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 200
        assert resp.json()["stock_actual_restante"] == "15.000"

        cercano = await db_session.get(models.TLote, catalog_a["lote_cercano"].id)
        lejano = await db_session.get(models.TLote, catalog_a["lote_lejano"].id)
        assert cercano.cantidad_actual == Decimal("0.000")
        assert cercano.estado == "agotado"
        assert lejano.cantidad_actual == Decimal("15.000")
        assert lejano.estado == "parcial"

        # El movimiento 'salida' quedó registrado por lote
        salidas = (
            (
                await db_session.execute(
                    select(models.TMovInventario).where(
                        models.TMovInventario.tipo_movimiento == "salida"
                    )
                )
            )
            .scalars()
            .all()
        )
        assert sum(s.cantidad for s in salidas) == Decimal("15.000")
        assert len(salidas) == 2  # 10 del cercano + 5 del lejano

    async def test_allocate_insuficiente_422(self, app_client, admin_a, catalog_a):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        resp = await app_client.post(
            "/api/v1/inventory/allocate",
            json={"articulo_id": str(catalog_a["art"].id), "cantidad": "999.000"},
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 422


class TestT5RlsDisjoint:
    """T5 rls_disjoint: Admin A vs B listan artículos → conjuntos disjuntos; A GET id de B → 404."""

    async def test_admins_ven_solo_su_tenant(
        self,
        app_client,
        db_session,
        tenant_a,
        tenant_b,
        admin_a,
        admin_b,
    ):
        from tests.fixtures.seed_data import seed_catalog_with_lotes

        cat_a = await seed_catalog_with_lotes(db_session, tenant_a, sku="ART-A")
        cat_b = await seed_catalog_with_lotes(db_session, tenant_b, sku="ART-B")
        # IDs capturados ANTES de cualquier request: un 404 (NotFound) provoca
        # rollback y expira los objetos del identity map (acceso lazy = error)
        art_a_id = cat_a["art"].id
        art_b_id = cat_b["art"].id

        tokens_a = await login(app_client, "admin_a", "AdminA123!")
        tokens_b = await login(app_client, "admin_b", "AdminB123!")

        list_a = await app_client.get(
            "/api/v1/catalog/articulos", headers=bearer(tokens_a["access_token"])
        )
        list_b = await app_client.get(
            "/api/v1/catalog/articulos", headers=bearer(tokens_b["access_token"])
        )
        ids_a = {a["id"] for a in list_a.json()}
        ids_b = {a["id"] for a in list_b.json()}

        # Conjuntos disjuntos
        assert ids_a and ids_b
        assert ids_a.isdisjoint(ids_b)
        assert {a["sku"] for a in list_a.json()} == {"ART-A"}
        assert {a["sku"] for a in list_b.json()} == {"ART-B"}

        # A GET id de B → 404
        resp_cross = await app_client.get(
            f"/api/v1/catalog/articulos/{art_b_id}",
            headers=bearer(tokens_a["access_token"]),
        )
        assert resp_cross.status_code == 404

        # B GET id de A → 404
        resp_cross_b = await app_client.get(
            f"/api/v1/catalog/articulos/{art_a_id}",
            headers=bearer(tokens_b["access_token"]),
        )
        assert resp_cross_b.status_code == 404

        # Cada uno ve el suyo → 200
        resp_own = await app_client.get(
            f"/api/v1/catalog/articulos/{art_a_id}",
            headers=bearer(tokens_a["access_token"]),
        )
        assert resp_own.status_code == 200
