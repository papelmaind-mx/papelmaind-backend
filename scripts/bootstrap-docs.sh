# ---------------------------------------------------------------
# 8. Capa BuJo: README, INDEX y AI Skill (Idempotente)
# ---------------------------------------------------------------
mkdir -p docs/bujo

if [ ! -f docs/bujo/README.md ]; then
  cat <<'EOF' >docs/bujo/README.md
# 📌 Capa BuJo (Bullet Journal Técnico)
Notas estables, versionadas e indexadas (NXX) para decisiones de arquitectura y conceptos.
> **Regla:** `INDEX.md` se regenera con `bujo-note: reindex`. No editar manualmente.
EOF
  echo "✅ Creado: docs/bujo/README.md"
else
  echo "⏭️  docs/bujo/README.md ya existe"
fi

if [ ! -f docs/bujo/INDEX.md ]; then
  cat <<'EOF' >docs/bujo/INDEX.md
<!-- AUTO-GENERATED: usa 'bujo-note: reindex' para actualizar -->
# 🗂️ Índice de Notas BuJo
| ID | Título | Estado | Prioridad | Updated | Tags |
|----|--------|--------|-----------|---------|------|
EOF
  echo "✅ Creado: docs/bujo/INDEX.md"
else
  echo "⏭️  docs/bujo/INDEX.md ya existe"
fi

if [ ! -f docs/ai-skills/bujo-note.md ]; then
  cat <<'SKILL' >docs/ai-skills/bujo-note.md
---
name: bujo-note
description: Crea, actualiza e indexa Notas BuJo (NXX) estables.
triggers: ['bujo-note: "<título>"', 'bujo-note: reindex']
---
# BuJo Note Manager
## 🎯 Misión
1. Crear/Actualizar: genera NXX con 9 significadores + actualiza INDEX.md.
2. Reindexar: escanea frontmatters y regenera INDEX.md.
## 🔒 Seguridad
- NUNCA incluyas credenciales. Enmascara rutas sensibles en `place:`.
## 📐 Plantilla 9 Significadores (insertar post-frontmatter)
<!-- 1. Contexto --> <!-- 2. Alternativas --> <!-- 3. Decisión -->
<!-- 4. Trade-offs --> <!-- 5. Suposiciones --> <!-- 6. Riesgos -->
<!-- 7. Métricas --> <!-- 8. Referencias --> <!-- 9. Siguiente paso -->
## ⚙️ Validación (Opción Z)
- Frontmatter obligatorio: id (NXX), title, created, updated, place, tags, status, priority, links.
- Archivo: NXX-slug-kebab-case.md.
- Si mtime > updated, avisar y proponer actualización.
- Al reindexar, avisar si hay ediciones manuales en INDEX.md antes de sobrescribir.
SKILL
  echo "✅ Creado: docs/ai-skills/bujo-note.md"
else
  echo "⏭️  docs/ai-skills/bujo-note.md ya existe"
fi

# ---------------------------------------------------------------
# 7. Capa BuJo: Infraestructura y Skill (Idempotente)
# ---------------------------------------------------------------
mkdir -p docs/bujo

if [ ! -f docs/bujo/README.md ]; then
cat <<'BUJO_README' > docs/bujo/README.md
# 📌 Capa BuJo (Bullet Journal Técnico)
Notas estables, versionadas e indexadas (NXX) para decisiones de arquitectura.
> **Regla:** `INDEX.md` se regenera con `bujo-note: reindex`.
BUJO_README
echo "✅ Creado: docs/bujo/README.md"
fi

if [ ! -f docs/bujo/INDEX.md ]; then
cat <<'BUJO_INDEX' > docs/bujo/INDEX.md
<!-- AUTO-GENERATED: usa 'bujo-note: reindex' para actualizar -->
# 🗂️ Índice de Notas BuJo
| ID | Título | Estado | Prioridad | Updated | Tags |
|----|--------|--------|-----------|---------|------|
BUJO_INDEX
echo "✅ Creado: docs/bujo/INDEX.md"
fi

if [ ! -f docs/ai-skills/bujo-note.md ]; then
cat <<'BUJO_SKILL' > docs/ai-skills/bujo-note.md
---
name: bujo-note
description: Crea, actualiza e indexa Notas BuJo (NXX) estables.
triggers: ['bujo-note: "<título>"', 'bujo-note: reindex']
---
# BuJo Note Manager
## 🎯 Misión: 1. Crear NXX con 9 significadores. 2. Reindexar INDEX.md.
## 🔒 Seguridad: NUNCA incluyas credenciales. Enmascara rutas en `place:`.
## 📐 9 Significadores: <!-- 1. Contexto --> <!-- 2. Alternativas --> <!-- 3. Decisión --> <!-- 4. Trade-offs --> <!-- 5. Suposiciones --> <!-- 6. Riesgos --> <!-- 7. Métricas --> <!-- 8. Referencias --> <!-- 9. Siguiente paso -->
## ⚙️ Validación (Opción Z): Frontmatter obligatorio. Avisa si mtime > updated. Avisa antes de sobrescribir INDEX.md manual.
BUJO_SKILL
echo "✅ Creado: docs/ai-skills/bujo-note.md"
fi
