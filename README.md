# PapelMaind — Plataforma Omnicanal Multi-Tenant para Cadenas de Papelerías

> **PapelMaind Tecnología Omnicanal S.A. de C.V.** · papelmaind.com · Canon v2.3.0 · 2026-10-18

SaaS multi-tenant (RLS) para cadenas de papelerías de giro mixto: POS offline-first,
e-commerce local, CRM omnicanal con IA (BYO-LLM), WhatsApp RAG, calendario de citas,
CFDI 4.0 PAC-first, logística local y guía de compras GEO/AEO.

**Nombre del producto: PapelMaind** (antes PapelMind — el tag raíz del canon
`<papelmind_context_engineer>` se conserva como identificador legado documentado).

## Estado de sprints (roadmap canon P0-núcleo → P3)

| Sprint | Alcance | Estado |
|--------|---------|--------|
| **S1 Fundación** | Auth multi-tenant, JWT (access 15min + refresh ROTACIÓN), roles, RLS, sesiones, seed | ✅ DONE — 25 tests verdes, smoke 15/15 |
| **S2 Catálogo + Inventario** | Unidades, impuestos, artículos, lotes, movimientos, **FEFO allocator**, T2/T5 verificados | ✅ DONE |
| S3-S3.5 POS | Venta transaccional, outbox F17, idempotencia (T1, T3, T4), DLQ | ⏭ siguiente |
| S4-S4.5 | Caja, apartados (T7), kiosco (T9) | pendiente |
| S5-S6 | CRM omnicanal, WhatsApp (T11), loyalty, alertas | pendiente |
| S7-S8 | CFDI PAC fallback (T10 lógica ya implementada y testeada), e-commerce (T6), sweeper (T12) | pendiente |

### Gate de calidad (canon Sección 12 — CHK)

- ✅ `canon_lint.py` → **0 issues** (F28: gate obligatorio pre-merge)
- ✅ pytest → **25 passed** (incluye T2 fefo_orden, T5 rls_disjoint, T10 cfdi_pac_fallback)
- ✅ smoke test E2E → **15/15** contra servidor real
- ✅ ruff → limpio
- ✅ Migraciones 0001_s1 + 0002_s2 (PostgreSQL 16 + RLS real) y schema automático SQLite dev

## Arquitectura (resumen)

```
FastAPI 0.115+ · Python 3.12 · SQLAlchemy 2.0 Async · PyJWT · passlib/bcrypt
PostgreSQL 16 (RLS + UUID v7 + JSONB) · Redis 7 · Transactional Outbox
api/ → application/ → domain/ → infrastructure/   (CONV-05 Clean Architecture)
```

- **Multi-tenant**: `papelerias` = tenant. PostgreSQL con políticas RLS
  (`app.current_tenant_id`) en producción; en desarrollo sin Docker se usa
  **SQLite con RLS emulado en capa aplicación** (mismo contrato, testeado por T5).
- **Login multi-tenant** (canon): credenciales → lista de tenants → selección
  EXPLÍCITA → JWT `{sub, tenant_id, role, rel_id}` + refresh opaco con
  **rotación one-time-use** (hash SHA-256 en `usuario_sesiones`).
- **FEFO**: `allocate_stock_fefo()` consume lotes por vencimiento ascendente;
  único punto que consume lotes (F20). Métrica `erp_fefo_allocation_latency_seconds`.
- **POS transaccional (S3)**: `POST /pos/ventas` = una TX ACID (venta + FEFO +
  pagos + outbox `sale.completed`). **Idempotente por `client_uuid`** (CONV-12/13,
  offline-first): replay → 200 con la venta original, sin efectos duplicados.
- **Transactional Outbox F17**: flags separados por consumidor
  (`publicado_kafka` / `procesado_loyalty`); loyalty_worker (polling P0) con
  **DLQ** para errores de dominio (`tdlq_eventos`: reintento + descarte auditado).

## Arranque rápido

### Sin Docker (dev local — SQLite)

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn src.main:app --reload --port 8000
# → migrate + seed automáticos: admin_a / AdminA123! (tenant central) · admin_b / AdminB123! (tenant norte)
# Docs interactivas: http://localhost:8000/docs
```

### Con Docker (producción — PostgreSQL 16 + RLS real + Redis)

```bash
cp .env.example .env   # ajustar JWT_SECRET
docker compose up -d   # API :8000 · PostgreSQL :5433 · Redis :6379
docker compose exec api python -m src.infrastructure.db.migrate apply
docker compose exec api python -m src.infrastructure.db.seed
```

### Comandos Makefile (canon Sección 11)

```bash
make dev         # API hot-reload
make test        # suite pytest (39 tests)
make seed        # seed idempotente (2 tenants, 3 usuarios, catálogo base)
make canon-lint  # F28 gate del canon XML (debe estar en 0)
make smoke       # smoke E2E (requiere API arriba)
make lint        # ruff
```

## Estructura del repositorio

```
papelmaind/
├── docs/canon/papelmaind_context_engineer_v2.2.3.xml   # CANON (fuente de verdad)
├── scripts/canon_lint.py                                # Lint F28 (L1-L6)
├── backend/
│   ├── src/core/                    # config, security, logging, metrics, exceptions
│   ├── src/api/v1/                  # routers: health, auth, tenants, catalog, inventory, pos + stubs S3.5+
│   ├── src/application/services/    # auth_service, fefo_allocator, sale_service, outbox_service
│   ├── src/infrastructure/db/       # session dual, TenantUnitOfWork, migrate, seed, models
│   ├── src/infrastructure/workers/  # outbox/loyalty/dlq (S3) · cfdi (PAC fallback T10) + stubs canon
│   ├── migrations/                  # 0001_s1 · 0002_s2 · 0003_s3 (PostgreSQL + RLS)
│   └── tests/                       # e2e (T1-T5) · integration (T10) · smoke · fixtures
├── docker/init-scripts/             # extensions, roles, funciones, RLS suite
├── docker/prometheus/               # métricas + alertas
├── frontend/{pos,web,checkout,kiosco}/   # Sprint 3.5+ (estructura canon reservada)
└── .github/workflows/               # ci.yml · cd.yml · canon-lint.yml (F28)
```

## Seguridad

- Access token 15 min · refresh 24 h con **rotación estricta** (replay → 401)
- Contraseñas bcrypt (rounds=12) · claims `{sub, tenant_id, role, rel_id, jti}`
- Aislamiento por tenant verificado por **T5 rls_disjoint** (conjuntos disjuntos + 404 cruzado)
- Roles canon: superadmin · admin · cajero · contador · cliente · system

## Gobernanza del canon

El XML en `docs/canon/` es la **única fuente de verdad**. Todo cambio pasa por
`make canon-lint` (F28) y RFC-lite (CHK-34). Prohibido declarar DONE con checks
en rojo (canon Sección 12).

## Licencia

**Propietaria** — © 2026 PapelMaind Tecnología Omnicanal S.A. de C.V.
Todos los derechos reservados (ver `LICENSE`). Marca en trámite ante el IMPI.

<!-- bootstrap-docs:start -->
## 🧠 Sistema de conocimiento interno

Capas: **RAM** (dev-log local) → **Disco** (notas BuJo `NXX`) → **BIOS** (runbooks `RB-XX`).

- Arquitectura: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Automatización y skills: [`docs/AUTOMATIZACION-AI-SKILLS.md`](docs/AUTOMATIZACION-AI-SKILLS.md)
- Índice de notas: [`docs/bujo/INDEX.md`](docs/bujo/INDEX.md)
- Comandos rápidos: `make help` · `./scripts/bujo new|open|index|list`
<!-- bootstrap-docs:end -->
