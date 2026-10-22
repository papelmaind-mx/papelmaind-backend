---
id: N01
title: Rotación de Token y Blindaje de Credenciales
created: 2026-10-23
updated: 2026-10-23
place: "nvim / ~/proyectos-python/papelmaind"
tags: [seguridad, git, bootstrap]
status: done
priority: high
links: []
---
<!-- 1. Contexto: Se detectó un token clásico de GitHub expuesto en texto plano en un archivo de setup local. -->
<!-- 2. Alternativas consideradas: Borrar del historial de Git (complejo/riesgoso) vs. Rotar y aislar el archivo. -->
<!-- 3. Decisión tomada: Revocar el token viejo, migrar a Fine-Grained PAT, mover el archivo a docs/secure-notes/ y usar git credential.helper. -->
<!-- 4. Trade-offs aceptados: Requiere configuración inicial del helper, pero elimina el riesgo de exposición en URLs de remote. -->
<!-- 5. Suposiciones: El archivo no había sido commiteado previamente a una rama pública remota. -->
<!-- 6. Riesgos: Acceso no autorizado previo a la revocación. Mitigado con la revocación inmediata en GitHub. -->
<!-- 7. Métricas de éxito: `git status` limpio de secretos, `git fetch` exitoso con URL limpia. -->
<!-- 8. Referencias: GitHub Docs sobre Fine-Grained PATs y buenas prácticas de .gitignore. -->
<!-- 9. Siguiente paso: Integrar la Capa BuJo en el script bootstrap-docs.sh para prevenir esto en futuros proyectos. -->

## Resumen de la Acción
Se ejecutó un protocolo de respuesta a incidentes de nivel 1:
1. Revocación del token `ghp_...` en GitHub.
2. Generación de nuevo PAT con permisos mínimos (solo este repo).
3. Enmascaramiento del archivo original y traslado a `docs/secure-notes/`.
4. Limpieza de `git remote set-url` y activación de `credential.helper store`.
