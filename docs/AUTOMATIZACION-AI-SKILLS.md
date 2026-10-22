# 🤖 Automatización y AI Skills — Resumen Oficial
## 1. Concepto y Filosofía
**AI Skills:** directivas que enseñan a la IA a ejecutar tareas de ingeniería con rigor senior.
**Documentación proactiva cero-fricción:** transforma el esfuerzo de documentar en un proceso asistido.

## 2. Los Tres Pilares de la Automatización en PapelMaind
### A. Asistente de Registro Diario (`dev-log-assistant`)
- **Ubicación:** Local y privado — `docs/secure-notes/dev-log/YYYY-MM-DD.md` (ignorado por Git).
- **Función:** Registra cronológicamente el trabajo diario.
- **Seguridad:** Enmascara automáticamente credenciales (`[REDACTED]`).

### B. Capa BuJo (`bujo-note`)
- **Ubicación:** Versionado en Git — `docs/bujo/NXX-slug.md` + `INDEX.md`.
- **Función:** Captura decisiones de arquitectura, conceptos y "por qués" que no son diarios ni procedimentales.
- **Seguridad:** Valida enmascaramiento de rutas y credenciales. Regenera el índice con validación "Opción Z".

### C. Generador de Procedimientos (`runbook-generator`)
- **Ubicación:** Versionado en Git — `docs/runbooks/RB-XX.md`.
- **Función:** Convierte notas técnicas en runbooks operativos (metadata, pasos, rollback, troubleshooting).

## 3. Script de Automatización Idempotente (`scripts/bootstrap-docs.sh`)
Garantiza que cualquier nuevo proyecto tenga el sistema al clonar el repo. Usa **heredocs anidados** (`SKILL` dentro de `EOF`) para auto-generar la infraestructura sin romper bash.

## 4. Mapa Actual de Recursos
| Recurso | Ruta | Estado |
|---|---|---|
| N01: Rotación de Token | `docs/bujo/N01-rotacion-token-blindaje.md` | ✅ Completo |
| dev-log-assistant | `docs/ai-skills/reporte-notas-deldia.md` | ✅ |
| bujo-note | `docs/ai-skills/bujo-note.md` | ✅ |
| runbook-generator | `docs/ai-skills/generar-runbook.md` | ✅ |
| bootstrap seguro | `scripts/bootstrap-docs.sh` | ✅ Idempotente |
