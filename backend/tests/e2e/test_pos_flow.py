"""Suite E2E Sprint 3 — POS transaccional.

T1 idempotencia_venta: mismo client_uuid → replay sin efectos duplicados.
T3 concurrencia_ultimo: 2 ventas del último stock → 1 éxito (201) + 1 controlado (422).
T4 rollback_atomico: fallo a mitad de venta → TODO revierte (sin filas huérfanas).
Outbox F17: sale.completed en la misma TX + flags separados + DLQ de dominio.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select

from src.infrastructure.db import models
from src.infrastructure.workers import dlq_consumer, loyalty_worker
from tests.conftest import bearer, login


def _sale_payload(articulo_id, cantidad="2.000", client_uuid=None, **overrides):
    payload = {
        "client_uuid": str(client_uuid or uuid4()),
        "items": [{"articulo_id": str(articulo_id), "cantidad": cantidad}],
        "metodo_pago": "efectivo",
        "origen": "pos",
    }
    payload.update(overrides)
    return payload


class TestT1IdempotenciaVenta:
    """T1: venta idempotente por client_uuid (CONV-12/13, ON CONFLICT DO NOTHING)."""

    async def test_replay_mismo_client_uuid_sin_duplicados(
        self, app_client, db_session, admin_a, catalog_a
    ):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        art_id = str(catalog_a["art"].id)
        c_uuid = str(uuid4())

        # Primera llamada → 201
        resp1 = await app_client.post(
            "/api/v1/pos/ventas",
            json=_sale_payload(art_id, "2.000", c_uuid),
            headers=bearer(tokens["access_token"]),
        )
        assert resp1.status_code == 201, resp1.text
        body1 = resp1.json()
        assert body1["folio"] == "V-000001"
        assert body1["replayed"] is False
        # 2 × 35.50 = 71.00 + IVA 16% (11.36) = 82.36
        assert body1["subtotal"] == "71.00"
        assert body1["impuestos"] == "11.36"
        assert body1["total"] == "82.36"

        # Replay mismo client_uuid → 200, misma venta
        resp2 = await app_client.post(
            "/api/v1/pos/ventas",
            json=_sale_payload(art_id, "2.000", c_uuid),
            headers=bearer(tokens["access_token"]),
        )
        assert resp2.status_code == 200, resp2.text
        body2 = resp2.json()
        assert body2["replayed"] is True
        assert body2["id"] == body1["id"]
        assert body2["folio"] == body1["folio"]

        # Efectos aplicados EXACTAMENTE una vez
        ventas = (await db_session.execute(select(models.TVenta))).scalars().all()
        assert len(ventas) == 1
        outbox = (
            await db_session.execute(
                select(models.OutboxEvento).where(
                    models.OutboxEvento.client_uuid == UUID(c_uuid)
                )
            )
        ).scalars().all()
        assert len(outbox) == 1
        salidas = (
            await db_session.execute(
                select(models.TMovInventario).where(
                    models.TMovInventario.tipo_movimiento == "salida"
                )
            )
        ).scalars().all()
        assert sum(s.cantidad for s in salidas) == Decimal("2.000")

    async def test_dos_client_uuid_distintos_dos_ventas(
        self, app_client, db_session, admin_a, catalog_a
    ):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        art_id = str(catalog_a["art"].id)
        headers = bearer(tokens["access_token"])

        r1 = await app_client.post(
            "/api/v1/pos/ventas", json=_sale_payload(art_id, "2.000"), headers=headers
        )
        r2 = await app_client.post(
            "/api/v1/pos/ventas", json=_sale_payload(art_id, "2.000"), headers=headers
        )
        assert (r1.status_code, r2.status_code) == (201, 201)
        assert r1.json()["folio"] != r2.json()["folio"]
        folios = [r1.json()["folio"], r2.json()["folio"]]
        assert folios == ["V-000001", "V-000002"]

    async def test_venta_multilinea_con_lotes_fefo(
        self, app_client, db_session, admin_a, catalog_a
    ):
        """15 uds agotan lote cercano (10) y dejan lejano parcial (15/20) — venta vía POS."""
        tokens = await login(app_client, "admin_a", "AdminA123!")
        art_id = str(catalog_a["art"].id)

        resp = await app_client.post(
            "/api/v1/pos/ventas",
            json=_sale_payload(art_id, "15.000"),
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        # El detalle fija el lote de vencimiento más cercano (trazabilidad FEFO)
        assert body["items"][0]["lote_id"] == str(catalog_a["lote_cercano"].id)
        assert body["subtotal"] == "532.50"  # 15 × 35.50
        assert body["impuestos"] == "85.20"
        assert body["total"] == "617.70"

        cercano = await db_session.get(models.TLote, catalog_a["lote_cercano"].id)
        lejano = await db_session.get(models.TLote, catalog_a["lote_lejano"].id)
        assert cercano.estado == "agotado"
        assert lejano.estado == "parcial"
        assert lejano.cantidad_actual == Decimal("15.000")


class TestT3ConcurrenciaUltimoArticulo:
    """T3: dos ventas por el último stock → exactamente una gana."""

    async def test_un_exito_un_422(
        self, app_client, db_session, admin_a, catalog_a
    ):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        art_id = str(catalog_a["art"].id)
        headers = bearer(tokens["access_token"])

        # Agotar hasta dejar 1 unidad
        resp = await app_client.post(
            "/api/v1/pos/ventas", json=_sale_payload(art_id, "29.000"), headers=headers
        )
        assert resp.status_code == 201, resp.text

        # Dos cajeros por la última unidad (client_uuid distintos)
        r_a = await app_client.post(
            "/api/v1/pos/ventas", json=_sale_payload(art_id, "1.000"), headers=headers
        )
        r_b = await app_client.post(
            "/api/v1/pos/ventas", json=_sale_payload(art_id, "1.000"), headers=headers
        )
        codigos = sorted([r_a.status_code, r_b.status_code])
        assert codigos == [201, 422], (r_a.text, r_b.text)

        art = await db_session.get(models.TArticulo, UUID(art_id))
        assert art.stock_actual == Decimal("0.000")
        # Sin sobreventa: salidas totales == 30
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
        assert sum(s.cantidad for s in salidas) == Decimal("30.000")
        # La venta fallida NO dejó rastro (ni venta ni outbox zombi)
        exitosas = (await db_session.execute(select(models.TVenta))).scalars().all()
        assert len(exitosas) == 2  # la de 29 + la ganadora de 1


class TestT4RollbackAtomico:
    """T4 atomicidad: fallo en cualquier partida revierte TODA la venta."""

    async def test_venta_con_partida_imposible_no_deja_huerfanos(
        self, app_client, db_session, admin_a, catalog_a
    ):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        art_id = str(catalog_a["art"].id)
        lote_cercano_id = catalog_a["lote_cercano"].id
        headers = bearer(tokens["access_token"])
        await db_session.commit()  # fixture visible a la TX fallida (rollback limpio)

        # Partida 1 OK (2 uds) + partida 2 imposible (999 uds) → 422 global
        payload = {
            "client_uuid": str(uuid4()),
            "items": [
                {"articulo_id": art_id, "cantidad": "2.000"},
                {"articulo_id": art_id, "cantidad": "999.000"},
            ],
            "metodo_pago": "efectivo",
        }
        resp = await app_client.post("/api/v1/pos/ventas", json=payload, headers=headers)
        assert resp.status_code == 422, resp.text

        # Nada quedó: sin venta, sin detalle, sin pagos, sin outbox, sin movimientos
        assert (await db_session.execute(select(models.TVenta))).scalars().first() is None
        assert (
            await db_session.execute(select(models.TDetalleVenta))
        ).scalars().first() is None
        assert (await db_session.execute(select(models.TPagoVenta))).scalars().first() is None
        assert (await db_session.execute(select(models.OutboxEvento))).scalars().first() is None
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
        assert salidas == []
        # Stock intacto
        art = await db_session.get(models.TArticulo, UUID(art_id))
        assert art.stock_actual == Decimal("30.000")
        cercano = await db_session.get(models.TLote, lote_cercano_id)
        assert cercano.cantidad_actual == Decimal("10.000")

    async def test_pagos_insuficientes_422(
        self, app_client, db_session, admin_a, catalog_a
    ):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        await db_session.commit()  # fixture comprometida antes del rollback
        art_id = str(catalog_a["art"].id)
        payload = {
            "client_uuid": str(uuid4()),
            "items": [{"articulo_id": art_id, "cantidad": "1.000"}],
            "metodo_pago": "mixto",
            "pagos": [
                {"tipo": "efectivo", "monto": "1.00"},
                {"tipo": "tarjeta", "monto": "2.00"},
            ],  # 3.00 < 41.18
        }
        resp = await app_client.post(
            "/api/v1/pos/ventas",
            json=payload,
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 422
        assert (await db_session.execute(select(models.TVenta))).scalars().first() is None

    async def test_mixto_sin_desglose_422(self, app_client, admin_a, catalog_a):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        payload = {
            "client_uuid": str(uuid4()),
            "items": [{"articulo_id": str(catalog_a["art"].id), "cantidad": "1.000"}],
            "metodo_pago": "mixto",
        }
        resp = await app_client.post(
            "/api/v1/pos/ventas",
            json=payload,
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 422

    async def test_pago_mixto_valido_201(self, app_client, db_session, admin_a, catalog_a):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        payload = {
            "client_uuid": str(uuid4()),
            "items": [{"articulo_id": str(catalog_a["art"].id), "cantidad": "1.000"}],
            "metodo_pago": "mixto",
            "pagos": [
                {"tipo": "efectivo", "monto": "20.00"},
                {"tipo": "tarjeta", "monto": "21.18"},
            ],  # 41.18 == total (35.50 + 5.68)
        }
        resp = await app_client.post(
            "/api/v1/pos/ventas",
            json=payload,
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 201, resp.text
        pagos = (await db_session.execute(select(models.TPagoVenta))).scalars().all()
        assert len(pagos) == 2


class TestOutboxF17:
    """sale.completed en la misma TX + flags separados + DLQ de dominio."""

    async def test_outbox_evento_en_misma_tx(
        self, app_client, db_session, admin_a, catalog_a
    ):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        c_uuid = str(uuid4())
        resp = await app_client.post(
            "/api/v1/pos/ventas",
            json=_sale_payload(str(catalog_a["art"].id), "1.000", c_uuid),
            headers=bearer(tokens["access_token"]),
        )
        assert resp.status_code == 201, resp.text

        eventos = (
            await db_session.execute(select(models.OutboxEvento))
        ).scalars().all()
        assert len(eventos) == 1
        ev = eventos[0]
        assert ev.tipo == "sale.completed"
        assert ev.aggregate_type == "sale"
        assert str(ev.client_uuid) == c_uuid
        # F17: flags separados, ambos false al nacer
        assert ev.procesado_loyalty is False
        assert ev.publicado_kafka is False
        assert ev.payload["folio"] == "V-000001"

    async def test_loyalty_worker_procesa_y_marca(
        self, app_client, db_session, admin_a, catalog_a
    ):
        tokens = await login(app_client, "admin_a", "AdminA123!")
        await app_client.post(
            "/api/v1/pos/ventas",
            json=_sale_payload(str(catalog_a["art"].id), "1.000"),
            headers=bearer(tokens["access_token"]),
        )
        stats = await loyalty_worker.run_once(db_session)
        await db_session.commit()
        assert stats == {"procesados": 1, "a_dlq": 0}

        ev = (
            await db_session.execute(select(models.OutboxEvento))
        ).scalars().one()
        assert ev.procesado_loyalty is True
        assert ev.procesado_en is not None
        assert ev.publicado_kafka is False  # intacto: checkpoint de OTRO consumidor

        # Idempotente: segundo ciclo no re-procesa
        stats2 = await loyalty_worker.run_once(db_session)
        await db_session.commit()
        assert stats2 == {"procesados": 0, "a_dlq": 0}

    async def test_error_dominio_va_a_dlq_y_se_resuelve(
        self, app_client, db_session, admin_a, catalog_a
    ):
        # Evento corrupto (payload sin 'items') — como si un bug lo hubiera encolado
        db_session.add(
            models.OutboxEvento(
                papeleria_id=admin_a[1].papeleria_id,
                tipo="sale.completed",
                aggregate_type="sale",
                aggregate_id=str(uuid4()),
                payload={"venta_id": "x", "folio": "V-BAD", "total": "1.00"},  # sin items
            )
        )
        await db_session.commit()

        stats = await loyalty_worker.run_once(db_session)
        await db_session.commit()
        assert stats["a_dlq"] == 1

        dlq = (
            await db_session.execute(select(models.TDlqEvento))
        ).scalars().one()
        assert dlq.estado == "pendiente"
        assert "items" in (dlq.error_ultimo or "")

        # El evento no se reintenta en ciclos siguientes (ya está en DLQ)
        stats2 = await loyalty_worker.run_once(db_session)
        await db_session.commit()
        assert stats2["procesados"] == 0

        # Reparación + reintento admin → resuelto + checkpoint del outbox
        evento = (
            await db_session.execute(select(models.OutboxEvento))
        ).scalars().one()
        evento.payload = {
            "venta_id": "x",
            "folio": "V-BAD",
            "total": "1.00",
            "items": [{"articulo_id": "a", "cantidad": "1", "precio_unitario": "1.00"}],
        }
        await db_session.commit()

        resuelto = await dlq_consumer.retry_dlq_event(db_session, dlq.id)
        await db_session.commit()
        assert resuelto.estado == "resuelto"
        assert evento.procesado_loyalty is True

    async def test_descarte_dlq_auditado(
        self, app_client, db_session, admin_a, catalog_a
    ):
        db_session.add(
            models.OutboxEvento(
                papeleria_id=admin_a[1].papeleria_id,
                tipo="sale.completed",
                aggregate_type="sale",
                aggregate_id=str(uuid4()),
                payload={"folio": "x"},  # inválido
            )
        )
        await db_session.commit()
        await loyalty_worker.run_once(db_session)
        await db_session.commit()

        dlq = (
            await db_session.execute(select(models.TDlqEvento))
        ).scalars().one()
        descartado = await dlq_consumer.discard_dlq_event(
            db_session,
            dlq.id,
            motivo="Datos corruptos irreparables",
            usuario_id=str(admin_a[0].id),
        )
        await db_session.commit()
        assert descartado.estado == "descartado"
        assert descartado.motivo_descarte == "Datos corruptos irreparables"
        assert descartado.descartado_por == admin_a[0].id


class TestVentasRls:
    """Aislamiento tenant en ventas (RLS emulado, misma familia que T5)."""

    async def test_venta_de_otro_tenant_404(
        self, app_client, admin_a, admin_b, catalog_a, tenant_b, catalog_b_for_tenant_b
    ):
        tokens_a = await login(app_client, "admin_a", "AdminA123!")
        resp = await app_client.post(
            "/api/v1/pos/ventas",
            json=_sale_payload(str(catalog_a["art"].id), "1.000"),
            headers=bearer(tokens_a["access_token"]),
        )
        assert resp.status_code == 201
        venta_id = resp.json()["id"]

        tokens_b = await login(app_client, "admin_b", "AdminB123!")
        resp_b = await app_client.get(
            f"/api/v1/pos/ventas/{venta_id}",
            headers=bearer(tokens_b["access_token"]),
        )
        assert resp_b.status_code == 404

        lista_b = await app_client.get(
            "/api/v1/pos/ventas", headers=bearer(tokens_b["access_token"])
        )
        assert lista_b.status_code == 200
        assert lista_b.json() == []

    async def test_cajero_puede_vender_contador_no_puede_crear(
        self, app_client, db_session, tenant_a, admin_a, catalog_a
    ):
        from tests.conftest import _make_user

        cajero, _ = await _make_user(db_session, "cajero_a", "Cajero123!", tenant_a, "cajero")
        contador, _ = await _make_user(db_session, "contador_a", "Conta123!", tenant_a, "contador")

        tok_cajero = await login(app_client, "cajero_a", "Cajero123!")
        r = await app_client.post(
            "/api/v1/pos/ventas",
            json=_sale_payload(str(catalog_a["art"].id), "1.000"),
            headers=bearer(tok_cajero["access_token"]),
        )
        assert r.status_code == 201, r.text

        tok_conta = await login(app_client, "contador_a", "Conta123!")
        r2 = await app_client.post(
            "/api/v1/pos/ventas",
            json=_sale_payload(str(catalog_a["art"].id), "1.000"),
            headers=bearer(tok_conta["access_token"]),
        )
        assert r2.status_code == 403
