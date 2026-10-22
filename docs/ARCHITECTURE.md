# Arquitectura — PapelMaind

## Capas (CONV-05 Clean Architecture)

```
┌────────────────────────────────────────────────────────────┐
│ api/v1/            HTTP: routers FastAPI + schemas Pydantic │
│                    HTTPException SOLO aquí                  │
├────────────────────────────────────────────────────────────┤
│ application/       Casos de uso: AuthService, FEFOAllocator │
├────────────────────────────────────────────────────────────┤
│ domain/            Errores + invariantes (core.exceptions)  │
├────────────────────────────────────────────────────────────┤
│ infrastructure/    db (session dual, UoW, models), workers   │
└────────────────────────────────────────────────────────────┘
```

## Multi-tenant + RLS

- **Producción (PostgreSQL 16)**: cada request autenticado ejecuta
  `SELECT set_config('app.current_tenant_id', :tid, true)` (transaccional).
  Las políticas RLS (migraciones 0001/0002 + docker/init-scripts/04) filtran
  TODA tabla con `papeleria_id`.
- **Dev/test sin Docker (SQLite)**: `TenantUnitOfWork` registra el tenant en
  `session.info['tenant_id']` y cada endpoint filtra explícitamente por
  `papeleria_id == current_user.tenant_id` (RLS emulado). El contrato es el
  mismo y lo verifica el test T5 (conjuntos disjuntos + 404 cruzado).

### Roles (canon `<roles_canon>`)

superadmin (cruza tenants + audit obligatorio) · admin (tenant completo) ·
cajero · contador (solo reportes) · cliente · system (workers).

## Autenticación

```
POST /api/v1/auth/login {username, password}
   ├─ 1 tenant  → 200 {access_token, refresh_token}
   └─ N tenants → 200 {requires_selection, tenants[]}   ← selección EXPLÍCITA
POST /api/v1/auth/login {username, password, papeleria_id} → tokens (JWT: sub, tenant_id, role, rel_id, jti)
POST /api/v1/auth/refresh {refresh_token} → NUEVO par (rotación one-time-use; replay → 401)
GET  /api/v1/auth/me (Bearer) → perfil + tenant activo
```

- Access 15 min (HS256). Refresh opaco 48 bytes, hash SHA-256 en `usuario_sesiones`.
- Purga automática de sesiones expiradas en cada rotación.

## Inventario y FEFO (F20)

- **Catálogo por tenant** (`tarticulos` sin sucursal — CONV-17).
- **Stock por sucursal**: la verdad dura vive en `tlotes`;
  `vw_stock_sucursal` agrega disponibilidad.
- `allocate_stock_fefo()` (application/services) es el **ÚNICO** punto que
  consume lotes: ordena por `fecha_vencimiento ASC`, with_for_update,
  registra `tmovinventario` tipo 'salida', marca estados
  disponible → parcial → agotado, decrementa `stock_actual` del artículo.
- Reserva blanda de carrito (S8): `tarticulos.stock_reservado` TTL 15min,
  liberada por `reservation_sweeper` al mismo nivel (artículo).

## Eventos (P0 → P1)

- P0: Transactional Outbox + polling `FOR UPDATE SKIP LOCKED` (workers).
- P1: Kafka KRaft + JSON Schema por evento (Anexo S mapea enums DB ↔ eventos).

## CFDI (S7) — patrón PAC fallback (T10)

`PacClient.timbrar()` → PAC_PRIMARY (reintentos exponenciales) → si cae,
PAC_FALLBACK → timbrado. Ambos caídos → `PacUnavailableError` (→ DLQ).
La lógica ya está implementada y testeada (tests/integration/test_cfdi_pac_fallback.py);
la orquestación del worker llega con S7.
