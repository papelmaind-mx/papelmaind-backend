---
name: weekly-review
description: Ritual semanal de Migración BuJo — revisa notas abiertas, propone migrar/cancelar/escalar, y actualiza INDEX + ROADMAP.
triggers:
  - "weekly review"
  - "revisión semanal"
  - "ritual de migración"
  - "migrar notas de la semana"
---

# Weekly Review — Ritual de Migración BuJo

## 🎯 Misión
Ejecutar la **Migración** (el corazón del Bullet Journal de Ryder Carroll):
revisar lo abierto, decidir conscientemente qué sigue vivo, y cerrar el ciclo semanal.

> *"La migración te obliga a replantearte: ¿de verdad vale la pena hacer esto?"* — Ryder Carroll

## 📥 Precondiciones
- `docs/bujo/notes/` existe y tiene notas `NXX-*.md`.
- `docs/bujo/INDEX.md` existe (regenerado por `bujo-note: reindex`).
- Opcional: `docs/ROADMAP.md` existe (Future Log). Si no, el skill lo propone pero no lo crea sin confirmación.

## 🔄 Flujo (5 pasos)

### Paso 1 — Inventario
1. Leer todos los `docs/bujo/notes/NXX-*.md` con `status: open` o `status: migrated`.
2. Leer `docs/secure-notes/dev-log/` de los últimos **7 días** (solo nombres de archivo y bullets con `·` o `?`).
3. Cruzar: ¿hay tareas en dev-logs que no tienen nota `NXX`? → candidatas a migrar a nueva nota.

### Paso 2 — Clasificar cada nota abierta
Para cada nota con `status: open`:
```
[K]eep | [M]igrate | [D]one | [C]ancel | [E]scalate
```

Sugerencias automáticas:
- open + updated > 14 días → sugerir Cancel o Migrate
- high + > 7 días → sugerir Escalate
- migrated + > 21 días → sugerir Cancel
- ? duda > 10 días → sugerir cerrar como done

### Paso 3 — ROADMAP
Si existe: proponer añadir high migradas.
Si no: preguntar si crear plantilla mínima.

### Paso 4 — Regenerar índice
Delegar a `bujo-note: reindex`.

### Paso 5 — Cierre semanal
Escribir bloque de máximo 5 líneas en el dev-log del viernes.

## 🔒 Seguridad
Enmascarar secretos con `[REDACTED]`. El resumen va al dev-log (privado).

## 📤 Entrega
1. Tabla de decisiones (nota → acción → status).
2. Diff del INDEX regenerado.
3. Resumen de 5 líneas.
4. Preguntar si se commitea.
