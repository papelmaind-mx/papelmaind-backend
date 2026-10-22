$()$(
  bash
  #!/usr/bin/env bash
  # ============================================================
  # PAPELMAIND — Bootstrap del Sistema de Conocimiento v2.4
  # Uso:  chmod +x scripts/bootstrap-docs.sh && ./scripts/bootstrap-docs.sh
  #       o: make bootstrap
  # Características:
  #   - 100% idempotente (additive-only)
  #   - Zero-Trust (.gitignore + pre-commit con allowlist)
  #   - 3 capas + 4 AI Skills
  #   - Makefile con tabs correctos + check delega al hook
  #   - N00 seed + INDEX 3 bloques
  #   - Parches P0: regex ERE válidas, allowlist explícita
  # ============================================================
  set -euo pipefail

  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  cd "$ROOT"
  TODAY="$(date +%Y-%m-%d)"

  echo "🚀 Bootstrap del sistema de conocimiento v2.4 (3 capas + AI Skills)"
  echo "   Directorio: $ROOT"
  echo "   Fecha:      $TODAY"
  echo ""

  # ────────────────────────────────────────────────────────────
  # Helper: append idempotente con marcador
  # ────────────────────────────────────────────────────────────
  append_block() {
    local file="$1" marker="$2" content="$3"
    local start="<!-- ${marker}:start -->"
    local end="<!-- ${marker}:end -->"

    touch "$file"

    if grep -qF "$start" "$file"; then
      # Bloque ya presente → reemplazar solo el contenido entre marcadores
      awk -v s="$start" -v e="$end" -v new="$content" '
      $0 == s { print s; print new; skip=1; next }
      $0 == e { skip=0; print e; next }
      !skip { print }
    ' "$file" >"${file}.tmp" && mv "${file}.tmp" "$file"
      echo "♻️  Actualizado bloque '$marker' en: $file"
    else
      printf "\n%s\n%s\n%s\n" "$start" "$content" "$end" >>"$file"
      echo "✅ Añadido bloque '$marker' a: $file"
    fi
  }

  # ────────────────────────────────────────────────────────────
  # 1. Estructura de directorios
  # ────────────────────────────────────────────────────────────
  mkdir -p \
    docs/ai-skills \
    docs/bujo/notes \
    docs/bujo/collections \
    docs/runbooks \
    docs/secure-notes/dev-log \
    scripts \
    .githooks

  echo "✅ Estructura de directorios lista"

  # ────────────────────────────────────────────────────────────
  # 2. .gitignore (Zero-Trust) — append idempotente
  # ────────────────────────────────────────────────────────────
  GITIGNORE_BLOCK='# ============================================================
# PAPELMAIND — Protección de datos sensibles (bootstrap-docs v2.4)
# ============================================================
# Entornos y secretos
.env
.env.*
!.env.example
*.pem
*.key
*.enc
*.p12
*.pfx
secrets/
credentials/
*.secret

# Archivos de setup que suelen contener tokens/URLs
papelmaind-setup*
*credential*.md
*secret*.md

# Notas seguras / locales (nunca versionar)
docs/secure-notes/
!docs/secure-notes/README.md

# Logs diarios y temporales
*.log
dev-log/
tmp/
temp/
.cache/

# Sistema operativo
.DS_Store
Thumbs.db
desktop.ini

# IDEs y editores
.idea/
.vscode/
*.swp
*.swo
*~
.project
.classpath
.settings/

# Node / JS
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
dist/
build/
.next/
.nuxt/
.out/

# Python
__pycache__/
*.py[cod]
*$py.class
.Python
venv/
.venv/
env/
*.egg-info/
.pytest_cache/
.coverage
htmlcov/
.mypy_cache/
.ruff_cache/

# Otros
*.bak
*.tmp
*.orig
.sass-cache/
.parcel-cache/
.turbo/

# GitHub / CI
.github/workflows/*.secret.yml'

  if [ ! -f .gitignore ]; then
    printf "%s\n" "$GITIGNORE_BLOCK" >.gitignore
    echo "✅ Creado: .gitignore (zero-trust)"
  elif ! grep -qF "# PAPELMAIND — Protección de datos sensibles" .gitignore; then
    printf "\n%s\n" "$GITIGNORE_BLOCK" >>.gitignore
    echo "✅ Append: .gitignore (bloque zero-trust añadido)"
  else
    echo "⏭️  .gitignore ya contiene el bloque zero-trust"
  fi

  # ────────────────────────────────────────────────────────────
  # 3. .env.example
  # ────────────────────────────────────────────────────────────
  if [ ! -f .env.example ]; then
    cat >.env.example <<'EOF'
# ============================================================
# Ejemplo de variables de entorno (NO commitear el .env real)
# ============================================================
# Base de datos
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Redis (idempotencia, cache)
REDIS_URL=redis://localhost:6379

# Tokens y claves (reemplazar con valores reales)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
JWT_SECRET=your-super-secret-jwt-key-change-me

# Otros
NODE_ENV=development
PORT=3000
EOF
    echo "✅ Creado: .env.example"
  else
    echo "⏭️  .env.example ya existe"
  fi

  # ────────────────────────────────────────────────────────────
  # 4. Secure Notes README
  # ────────────────────────────────────────────────────────────
  if [ ! -f docs/secure-notes/README.md ]; then
    cat >docs/secure-notes/README.md <<'EOF'
# 🔒 Secure Notes (Local / No versionado)

Esta carpeta está **completamente ignorada por Git** (excepto este README).

Contiene:
- Bitácoras diarias (`dev-log/YYYY-MM-DD.md`)
- Mapeo de credenciales locales
- Cualquier nota sensible que **nunca** debe subir al repositorio

> Usa el skill `dev-log-assistant` (trigger: `resume mi día`) para generar los logs.
> Regla de seguridad: enmascara secretos con `[REDACTED]` antes de escribir.
EOF
    echo "✅ Creado: docs/secure-notes/README.md"
  else
    echo "⏭️  docs/secure-notes/README.md ya existe"
  fi

  # ────────────────────────────────────────────────────────────
  # 5. Capa BuJo: README + INDEX (3 bloques) + N00 seed
  # ────────────────────────────────────────────────────────────
  if [ ! -f docs/bujo/README.md ]; then
    cat >docs/bujo/README.md <<'EOF'
# 📓 Capa BuJo (Bullet Journal Técnico)

Notas conceptuales `N00-slug.md` versionadas en Git: decisiones, dudas e ideas que **no** son diarias (`dev-log/`) ni procedurales (`runbooks/`).

## Formato de ID
`N00`, `N01`, …, `N99`, luego `N100`, `N101`… — **sin guion interno**, guion solo entre ID y slug.

## Significadores BuJo (cuerpo de la nota)
```
· tarea      - nota       o evento     * prioridad
! idea       ? duda       @ espera     > migrada     x cancelada
```

## Estados (`status`)
`open` · `migrated` · `done` · `cancelled`

## Prioridades (`priority`)
`high` · `normal` · `low`

## Índice
`INDEX.md` se regenera con el skill `bujo-note: reindex`. **No editar a mano** (two-way: el skill avisa si detecta cambios manuales).

## Crear una nota
```
bujo-note: "Título de la decisión o concepto"
```

## Seguridad
Nunca credenciales. Enmascara con `[REDACTED]` o `$VARIABLE`.
EOF
    echo "✅ Creado: docs/bujo/README.md"
  else
    echo "⏭️  docs/bujo/README.md ya existe"
  fi

  if [ ! -f docs/bujo/INDEX.md ]; then
    cat >docs/bujo/INDEX.md <<'EOF'
# 🗂️ INDEX — Capa BuJo

<!-- ⚠️ AUTO-GENERADO por el skill `bujo-note` (modo reindex). NO EDITAR A MANO. -->
<!-- Si necesitas corregir algo, edita el frontmatter de la nota NXX en docs/bujo/notes/ y ejecuta: bujo-note: reindex -->

## 🔴 Alta prioridad

| ID | Título | Estado | Tags | Creada | Actualizada |
|----|--------|--------|------|--------|-------------|
| N00 | Inicio del sistema de conocimiento | open | meta,sistema | 2026-10-22 | 2026-10-22 |

## 🟡 Prioridad media

| ID | Título | Estado | Tags | Creada | Actualizada |
|----|--------|--------|------|--------|-------------|

## 🟢 Prioridad baja

| ID | Título | Estado | Tags | Creada | Actualizada |
|----|--------|--------|------|--------|-------------|

## ❌ Retiradas (IDs no reutilizables)

| ID | Título | Motivo | Fecha retiro |
|----|--------|--------|--------------|
EOF
    echo "✅ Creado: docs/bujo/INDEX.md"
  else
    echo "⏭️  docs/bujo/INDEX.md ya existe"
  fi

  if [ ! -f docs/bujo/notes/N00-inicio-del-sistema.md ]; then
    cat >docs/bujo/notes/N00-inicio-del-sistema.md <<'EOF'
---
id: N00
title: "Inicio del sistema de conocimiento"
created: 2026-10-22
updated: 2026-10-22
place: "scripts/bootstrap-docs.sh"
tags: [meta, sistema]
status: open
priority: high
links: []
---

<!-- Significadores BuJo: · tarea | - nota | o evento | * prioridad | ! idea | ? duda | @ espera | > migrada | x cancelada -->

# Inicio del sistema de conocimiento

- Esta nota documenta el propio sistema (dogfooding).
- Capas: **RAM** (dev-log) → **Disco** (NXX) → **BIOS** (RB-XX).
- Skills: `dev-log-assistant`, `bujo-note`, `runbook-generator`, `weekly-review`.
- El índice (`INDEX.md`) se regenera con `bujo-note: reindex`.

· Tarea: crear primera nota propia con `bujo-note: "<título>"`
? Duda: ¿migrar `ROADMAP.md` (Future Log) en la próxima iteración?
! Idea: usar `make check` antes de cada commit (además del hook)
EOF
    echo "✅ Creado: docs/bujo/notes/N00-inicio-del-sistema.md"
  else
    echo "⏭️  N00 ya existe"
  fi

  # ────────────────────────────────────────────────────────────
  # 6. AI Skills (4 contratos completos)
  # ────────────────────────────────────────────────────────────

  # --- Skill 1: dev-log-assistant ---
  if [ ! -f docs/ai-skills/reporte-notas-deldia.md ]; then
    cat >docs/ai-skills/reporte-notas-deldia.md <<'SKILL'
---
name: dev-log-assistant
description: Genera bitácora diaria local y segura (Capa RAM).
triggers:
  - "resume mi día"
  - "haz el log de hoy"
  - "dev-log de [fecha]"
  - "bitácora diaria"
---

# Skill: dev-log-assistant

## 🎯 Misión
Convertir lo trabajado en el día en una bitácora local y segura.

## 📤 Output
`docs/secure-notes/dev-log/YYYY-MM-DD.md` (ignorado por Git).

## 🔒 Seguridad (OBLIGATORIA)
1. Enmascarar TODO secreto: `[REDACTED]`, `[SECRET_KEY]`, `[ENV_VARIABLE]`.
2. Nunca escribir tokens, contraseñas, claves API, cadenas de conexión reales.
3. Si el usuario pegó un secreto por error, enmascararlo antes de escribir.

## 📐 Estructura
```markdown
# Dev Log — YYYY-MM-DD

## Resumen del día
- ...

## Tareas realizadas
- [x] ...
- [ ] ...

## Decisiones técnicas
- ...

## Problemas / Blockers
- ...

## Próximos pasos
- ...

## Notas libres
...
```

## 📤 Entrega
1. Escribir el archivo en `docs/secure-notes/dev-log/`.
2. Recordar al usuario: "Este log es local y seguro. No se versiona."
3. Sugerir: "Si hay una decisión conceptual, usa `bujo-note: \"<título>\"` para migrarla a la Capa BuJo."
SKILL
    echo "✅ Creado: docs/ai-skills/reporte-notas-deldia.md"
  else
    echo "⏭️  reporte-notas-deldia.md ya existe"
  fi

  # --- Skill 2: bujo-note ---
  if [ ! -f docs/ai-skills/bujo-note.md ]; then
    cat >docs/ai-skills/bujo-note.md <<'SKILL'
---
name: bujo-note
description: Crea notas BuJo NXX-slug.md (significadores) y regenera docs/bujo/INDEX.md (two-way).
triggers:
  - "bujo-note: \"<título>\""
  - "bujo-note: reindex"
  - "nueva nota bujo"
  - "captura esto como nota"
---

# BuJo Note Manager

## 🎯 Dos modos

### Modo 1 — Crear nota: `bujo-note: "<título>" [tags opcionales]`
1. **Escanear** `docs/bujo/notes/` y `docs/bujo/INDEX.md` → calcular siguiente ID libre (`N00`…`N99`, luego `N100`…). **IDs retirados no se reutilizan.**
2. **Slug** kebab-case ASCII desde el título.
3. **Crear** `docs/bujo/notes/NXX-<slug>.md` con frontmatter:
   ```yaml
   ---
   id: NXX
   title: "<título original>"
   created: <YYYY-MM-DD>
   updated: <YYYY-MM-DD>
   place: "<cwd o editor detectado>"
   tags: [tag1, tag2]
   status: open        # open | migrated | done | cancelled
   priority: normal    # high | normal | low
   links: []
   ---
   ```
4. **Insertar** plantilla de significadores BuJo al inicio del cuerpo:
   ```markdown
   <!-- Significadores BuJo: · tarea | - nota | o evento | * prioridad | ! idea | ? duda | @ espera | > migrada | x cancelada -->
   # <Título>
   ·
   ```
5. **Idempotencia de carpetas**: crear `docs/bujo/notes/` y `docs/bujo/collections/` si faltan.
6. **Colisión de IDs**: renombrar la nueva al siguiente ID libre + avisar.
7. **Regenerar índice** (delegar a Modo 2).
8. **Devolver**: ruta, ID asignado, sugerir `nvim <ruta>`.

### Modo 2 — Reindexar: `bujo-note: reindex`
1. **Leer** todos los `docs/bujo/notes/NXX-*.md` y parsear frontmatter.
2. **Validar** (avisar y continuar):
   - IDs duplicados → renombrar el más reciente, avisar.
   - `status` fuera de `open|migrated|done|cancelled` → tratar como `open`, avisar.
   - `priority` fuera de `high|normal|low` → tratar como `normal`, avisar.
   - Campos faltantes (`id,title,created`) → avisar, omitir del índice.
3. **mtime > updated**: detectar y **proponer** actualizar `updated: <hoy>`, preguntar por nota `[A]probar / [R]echazar`.
4. **Two-way (Opción Z)**: comparar filas actuales del `INDEX.md` contra las que el skill generaría. Si hay ediciones manuales, mostrar diff y preguntar `[A]probar y sobrescribir / [R]echazar y abortar / [M]antener manual y regenerar el resto`.
5. **Ordenar** cada bloque por `updated` **descendente**.
6. **Reescribir** `INDEX.md` completo: 3 bloques 🔴/🟡/🟢 + sección Retiradas.
7. **Reportar**: `N indexadas, M avisos, K colisiones resueltas`.

## 🔒 Seguridad
- Nunca credenciales. Enmascarar con `[REDACTED]` o `$VARIABLE`.
- Si la nota nace de un dev-log, no copiar entero: resumir a bullets BuJo.

## 📤 Entrega final
1. Mostrar diff resumido de `INDEX.md` (si cambió).
2. Mostrar rutas creadas/renombradas.
3. Preguntar: *"¿Abro la nota en nvim o quieres ajustar algo?"*
SKILL
    echo "✅ Creado: docs/ai-skills/bujo-note.md"
  else
    echo "⏭️  bujo-note.md ya existe"
  fi

  # --- Skill 3: runbook-generator ---
  if [ ! -f docs/ai-skills/generar-runbook.md ]; then
    cat >docs/ai-skills/generar-runbook.md <<'SKILL'
---
name: runbook-generator
description: Genera procedimientos operativos (RB-XX) con rollback y troubleshooting.
triggers:
  - "genera un runbook de esto"
  - "documenta este procedimiento"
  - "convierte esto en un runbook"
  - "RB de [tema]"
---

# Runbook Generator

## 🎯 Misión
Transformar contexto técnico (notas, comandos, errores) en un runbook operativo profesional.

## 🔒 Seguridad (OBLIGATORIA)
1. NUNCA incluir credenciales reales. Usar `$VARIABLE` o `[REDACTED]`.
2. Enmascarar secretos pegados por error.
3. Variables de entorno en lugar de valores hardcodeados.

## 📐 Estructura obligatoria
1. **Título:** `RB-XX: [Acción]`
2. **TL;DR:** 1 línea
3. **Metadata:** Owner, Última revisión (YYYY-MM-DD), Tiempo estimado, Riesgo (🟢/🟡/🔴), Downtime (Sí/No)
4. **🎯 Objetivo**
5. **⚠️ Prerrequisitos** (checks `- [ ]`)
6. **🚀 Ejecución** (pasos numerados con código copiable + "Resultado esperado")
7. **✅ Verificación**
8. **🔙 Rollback**
9. **🚨 Troubleshooting** (`Error | Causa | Solución`)
10. **📚 Referencias** (RFCs, docs, otras NXX o RB-XX)

## 🎨 Estilo
- Técnico, directo, sin relleno.
- Comandos copiables con variables, no hardcodeados.
- Si falta info: `[TBD]` + avisar al final.

## 📤 Entrega
1. Runbook completo en bloque Markdown.
2. Ruta sugerida: `docs/runbooks/RB-XX-[slug].md`.
3. Preguntar: *"¿Guardo en esa ruta o ajustamos?"*
SKILL
    echo "✅ Creado: docs/ai-skills/generar-runbook.md"
  else
    echo "⏭️  generar-runbook.md ya existe"
  fi

  # --- Skill 4: weekly-review ---
  if [ ! -f docs/ai-skills/weekly-review.md ]; then
    cat >docs/ai-skills/weekly-review.md <<'SKILL'
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
SKILL
    echo "✅ Creado: docs/ai-skills/weekly-review.md"
  else
    echo "⏭️  weekly-review.md ya existe"
  fi

  # ────────────────────────────────────────────────────────────
  # 7. Documentación de arquitectura
  # ────────────────────────────────────────────────────────────
  if [ ! -f docs/ARCHITECTURE.md ]; then
    cat >docs/ARCHITECTURE.md <<'EOF'
# Arquitectura del Sistema de Conocimiento

## Visión general
Sistema de **3 capas + motor de automatización + seguridad zero-trust**:

| Capa | Nombre | Persistencia | Propósito | Skill |
|------|--------|--------------|-----------|-------|
| 1 | **RAM** (Efímero) | Local, no versionado | Bitácora diaria | `dev-log-assistant` |
| 2 | **DISCO** (Estable) | Git | Notas conceptuales BuJo (`NXX`) | `bujo-note` |
| 3 | **BIOS** (Procedural) | Git | Runbooks operativos (`RB-XX`) | `runbook-generator` |

## Flujo de maduración
```
Trabajo diario
    ↓
dev-log (RAM)          ← dev-log-assistant
    ↓ (si es conceptual)
BuJo Note (DISCO)      ← bujo-note
    ↓ (si es procedimiento)
Runbook (BIOS)         ← runbook-generator
    ↓ (viernes)
Weekly Review          ← weekly-review
```

## Principios
1. **Zero-trust**: nada sensible en Git.
2. **Idempotencia**: `make bootstrap` se puede ejecutar N veces.
3. **Maduración progresiva**: efímero → conceptual → procedural.
4. **IA-first**: los skills automatizan creación y mantenimiento.
5. **Two-way index**: el índice avisa si hay ediciones manuales.

## Protecciones
- Hook `pre-commit` bloquea `.env`, credenciales y `docs/secure-notes/`.
- Allowlist explícita: `.env.example`, `docs/runbooks/`, README de secure-notes.
- `.gitignore` cubre secretos y artefactos.
- `make check` llama al mismo hook (una sola fuente de verdad).
EOF
    echo "✅ Creado: docs/ARCHITECTURE.md"
  else
    echo "⏭️  docs/ARCHITECTURE.md ya existe"
  fi

  if [ ! -f docs/AUTOMATIZACION-AI-SKILLS.md ]; then
    cat >docs/AUTOMATIZACION-AI-SKILLS.md <<'EOF'
# Automatización con AI Skills

## Los 4 pilares

| Skill | Trigger principal | Capa | Output |
|-------|-------------------|------|--------|
| `dev-log-assistant` | `resume mi día` | RAM | `docs/secure-notes/dev-log/YYYY-MM-DD.md` |
| `bujo-note` | `bujo-note: "<título>"` | DISCO | `docs/bujo/notes/NXX-slug.md` + INDEX |
| `runbook-generator` | `genera un runbook de esto` | BIOS | `docs/runbooks/RB-XX-slug.md` |
| `weekly-review` | `weekly review` | Ritual | Actualiza INDEX + ROADMAP + dev-log |

## Flujo diario recomendado
1. Trabaja normalmente.
2. `resume mi día` → log local seguro.
3. Si es conceptual → `bujo-note: "..."`.
4. Si es procedimiento → `genera un runbook de esto`.
5. `make check` → verifica que no haya sensibles en stage.
6. Commit limpio (hook pre-commit valida automáticamente).

## Ritual semanal
`weekly review` → clasifica notas abiertas (Keep/Migrate/Done/Cancel/Escalate), regenera INDEX, actualiza ROADMAP y escribe resumen en el dev-log.

## Seguridad
Todos los skills enmascaran secretos (`[REDACTED]`, `[SECRET_KEY]`, etc.).
El hook `pre-commit` bloquea el commit si detecta archivos sensibles en stage.

## Comandos rápidos
```bash
make help        # ver targets
make bootstrap   # (re)instalar todo idempotente
make check       # verificar stage antes de commit
make hooks       # (re)instalar el hook pre-commit
```
EOF
    echo "✅ Creado: docs/AUTOMATIZACION-AI-SKILLS.md"
  else
    echo "⏭️  docs/AUTOMATIZACION-AI-SKILLS.md ya existe"
  fi

  # ────────────────────────────────────────────────────────────
  # 8. .githooks/pre-commit (CORREGIDO v2.4 — regex ERE válidas + allowlist)
  # ────────────────────────────────────────────────────────────
  if [ ! -f .githooks/pre-commit ]; then
    cat >.githooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
# ============================================================
# PAPELMAIND — pre-commit hook (Zero-Trust) — v2.4
# Bloquea el commit si hay archivos sensibles en stage.
# ============================================================
set -euo pipefail

# Patrones de archivos sensibles (regex ERE válidas)
PATTERN='(^|/)\.env($|\.)|(^|/)credentials|(^|/)docs/secure-notes/|\.(enc|key|pem|p12|pfx|kdbx)$|^(secrets?|tokens?|credentials)\.(json|ya?ml|txt)$|papelmaind-setup'

# Excepciones deliberadas y explícitas (allowlist)
ALLOW='(^|/)\.env\.example$|^docs/secure-notes/README\.md$|^docs/runbooks/'

STAGED="$(git diff --cached --name-only --diff-filter=ACM)"
[ -n "$STAGED" ] || exit 0

OFFENDERS="$(printf '%s\n' "$STAGED" \
  | grep -Ei "$PATTERN" \
  | grep -Ev "$ALLOW" \
  || true)"

if [ -n "$OFFENDERS" ]; then
  printf '\n🔴 ALTO: archivos sensibles en stage:\n'
  printf '%s\n' "$OFFENDERS" | sed 's/^/  → /'
  printf '\nSolución: git restore --staged <archivo>\n'
  printf 'Commit abortado.\n'
  exit 1
fi

exit 0
HOOK
    chmod +x .githooks/pre-commit
    echo "✅ Creado: .githooks/pre-commit (v2.4 con allowlist)"
  else
    echo "⏭️  .githooks/pre-commit ya existe (no se sobrescribe)"
  fi

  # Configurar core.hooksPath (solo si estamos en un repo git)
  if git rev-parse --git-dir >/dev/null 2>&1; then
    CURRENT_HOOKS_PATH="$(git config --get core.hooksPath || true)"
    if [ "$CURRENT_HOOKS_PATH" != ".githooks" ]; then
      git config core.hooksPath .githooks
      echo "✅ Configurado: git core.hooksPath = .githooks"
    else
      echo "⏭️  core.hooksPath ya = .githooks"
    fi
  else
    echo "ℹ️  No es un repositorio git todavía (core.hooksPath se configurará al hacer git init)"
  fi

  # ────────────────────────────────────────────────────────────
  # 9. Makefile (CORREGIDO v2.4 — tabs correctos + check delega al hook)
  # ────────────────────────────────────────────────────────────
  if [ ! -f Makefile ]; then
    cat >Makefile <<'MAKE'
.PHONY: help bootstrap check hooks

.DEFAULT_GOAL := help

help:           ## Muestra esta ayuda
	@echo "Targets disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2}'

bootstrap:      ## Ejecuta bootstrap-docs.sh (idempotente)
	@chmod +x scripts/bootstrap-docs.sh
	@./scripts/bootstrap-docs.sh

check:          ## Verifica que no haya archivos sensibles en stage
	@bash .githooks/pre-commit && echo "✅ Limpio: no hay archivos sensibles en stage"

hooks:          ## (Re)instala el hook pre-commit y configura core.hooksPath
	@chmod +x .githooks/pre-commit
	@git config core.hooksPath .githooks
	@echo "✅ Hook instalado: .githooks/pre-commit"
MAKE
    echo "✅ Creado: Makefile (v2.4 con tabs correctos)"
  else
    echo "⏭️  Makefile ya existe (no se sobrescribe)"
  fi

  # ────────────────────────────────────────────────────────────
  # 10. README — bloque idempotente
  # ────────────────────────────────────────────────────────────
  README_BLOCK='## 🧠 Sistema de conocimiento interno

Capas: **RAM** (dev-log local) → **Disco** (notas BuJo `NXX`) → **BIOS** (runbooks `RB-XX`).

- Arquitectura: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Automatización y skills: [`docs/AUTOMATIZACION-AI-SKILLS.md`](docs/AUTOMATIZACION-AI-SKILLS.md)
- Índice de notas: [`docs/bujo/INDEX.md`](docs/bujo/INDEX.md)
- Comandos rápidos: `make help`'

  if [ ! -f README.md ]; then
    cat >README.md <<EOF
# $(basename "$ROOT")

$README_BLOCK
EOF
    echo "✅ Creado: README.md (con bloque de sistema de conocimiento)"
  else
    append_block README.md "bootstrap-docs" "$README_BLOCK"
  fi

  # ────────────────────────────────────────────────────────────
  # 11. Verificación final (CORREGIDO v2.4 — patrones válidos)
  # ────────────────────────────────────────────────────────────
  echo ""
  echo "════════════════════════════════════════════════════════"
  echo "✅ Bootstrap v2.4 completado"
  echo "════════════════════════════════════════════════════════"
  echo ""
  echo "Estructura:"
  echo "  docs/ai-skills/            (4 skills)"
  echo "  docs/bujo/                 (INDEX 3 bloques + N00 seed)"
  echo "  docs/runbooks/"
  echo "  docs/secure-notes/dev-log/ (ignorado por Git)"
  echo "  .githooks/pre-commit       (v2.4 con allowlist)"
  echo "  Makefile                   (check → hook, single source of truth)"
  echo ""
  echo "Próximos pasos:"
  echo "  1. cp .env.example .env    (rellena valores reales)"
  echo "  2. make check              (verifica stage limpio)"
  echo "  3. Empieza a usar los skills:"
  echo "       • resume mi día"
  echo "       • bujo-note: \"mi primera nota\""
  echo "       • genera un runbook de esto"
  echo "       • weekly review"
  echo ""
  echo "Verificación de seguridad:"
  if git rev-parse --git-dir >/dev/null 2>&1; then
    git status --porcelain 2>/dev/null | grep -E '\.env$|credentials|docs/secure-notes/|\.enc$|\.key$|papelmaind-setup' &&
      echo "🔴 ALTO: archivos sensibles detectados" ||
      echo "✅ Limpio"
  else
    echo "ℹ️  No es un repositorio git todavía"
  fi
  echo ""
)$()
