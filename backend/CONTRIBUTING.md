# Contribuir a PapelMaind

## Flujo de trabajo (canon Sección 12)

1. Rama por sprint: `git checkout -b feat/s3-pos` desde `develop`.
2. Gate obligatorio ANTES de cualquier merge:
   ```bash
   make canon-lint   # F28: DEBE estar en 0 issues
   make lint         # ruff
   make test         # pytest (CHK-11)
   ```
3. PR → CI (GitHub Actions) verde → merge a `develop`.
4. `develop` → `main` solo con checklist de sprint en verde (CHK-01..CHK-39).

## Reglas del canon que NO se negocian

- **CONV-01**: narrativa es-MX; código/endpoints/eventos en inglés; tablas en español.
- **CONV-03**: DINERO NUMERIC(12,2) · CANTIDAD NUMERIC(12,3) · TIMESTAMPTZ · UUID v7.
- **CONV-05**: `HTTPException` SOLO en capa `api/` — el resto lanza errores de dominio.
- **CONV-07**: `TenantUnitOfWork` para tráfico autenticado; BYPASSRLS solo workers.
- **F17**: outbox con flags SEPARADOS (`publicado_kafka`, `procesado_loyalty`).
- **F26**: `estaciones.tipo` en MAYÚSCULAS (excepción documentada).
- Todo cambio al canon pasa por RFC-lite + `canon_lint.py` en cero.

## Estructura de commits

```
feat: <modulo> — <que hace> (Sprint N)
fix: <modulo> — <que arregla> (F##)
docs: canon|readme|changelog — <cambio>
test: T# — <escenario>
```
