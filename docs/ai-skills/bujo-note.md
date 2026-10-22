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
