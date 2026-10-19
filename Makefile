x# ==============================================================================
# Canon Lint (F28)
# ==============================================================================
canon-lint:  ## Validar el canon XML contra sí mismo (CI gate F28)
	@XML_FILE=$$(ls -t context-engineer/papel*mind_context_engineer_v*.xml 2>/dev/null | head -1); \
	if [ -z "$$XML_FILE" ]; then \
		echo "❌ No se encontró XML canon en context-engineer/"; \
		exit 1; \
	fi; \
	echo "🔍 Linteando: $$XML_FILE"; \
	python3 scripts/canon_lint.py --verbose "$$XML_FILE"

canon-validate:  ## Solo validar XML well-formed
	@XML_FILE=$$(ls -t context-engineer/papel*mind_context_engineer_v*.xml 2>/dev/null | head -1); \
	xmllint --noout "$$XML_FILE" && echo "✅ XML well-formed"

canon-stats:  ## Estadísticas del canon
	@XML_FILE=$$(ls -t context-engineer/papel*mind_context_engineer_v*.xml 2>/dev/null | head -1); \
	echo "📊 Estadísticas:"; \
	echo "   Archivo: $$XML_FILE"; \
	echo "   Líneas:  $$(wc -l < $$XML_FILE)"; \
	echo "   Modelos: $$(grep -c '<modelo ' $$XML_FILE)"; \
	echo "   Workers: $$(grep -c '<worker ' $$XML_FILE)"

# ==============================================================================
# Sprint 1
# ==============================================================================
up: ## Levanta postgres + redis + api
	docker compose up -d

down: ## Baja todo
	docker compose down

migrate: ## Migraciones como admin
	cd backend && ADMIN_DATABASE_URL=postgresql+asyncpg://admin:admin_dev@localhost:5432/papelmind alembic upgrade head

seed: ## Seed S1
	cd backend && python3 scripts/seed_s1.py

dev: ## API local
	cd backend && uvicorn src.main:app --reload --port 8000

test-s1: ## Suite T5/T10
	cd backend && TEST_DATABASE_URL=postgresql+asyncpg://admin:admin_dev@localhost:5432/papelmind python3 -m pytest tests/ -v

# ==============================================================================
# Sprint 1 — Docker (Python 3.12 en contenedor; host puede ser 3.14)
# ==============================================================================
s1-up: ## Postgres + Redis
	docker compose up -d postgres redis

s1-build: ## Build API (Python 3.12)
	docker compose build api

s1-migrate: ## Alembic upgrade head
	docker compose run --rm \
	  -e ADMIN_DATABASE_URL=postgresql+asyncpg://admin:admin_dev@postgres:5432/papelmind \
	  api alembic upgrade head

s1-seed: ## Seed S1
	docker compose run --rm \
	  -e ADMIN_DATABASE_URL=postgresql+asyncpg://admin:admin_dev@postgres:5432/papelmind \
	  api python scripts/seed_s1.py

s1-api: ## API en foreground
	docker compose up api

s1-test: ## T5/T10
	docker compose run --rm \
	  -e TEST_DATABASE_URL=postgresql+asyncpg://admin:admin_dev@postgres:5432/papelmind \
	  -e DATABASE_URL=postgresql+asyncpg://erp_app:erp_app_dev@postgres:5432/papelmind \
	  -e WORKER_DATABASE_URL=postgresql+asyncpg://erp_worker:erp_worker_dev@postgres:5432/papelmind \
	  api python -m pytest tests/ -v

s1-shell: ## Shell en contenedor API
	docker compose run --rm api bash
