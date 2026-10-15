# P0 Sprint 1 — Auth + Multi-tenant + RLS + UnitOfWork + Seed

## Objetivo
Identidad, tenant isolation, Unit of Work y seed mínimo. Tests T5/T10 verdes.

## Entregables
1. Modelos: usuarios, roles, papelerias, sucursales, relaciones user↔papeleria
2. RLS suite (FORCE ROW LEVEL SECURITY + policies por papeleria_id)
3. `generate_uuid_v7()` en DB
4. UnitOfWork (commit/rollback + set_current_tenant)
5. Endpoints: login, me, switch-tenant (si aplica)
6. Seed: 1 papelería, 1 sucursal, roles, 1 admin, catálogo claves (F24)
7. Tests: T5 (RLS isolation), T10 (login primera relación)

## Fuera de alcance S1
- Outbox worker real (S3) — pero modelo outbox puede existir
- POS / FEFO / CFDI
- Kafka

## RFCs que deben estar cerrados antes de S1
- [x] F17 flags outbox (ya en canon)
- [ ] RFC-024 catalogo_claves_config

## RFCs que NO bloquean S1
- F35, F36, F37, F38 (S3+), Anexo S/T
