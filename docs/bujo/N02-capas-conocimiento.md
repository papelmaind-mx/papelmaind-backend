---
id: N02
title: Arquitectura de 3 Capas de Conocimiento (Dev-Log, BuJo, Runbook)
created: 2026-10-23
updated: 2026-10-23
place: "~/proyectos-python/papelmaind"
tags: [arquitectura, documentacion, automatizacion]
status: done
priority: high
links: [RB-01, RB-02]
---

<!-- 1. Contexto: El conocimiento conceptual se perdía entre el dev-log efímero y los runbooks procedurales. -->
<!-- 2. Alternativas consideradas: Wikis externas (Notion), ADRs pesados, o seguir usando solo dev-logs. -->
<!-- 3. Decisión tomada: Implementar una "Capa BuJo" local, versionada en Git, con indexación automática por IA. -->
<!-- 4. Trade-offs aceptados: Requiere disciplina para usar el skill `bujo-note`, pero elimina la fricción de mantener índices manuales. -->
<!-- 5. Suposiciones: El equipo usará la IA para generar y reindexar, no editará el INDEX.md a mano. -->
<!-- 6. Riesgos: Ediciones manuales en INDEX.md que se sobrescriban. Mitigado por la "Opción Z" (aviso de dos vías). -->
<!-- 7. Métricas de éxito: Cero notas conceptuales perdidas; recuperación de decisiones por ID en < 10 segundos. -->
<!-- 8. Referencias: Método Bullet Journal (Carroll), Architecture Decision Records (ADR). -->
<!-- 9. Siguiente paso: Integrar el bloque de BuJo en `scripts/bootstrap-docs.sh` y actualizar el resumen oficial. -->

# Arquitectura de 3 Capas de Conocimiento

El sistema de documentación de PapelMaind se ha estabilizado en tres capas ortogonales:

1. **RAM (Efímero)**: `docs/secure-notes/dev-log/YYYY-MM-DD.md`. Ignorado por Git. Registro diario de trabajo.
2. **Disco (Estable)**: `docs/bujo/NXX-slug.md`. Versionado en Git. Decisiones de arquitectura, conceptos y "por qués".
3. **BIOS (Procedural)**: `docs/runbooks/RB-XX.md`. Versionado en Git. Procedimientos operativos paso a paso con rollback.

La automatización se logra mediante AI Skills (`dev-log-assistant`, `bujo-note`, `runbook-generator`) que transforman el contexto crudo en artefactos estandarizados, enmascarando siempre los secretos.
