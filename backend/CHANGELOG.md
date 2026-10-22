# Changelog — PapelMaind

## [2.3.0] — 2026-10-18

### Canon
- v2.3.0 consolidado: PapelMind → **PapelMaind**, CRM Omnicanal Unificado,
  Motor BYO-LLM (Kimi, Qwen, DeepSeek, Claude, OpenAI, local), Handoff a humano.
- Well-formed + `canon_lint.py` L1-L6 → **0 issues** (escapes `<`/`&` en SQL
  reparados, `<prompt canon="true">`).
- CI gate F28 activo (`.github/workflows/canon-lint.yml`).

### Sprint 1 — Fundación (DONE)
- Auth multi-tenant: login → lista tenants → selección EXPLÍCITA → JWT.
- Access 15 min + refresh **ROTACIÓN one-time-use** (hash SHA-256).
- GET /auth/me, POST /auth/refresh, GET /tenants/mine.
- Modelos S1 + RLS (migración 0001_s1 PostgreSQL; SQLite dev con RLS emulado).
- Seed idempotente: 2 tenants (central/norte), admin_a/AdminA123!,
  admin_b/AdminB123!, cajero01, sucursal, caja, estación POS.

### Sprint 2 — Catálogo + Inventario (DONE)
- CRUD unidades de medida, impuestos (iva/ieps/exento), artículos
  (UNIQUE(papeleria_id, sku)).
- Recepción de mercancía: POST /inventory/lotes → lote + tmovinventario
  'entrada' + stock_actual.
- **FEFO allocator** (código canon): consumo por vencimiento ascendente,
  estados disponible→parcial→agotado, métrica de latencia.
- Migración 0002_s2 con RLS + vista vw_stock_sucursal.

### Sprint 3 — POS Transaccional (DONE)
- **POST /pos/ventas**: venta ACID única TX = reclamo client_uuid
  (CONV-13: INSERT ON CONFLICT DO NOTHING, NUNCA SELECT previo) +
  hard-allocate FEFO por partida + pagos (mixto validado) + historial +
  **outbox sale.completed en la misma TX** (CONV-06).
- **Idempotencia offline-first** (CONV-12): replay del mismo client_uuid →
  200 con la venta original, cero efectos duplicados (venta/outbox/movs).
- Folio secuencial por tenant (V-000001…), totales con IVA por partida
  (override de precio soportado).
- GET /pos/ventas/{id} + GET /pos/ventas (tenant-scoped, 404 cruzado).
- **OutboxService F17** (código canon): flags separados
  `publicado_kafka` / `procesado_loyalty`, jamás un 'procesado' único.
- **Workers S3**: outbox_worker (P0: gauge erp_outbox_pending_events_count,
  alerta A1; Kafka en P1), loyalty_worker (polling idx_outbox_loyalty_p0,
  error de dominio → DLQ), dlq_consumer (reintento resuelto/reintentado +
  descarte auditado DLQ_DISCARD).
- Modelos: TDetalleVenta, TPagoVenta, THistorialVentas, TDlqEvento.
- Migración 0003_s3: 6 tablas + RLS FORCE + índices parciales F17
  (idx_outbox_loyalty_p0 / idx_outbox_kafka_p1) + GRANT erp_worker.
- Fix conftest: override get_db ahora replica commit/rollback de producción
  (expuso estado sucio en requests 4xx que ensuciaba tests posteriores).
- Fix CI-latente: scripts/canon_lint.py tenía 48 errores ruff (CI corre
  `ruff check .` en la raíz) — corregidos sin cambio de comportamiento.

### Tests (CHK-11/CHK-12)
- Suite pytest: **39 passed** — auth flow (login/me/refresh/roles),
  catálogo, inventario, **T1 idempotencia_venta**, **T2 fefo_orden**,
  **T3 concurrencia_ultimo** (201+422, sin sobreventa), **T4 rollback
  atómico** (cero filas huérfanas), outbox F17 (misma TX, flags, DLQ
  resolve/discard), **T5 rls_disjoint** (extendido a ventas),
  **T10 cfdi_pac_fallback** (PacClient primary→fallback con httpx mock).
- Smoke E2E bash: **15/15** (health→login→me→refresh→catálogo→lotes→FEFO→RLS).
- Stubs de prueba T11 (WhatsApp, S5) y T12 (sweeper, S8) reservados.

### Infra
- docker-compose (API 8000 · PG 5433 · Redis) + compose prod + Dockerfile.
- Init-scripts PG: extensiones, roles erp_app/erp_worker, funciones tenant, RLS suite.
- Prometheus config + alertas núcleo. Makefile completo (canon Sección 11).
