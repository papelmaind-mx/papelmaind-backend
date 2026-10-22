# Setup — PapelMaind

## Requisitos

- **Sin Docker (dev)**: Python 3.12+ (SQLite, RLS emulado en capa app)
- **Con Docker (prod-like)**: Docker + docker compose (PostgreSQL 16, Redis 7)

## Opción A — Dev local sin Docker

```bash
cd backend
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# uvicorn ejecuta migrate + seed automáticamente al iniciar (modo SQLite):
uvicorn src.main:app --reload --port 8000
```

Credenciales sembradas (idempotente):

| Usuario | Contraseña | Tenant | Rol |
|---------|-----------|--------|-----|
| admin_a | AdminA123! | Papelería Central (central) | admin |
| admin_b | AdminB123! | Librería del Norte (norte) | admin |
| cajero01 | Cajero123! | Papelería Central | cajero |

- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/api/v1/health
- Métricas: http://localhost:8000/api/v1/metrics

## Opción B — Docker (PostgreSQL 16 con RLS real)

```bash
cp .env.example .env         # genera JWT_SECRET: openssl rand -hex 32
docker compose up -d         # API :8000 · PG :5433 · Redis :6379
docker compose exec api python -m src.infrastructure.db.migrate apply
docker compose exec api python -m src.infrastructure.db.seed
```

> Nota: el host de este entorno solo tiene Python 3.14 (greenlet no compila);
> el contenedor usa Python 3.12 (canon). En dev local ya usamos 3.12 nativo.

## Tests y calidad

```bash
cd backend
python -m pytest                                    # 25 tests (T2, T5, T10 incluidos)
python -m pytest --cov=src --cov-report=term        # cobertura
bash tests/smoke/smoke_test.sh                      # smoke E2E 15 checks (API arriba)

cd .. && make canon-lint                            # F28 gate del canon
```

## Migraciones

- **SQLite (dev)**: `Base.metadata` automático al arrancar.
- **PostgreSQL (prod)**: `backend/migrations/*.sql` en orden +
  `docker/init-scripts/` (extensiones → roles → funciones → RLS suite).
  Registro en tabla `schema_migrations`.

## Solución de problemas

| Síntoma | Causa | Solución |
|---------|-------|----------|
| `Could not parse SQLAlchemy URL` | `DATABASE_URL` ambiental inválida (p.ej. `file:/...`) | Se ignora automáticamente; define `sqlite+aiosqlite://` o `postgresql+asyncpg://` |
| `password cannot be longer than 72 bytes` | bcrypt ≥ 4.1 con passlib 1.7.4 | `pip install bcrypt==4.0.1` (ya fijado en requirements) |
| 401 en todos los requests | token vencido (15 min) | `POST /auth/refresh` (rotación) |
| 404 con id válido | es de OTRO tenant (T5, comportamiento correcto) | usa recursos del tenant del JWT |
