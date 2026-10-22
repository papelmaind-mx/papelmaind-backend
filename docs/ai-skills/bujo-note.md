---
name: bujo-note
description: Crea, actualiza e indexa Notas BuJo (NXX) estables y versionadas.
triggers:
  - 'bujo-note: "<título>"'
  - 'bujo-note: reindex'
---

# BuJo Note Manager

## 🎯 Tu Misión
Gestionar la capa de conocimiento estable del proyecto. Tienes dos modos de operación:
1. **Modo Crear/Actualizar:** `bujo-note: "<título>"` → Genera o actualiza una nota `NXX` con la plantilla de 9 significadores y actualiza el `INDEX.md`.
2. **Modo Reindexar:** `bujo-note: reindex` → Escanea `docs/bujo/*.md`, lee los frontmatters y regenera completamente `docs/bujo/INDEX.md`.

## 🔒 Reglas de Seguridad (OBLIGATORIAS)
1. **NUNCA** incluyas credenciales reales. Usa `$DATABASE_URL`, `[REDACTED]`, etc.
2. Enmascara cualquier ruta local sensible en el campo `place:` (ej. usa `~/proyectos/...` en lugar de rutas absolutas con nombres de usuario reales).

## 📐 Plantilla de 9 Significadores (OBLIGATORIA al crear)
Al crear una nueva nota, inserta este bloque de comentarios HTML justo después del frontmatter:



markdown
<!-- 1. Contexto: ¿qué problema estoy resolviendo? -->
<!-- 2. Alternativas consideradas: ¿qué otras opciones había? -->
<!-- 3. Decisión tomada: ¿qué elegí y por qué? -->
<!-- 4. Trade-offs aceptados: ¿qué sacrifico a cambio? -->
<!-- 5. Suposiciones: ¿qué asumo que es cierto? -->
<!-- 6. Riesgos: ¿qué podría salir mal? -->
<!-- 7. Métricas de éxito: ¿cómo sé que funcionó? -->
<!-- 8. Referencias: ¿en qué me basé? -->
<!-- 9. Siguiente paso: ¿qué desencadena esta nota? -->



## ⚙️ Reglas de Validación y Flujo (Opción Z)
- **Frontmatter obligatorio:** `id` (NXX), `title`, `created`, `updated`, `place`, `tags`, `status` (open|migrated|done|cancelled), `priority` (high|normal|low), `links` ([]).
- **Nombre de archivo:** `NXX-slug-kebab-case.md` (el ID no lleva guion interno).
- **Colisión de IDs:** Si el ID ya existe, propón el siguiente ID libre y avisa.
- **Detección de desincronización (`updated`):** Si al actualizar detectas que el `mtime` del archivo es mayor que la fecha en `updated`, advierte: *"⚠️ El archivo fue modificado manualmente después de la fecha 'updated'. ¿Deseas que actualice la fecha a hoy antes de guardar?"*.
- **Indexación Two-Way:** Al regenerar `INDEX.md`, si detectas contenido manual fuera de la tabla generada, advierte: *"⚠️ Detecté ediciones manuales en INDEX.md. Voy a regenerarlo. ¿Apruebas la sobrescritura?"*.

## 📤 Entrega Final
- **Modo Crear:** Devuelve el bloque de código completo de la nueva nota `NXX` y la fila actualizada para `INDEX.md`. Pregunta: *"¿Deseas que guarde estos archivos en `docs/bujo/`?"*.
- **Modo Reindexar:** Devuelve únicamente el bloque de código completo para `docs/bujo/INDEX.md` y pregunta: *"¿Deseas sobrescribir `docs/bujo/INDEX.md` con esta versión?"*.
