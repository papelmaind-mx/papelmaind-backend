# PapelMaind — Makefile (canon Sección 11: dev, build, test, migrate, seed, lint, format, backup, deploy, canon-lint)
SHELL := /bin/bash
BACKEND := backend
PYTHON  ?= python3.12
PIP     := $(PYTHON) -m pip

.PHONY: help dev build test migrate seed lint format backup deploy canon-lint clean install

help:
	@echo "PapelMaind — objetivos disponibles:"
	@echo "  make install     — instala dependencias del backend"
	@echo "  make dev         — levanta API con uvicorn (hot reload)"
	@echo "  make build       — construye imágenes Docker (requiere Docker)"
	@echo "  make test        — suite pytest (SQLite, RLS emulado)"
	@echo "  make migrate     — aplica migraciones SQL (PostgreSQL)"
	@echo "  make seed        — seed inicial (tenants + usuarios + catálogo base)"
	@echo "  make lint        — ruff + mypy"
	@echo "  make format      — ruff format"
	@echo "  make backup      — pg_dump gz (PostgreSQL)"
	@echo "  make deploy      — deploy docker-compose prod (requiere Docker)"
	@echo "  make canon-lint  — F28: lint del canon XML (GATE obligatorio pre-merge)"
	@echo "  make smoke       — smoke test E2E contra la API corriendo"

install:
	cd $(BACKEND) && $(PIP) install -r requirements.txt

dev:
	cd $(BACKEND) && $(PYTHON) -m uvicorn src.main:app --reload --port 8000

build:
	docker compose build

test:
	cd $(BACKEND) && $(PYTHON) -m pytest

migrate:
	cd $(BACKEND) && $(PYTHON) -m src.infrastructure.db.migrate apply

seed:
	cd $(BACKEND) && $(PYTHON) -m src.infrastructure.db.seed

lint:
	$(PYTHON) -m ruff check $(BACKEND)
	$(PYTHON) -m mypy $(BACKEND)/src --ignore-missing-imports || true

format:
	$(PYTHON) -m ruff format $(BACKEND)

backup:
	bash scripts/backup.sh

deploy:
	docker compose -f docker-compose.prod.yml up -d

canon-lint:
	$(PYTHON) scripts/canon_lint.py docs/canon/papelmaind_context_engineer_v2.2.3.xml

smoke:
	bash backend/tests/smoke/smoke_test.sh

clean:
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null; rm -f *.db coverage 2>/dev/null; true
