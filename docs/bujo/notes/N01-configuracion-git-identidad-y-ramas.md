---
id: N01
title: "Configuración Git: identidad, remoto y ramas de entorno"
created: 2026-10-22
updated: 2026-10-22
place: "repo local / GitHub org papelmaind-mx"
tags: [git, identidad, remoto, ramas, setup]
status: open
priority: high
links: [N00]
---

<!-- Significadores BuJo: · tarea | - nota | o evento | * prioridad | ! idea | ? duda | @ espera | > migrada | x cancelada -->

# Configuración Git: identidad, remoto y ramas de entorno

## 1. Contexto
Se documenta la configuración base del repositorio `papelmaind-backend` (org `papelmaind-mx`): identidad del autor, vínculo remoto y ramas de entorno.

## 2. Problema / Oportunidad
- Identidad de commits incorrecta o incompleta en el primer commit.
- Remoto configurado con PAT embebido en la URL (riesgo de fuga).
- Necesidad de ramas claras: desarrollo, pruebas y producción.

## 3. Decisión tomada
1. Identidad local unificada:
   - `user.name = PapelMaind-Dev`
   - `user.email = papelmaind@gmail.com`
2. Corrección de autoría del commit inicial con `--amend`.
3. Remoto vía HTTPS (sin token en la URL a largo plazo; usar credential helper / Fine-Grained PAT).
4. Ramas de entorno con upstream:
   - `desarr` → desarrollo activo
   - `prueb` → staging / integración
   - `prod` → producción estable
   - `main` → línea principal

## 4. Razones / Trade-offs
- **Identidad corporativa**: commits trazables a `PapelMaind-Dev`.
- **PAT en URL**: cómodo al inicio, pero inseguro (histórico de shell, logs). Preferible `credential.helper store` + URL limpia.
- **Ramas separadas**: aísla riesgo; `prod` queda blindada.

## 5. Consecuencias
- Commits futuros con autor correcto.
- Flujo: `desarr` → `prueb` → `prod`.
- El PAT antiguo debe permanecer revocado; no reintroducirlo en la URL.

## 6. Métricas de éxito
- [x] `git config user.name` / `user.email` correctos
- [x] Ramas `desarr`, `prueb`, `prod`, `main` con upstream
- [ ] URL remota **sin** token embebido (`git remote -v`)
- [ ] PAT antiguo revocado en GitHub

## 7. Relaciones
- N00 — Inicio del sistema de conocimiento
- Seguridad zero-trust (`.gitignore` + hook pre-commit)

## 8. Estado actual
Identidad y ramas configuradas. Pendiente: asegurar URL limpia del remoto y no volver a pegar tokens en la URL.

## 9. Siguiente paso
· Verificar: `git remote -v` (no debe mostrar token)
· Si aún tiene token: `git remote set-url origin https://github.com/papelmaind-mx/papelmaind-backend.git`
· Confirmar que el Fine-Grained PAT tiene solo permisos mínimos
