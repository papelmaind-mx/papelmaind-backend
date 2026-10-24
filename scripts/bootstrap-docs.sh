$()$(
  bash
  #!/usr/bin/env bash
  # ============================================================
  # PAPELMAIND — Bootstrap del Sistema de Conocimiento v2.5
  # Uso:  chmod +x scripts/bootstrap-docs.sh && ./scripts/bootstrap-docs.sh
  #       o: make bootstrap
  # Características:
  #   - 100% idempotente (additive-only)
  #   - Zero-Trust (.gitignore + pre-commit con allowlist)
  #   - 3 capas + 4 AI Skills
  #   - Makefile con tabs correctos + check delega al hook
  #   - N00 seed + INDEX 3 bloques
  #   - Parches P0: regex ERE válidas, allowlist explícita
  #   - NUEVO v2.5: bujo-open.sh + wrapper bujo + target edit
  # ============================================================
  set -euo pipefail

  ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
  cd "$ROOT"
  TODAY="$(date +%Y-%m-%d)"

  echo "🚀 Bootstrap del sistema de conocimiento v2.5 (3 capas + AI Skills)"
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
# PAPELMAIND — Protección de datos sensibles (bootstrap-docs v2.5)
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
*setup*.md
*token*.md

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
```bash
./scripts/bujo new "Título de la decisión o concepto" [PRIORITY=high] [TAGS=a,b]
```

## Abrir una nota
```bash
make edit                          # la última
make edit ID=N05                   # por ID
make edit PICK=1                   # menú interactivo (fzf)
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

<!-- ⚠️ AUTO-GENERADO por scripts/bujo-reindex.sh. NO EDITAR A MANO. -->

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
- El índice (`INDEX.md`) se regenera con `./scripts/bujo index`.

· Tarea: crear primera nota propia con `./scripts/bujo new "..."`.
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
3. Sugerir: "Si hay una decisión conceptual, usa `./scripts/bujo new \"<título>\"` para migrarla a la Capa BuJo."
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
1. **Escanear** `docs/bujo/notes/` y `docs/bujo/INDEX.md` → calcular siguiente ID libre (`N00`…`N99`, luego `N100`…). IDs retirados no se reutilizan.
2. **Slug** kebab-case ASCII desde el título.
3. **Crear** `docs/bujo/notes/NXX-<slug>.md` con frontmatter (id, title, created, updated, place, tags, status, priority, links).
4. **Insertar** plantilla de significadores BuJo al inicio del cuerpo:
   ```markdown
   <!-- Significadores BuJo: · tarea | - nota | o evento | * prioridad | ! idea | ? duda | @ espera | > migrada | x cancelada -->
   ```
5. **Idempotencia de carpetas**: crear `docs/bujo/notes/` y `docs/bujo/collections/` si faltan.
6. **Colisión de IDs**: renombrar la nueva al siguiente ID libre + avisar.
7. **Regenerar índice** (delegar a Modo 2).
8. **Devolver**: ruta, ID asignado, sugerir `nvim <ruta>` o `make edit ID=NXX`.

### Modo 2 — Reindexar: `bujo-note: reindex`
1. **Leer** todos los `docs/bujo/notes/NXX-*.md` y parsear frontmatter.
2. **Validar** (avisar y continuar):
   - IDs duplicados → renombrar el más reciente, avisar.
   - `status` fuera de `open|migrated|done|cancelled` → tratar como `open`, avisar.
   - `priority` fuera de `high|normal|low` → tratar como `normal`, avisar.
   - Campos faltantes (`id,title,created`) → avisar, omitir del índice.
3. **mtime > updated**: detectar y **proponer** actualizar `updated: <hoy>`, preguntar por nota `[A]probar / [R]echazar`.
4. **Two-way (Opción Z)**: comparar filas actuales del `INDEX.md` contra las que el skill generaría. Si hay ediciones manuales, mostrar diff y preguntar `[A]probar y sobrescribir / [R]echazar y abortar / [M]mantener manual y regenerar el resto`.
5. **Ordenar** cada bloque por `updated` **descendente**.
6. **Reescribir** `INDEX.md` completo: 3 bloques 🔴/🟡/🟢 + sección Retiradas.
7. **Reportar**: `N indexadas, M avisos, K colisiones resueltas`.

## 🔒 Seguridad
- Nunca credenciales. Enmascarar con `[REDACTED]` o `$VARIABLE`.
- Si la nota nace de un dev-log, no copiar entero: resumir a bullets BuJo.

## 📤 Entrega final
1. Mostrar diff resumido de `INDEX.md` (si cambió).
2. Mostrar rutas creadas/renombradas.
3. Preguntar: *"¿Abro la nota en nvim (`make edit ID=NXX`) o quieres ajustar algo?"*
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
- `docs/bujo/INDEX.md` existe (regenerado por `./scripts/bujo index`).
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
Delegar a `./scripts/bujo index`.

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
  # 7. Scripts BuJo (new + open + reindex + wrapper)
  # ────────────────────────────────────────────────────────────

  # --- 7.1. bujo-new.sh ---
  if [ ! -f scripts/bujo-new.sh ]; then
    cat >scripts/bujo-new.sh <<'BUJO_NEW'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOTES_DIR="$ROOT/docs/bujo/notes"
TITLE="$1"
PRIORITY="${PRIORITY:-normal}"
TAGS_RAW="${TAGS:-pendiente}"

if [ -z "$TITLE" ]; then
  echo "❌ Uso: ./scripts/bujo-new.sh 'Título' [PRIORITY=high] [TAGS=a,b,c]"
  exit 1
fi

case "$PRIORITY" in
  high|normal|low) ;;
  *) echo "❌ PRIORITY inválida: $PRIORITY (usa high|normal|low)"; exit 1 ;;
esac

LAST_ID=$(ls "$NOTES_DIR"/N*.md 2>/dev/null | grep -oE 'N[0-9]+' | sort -V | tail -n 1 | grep -oE '[0-9]+')
NEXT_NUM=$((10#${LAST_ID:-0} + 1))
NEXT_ID=$(printf "N%02d" "$NEXT_NUM")

SLUG=$(echo "$TITLE" | iconv -t ascii//TRANSLIT | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g' | sed -E 's/^-+|-+$//g')
FILENAME="$NOTES_DIR/${NEXT_ID}-${SLUG}.md"
TODAY=$(date +%Y-%m-%d)

cat > "$FILENAME" << EOF
---
id: $NEXT_ID
title: "$TITLE"
created: $TODAY
updated: $TODAY
place: "$(pwd)"
tags: [$TAGS_RAW]
status: open
priority: $PRIORITY
links: []
---

<!-- Significadores BuJo: · tarea | - nota | o evento | * prioridad | ! idea | ? duda | @ espera | > migrada | x cancelada -->

<!-- 9 bloques ADR-light (opcional, usar si la nota madura a decisión formal):
     1. Contexto | 2. Alternativas | 3. Decisión | 4. Trade-offs | 5. Suposiciones
     6. Riesgos | 7. Métricas | 8. Referencias | 9. Siguiente paso -->

# $TITLE

## Contexto
-

## Alternativas
-

## Decisión
·

## Trade-offs
-

## Suposiciones
-

## Riesgos
-

## Métricas
-

## Referencias
-

## Siguiente paso
·
EOF

echo "✅ Creada: $FILENAME"
echo "   ID: $NEXT_ID | priority: $PRIORITY | tags: $TAGS_RAW"

"$ROOT/scripts/bujo-reindex.sh"
BUJO_NEW
    chmod +x scripts/bujo-new.sh
    echo "✅ Creado: scripts/bujo-new.sh"
  else
    echo "⏭️  scripts/bujo-new.sh ya existe"
  fi

  # --- 7.2. bujo-open.sh ---
  if [ ! -f scripts/bujo-open.sh ]; then
    cat >scripts/bujo-open.sh <<'BUJO_OPEN'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOTES="$ROOT/docs/bujo/notes"
EDITOR="${EDITOR:-nvim}"

if [[ "${1:-}" == "--id" ]]; then
  ID="${2:-}"
  [ -z "$ID" ] && { echo "❌ --id requiere NXX"; exit 1; }
  FILE=$(ls "$NOTES"/${ID}-*.md 2>/dev/null | head -1 || true)
  [ -z "$FILE" ] && { echo "❌ No existe nota $ID"; exit 1; }
  exec "$EDITOR" "$FILE"
fi

if [[ "${1:-}" == "--pick" ]]; then
  if command -v fzf >/dev/null 2>&1; then
    FILE=$(ls "$NOTES"/N*.md | fzf --preview 'head -20 {}' --prompt="Nota BuJo > " || true)
  else
    echo "Notas disponibles (más recientes primero):"
    mapfile -t FILES < <(ls -t "$NOTES"/N*.md 2>/dev/null)
    PS3="Elige número: "
    select FILE in "${FILES[@]}"; do
      [ -n "$FILE" ] && break
    done
  fi
  [ -z "${FILE:-}" ] && { echo "Cancelado."; exit 0; }
  exec "$EDITOR" "$FILE"
fi

FILE=$(ls -t "$NOTES"/N*.md 2>/dev/null | head -1 || true)
[ -z "$FILE" ] && { echo "❌ No hay notas. Crea una: ./scripts/bujo new '...'"; exit 1; }
exec "$EDITOR" "$FILE"
BUJO_OPEN
    chmod +x scripts/bujo-open.sh
    echo "✅ Creado: scripts/bujo-open.sh"
  else
    echo "⏭️  scripts/bujo-open.sh ya existe"
  fi

  # --- 7.3. bujo-reindex.sh ---
  if [ ! -f scripts/bujo-reindex.sh ]; then
    cat >scripts/bujo-reindex.sh <<'BUJO_REINDEX'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOTES_DIR="$ROOT/docs/bujo/notes"
INDEX="$ROOT/docs/bujo/INDEX.md"
TODAY="$(date +%Y-%m-%d)"

if [ ! -d "$NOTES_DIR" ]; then
  echo "❌ No existe $NOTES_DIR"
  exit 1
fi

HIGH_TMP=$(mktemp)
MED_TMP=$(mktemp)
LOW_TMP=$(mktemp)
RET_TMP=$(mktemp)
trap 'rm -f "$HIGH_TMP" "$MED_TMP" "$LOW_TMP" "$RET_TMP"' EXIT

count=0
for f in "$NOTES_DIR"/N*.md; do
  [ -f "$f" ] || continue
  id=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^id:' | head -1 | sed 's/^id:[[:space:]]*//' | tr -d "\"'")
  title=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^title:' | head -1 | sed 's/^title:[[:space:]]*//' | sed 's/^"//;s/"$//' | sed "s/^'//;s/'$//")
  status=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^status:' | head -1 | sed 's/^status:[[:space:]]*//' | tr -d "\"'")
  priority=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^priority:' | head -1 | sed 's/^priority:[[:space:]]*//' | tr -d "\"'")
  created=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^created:' | head -1 | sed 's/^created:[[:space:]]*//' | tr -d "\"'")
  updated=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^updated:' | head -1 | sed 's/^updated:[[:space:]]*//' | tr -d "\"'")
  tags=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^tags:' | head -1 | sed 's/^tags:[[:space:]]*//' | tr -d '[]' | tr -d "\"' ")

  id="${id:-?}"; title="${title:-sin título}"; status="${status:-open}"; priority="${priority:-normal}"
  created="${created:-$TODAY}"; updated="${updated:-$TODAY}"; tags="${tags:--}"
  row="| $id | $title | $status | $tags | $created | $updated |"

  case "$status" in
    cancelled|done) echo "| $id | $title | $status | $updated |" >> "$RET_TMP" ;;
    *) case "$priority" in
         high) echo "$updated|$row" >> "$HIGH_TMP" ;;
         low)  echo "$updated|$row" >> "$LOW_TMP" ;;
         *)    echo "$updated|$row" >> "$MED_TMP" ;;
       esac ;;
  esac
  count=$((count + 1))
done

sort_rows() {
  local file="$1"
  if [ -s "$file" ]; then sort -t'|' -k1,1r "$file" | cut -d'|' -f2-; fi
}

{
  echo "# 🗂️ INDEX — Capa BuJo"
  echo ""
  echo "<!-- ⚠️ AUTO-GENERADO por scripts/bujo-reindex.sh. NO EDITAR A MANO. -->"
  echo "<!-- Última regeneración: $TODAY -->"
  echo ""
  echo "## 🔴 Alta prioridad"
  echo "| ID | Título | Estado | Tags | Creada | Actualizada |"
  echo "|----|--------|--------|------|--------|-------------|"
  sort_rows "$HIGH_TMP" || true
  [ -s "$HIGH_TMP" ] || echo "| — | *sin notas* | — | — | — | — |"
  echo ""
  echo "## 🟡 Prioridad media"
  echo "| ID | Título | Estado | Tags | Creada | Actualizada |"
  echo "|----|--------|--------|------|--------|-------------|"
  sort_rows "$MED_TMP" || true
  [ -s "$MED_TMP" ] || echo "| — | *sin notas* | — | — | — | — |"
  echo ""
  echo "## 🟢 Prioridad baja"
  echo "| ID | Título | Estado | Tags | Creada | Actualizada |"
  echo "|----|--------|--------|------|--------|-------------|"
  sort_rows "$LOW_TMP" || true
  [ -s "$LOW_TMP" ] || echo "| — | *sin notas* | — | — | — | — |"
  echo ""
  echo "## ❌ Retiradas (IDs no reutilizables)"
  echo "| ID | Título | Motivo | Fecha retiro |"
  echo "|----|--------|--------|--------------|"
  if [ -s "$RET_TMP" ]; then sort -t'|' -k1,1 "$RET_TMP"; else echo "| — | *ninguna* | — | — |"; fi
  echo ""
  echo "---"
  echo "*$count notas indexadas · regenerado $TODAY*"
} > "$INDEX"

echo "✅ INDEX regenerado: $count notas → $INDEX"
BUJO_REINDEX
    chmod +x scripts/bujo-reindex.sh
    echo "✅ Creado: scripts/bujo-reindex.sh"
  else
    echo "⏭️  scripts/bujo-reindex.sh ya existe"
  fi

  # --- 7.4. Wrapper bujo ---
  if [ ! -f scripts/bujo ]; then
    cat >scripts/bujo <<'BUJO_WRAPPER'
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CMD="${1:-help}"; shift || true

case "$CMD" in
  new|n)       exec "$ROOT/scripts/bujo-new.sh" "$@" ;;
  open|o|edit) exec "$ROOT/scripts/bujo-open.sh" "$@" ;;
  index|i)     exec "$ROOT/scripts/bujo-reindex.sh" ;;
  list|ls)     ls -1t "$ROOT/docs/bujo/notes"/N*.md 2>/dev/null | head -20 || echo "Sin notas" ;;
  help|*)      cat << 'USAGE'
Uso: ./scripts/bujo <comando> [args]

  new "Título" [PRIORITY=high] [TAGS=a,b]   Crear nota nueva
  open                                       Abrir la última nota
  open --id N05                              Abrir N05 (sin escribir slug)
  open --pick                                Menú interactivo (fzf o select)
  index                                      Regenerar INDEX.md
  list                                       Listar últimas 20 notas
USAGE
  ;;
esac
BUJO_WRAPPER
    chmod +x scripts/bujo
    echo "✅ Creado: scripts/bujo (wrapper)"
  else
    echo "⏭️  scripts/bujo ya existe"
  fi

  # ────────────────────────────────────────────────────────────
  # 8. Documentación de arquitectura
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
BuJo Note (DISCO)      ← bujo-note / ./scripts/bujo new
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

## Comandos rápidos
```bash
make help                                    # ver targets
make bootstrap                               # (re)instalar todo
make check                                   # verificar stage
make edit                                    # abrir última nota
make edit ID=N05                             # abrir N05
make edit PICK=1                             # menú interactivo
./scripts/bujo new "Título" PRIORITY=high    # crear nota
./scripts/bujo index                         # regenerar INDEX
./scripts/bujo list                          # listar notas
```
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
| `bujo-note` | `./scripts/bujo new "..."` | DISCO | `docs/bujo/notes/NXX-slug.md` + INDEX |
| `runbook-generator` | `genera un runbook de esto` | BIOS | `docs/runbooks/RB-XX-slug.md` |
| `weekly-review` | `weekly review` | Ritual | Actualiza INDEX + ROADMAP + dev-log |

## Flujo diario recomendado
1. Trabaja normalmente.
2. `resume mi día` → log local seguro.
3. Si es conceptual → `./scripts/bujo new "..."`.
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
make help                                    # ver targets
make bootstrap                               # (re)instalar todo idempotente
make check                                   # verificar stage antes de commit
make hooks                                   # (re)instalar el hook pre-commit
make edit                                    # abrir última nota
./scripts/bujo new|open|index|list           # wrapper BuJo
```
EOF
    echo "✅ Creado: docs/AUTOMATIZACION-AI-SKILLS.md"
  else
    echo "⏭️  docs/AUTOMATIZACION-AI-SKILLS.md ya existe"
  fi

  # ────────────────────────────────────────────────────────────
  # 9. .githooks/pre-commit (regex ERE válidas + allowlist)
  # ────────────────────────────────────────────────────────────
  if [ ! -f .githooks/pre-commit ]; then
    cat >.githooks/pre-commit <<'HOOK'
#!/usr/bin/env bash
# ============================================================
# PAPELMAIND — pre-commit hook (Zero-Trust) — v2.5
# Bloquea el commit si hay archivos sensibles en stage.
# ============================================================
set -euo pipefail

PATTERN='(^|/)\.env($|\.)|(^|/)credentials|(^|/)docs/secure-notes/|\.(enc|key|pem|p12|pfx|kdbx)$|^(secrets?|tokens?|credentials)\.(json|ya?ml|txt)$|papelmaind-setup|(^|/)(setup|secret|token|credential).*\.md$'

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
    echo "✅ Creado: .githooks/pre-commit (v2.5 con allowlist)"
  else
    echo "⏭️  .githooks/pre-commit ya existe (no se sobrescribe)"
  fi

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
  # 10. Makefile (tabs correctos + check delega al hook + edit)
  # ────────────────────────────────────────────────────────────
  if [ ! -f Makefile ]; then
    cat >Makefile <<'MAKE'
.PHONY: help bootstrap check hooks bujo-new bujo-index edit

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

bujo-new:       ## Crea nota BuJo (make bujo-new TITLE="..." [PRIORITY=high] [TAGS=a,b])
	@./scripts/bujo-new.sh "$(TITLE)"

bujo-index:     ## Regenera INDEX.md de la Capa BuJo
	@./scripts/bujo-reindex.sh

edit:           ## Abre nota BuJo (sin arg=última | make edit ID=N05 | make edit PICK=1)
	@./scripts/bujo-open.sh $(if $(ID),--id $(ID),) $(if $(PICK),--pick,)
MAKE
    echo "✅ Creado: Makefile (v2.5 con bujo-new, bujo-index, edit)"
  else
    echo "⏭️  Makefile ya existe (no se sobrescribe)"
  fi

  # ────────────────────────────────────────────────────────────
  # 11. README — bloque idempotente
  # ────────────────────────────────────────────────────────────
  README_BLOCK='## 🧠 Sistema de conocimiento interno

Capas: **RAM** (dev-log local) → **Disco** (notas BuJo `NXX`) → **BIOS** (runbooks `RB-XX`).

- Arquitectura: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Automatización y skills: [`docs/AUTOMATIZACION-AI-SKILLS.md`](docs/AUTOMATIZACION-AI-SKILLS.md)
- Índice de notas: [`docs/bujo/INDEX.md`](docs/bujo/INDEX.md)
- Comandos rápidos: `make help` · `./scripts/bujo new|open|index|list`'

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
  # 12. Verificación final
  # ────────────────────────────────────────────────────────────
  echo ""
  echo "════════════════════════════════════════════════════════"
  echo "✅ Bootstrap v2.5 completado"
  echo "════════════════════════════════════════════════════════"
  echo ""
  echo "Estructura:"
  echo "  docs/ai-skills/            (4 skills)"
  echo "  docs/bujo/                 (INDEX 3 bloques + N00 seed)"
  echo "  docs/runbooks/"
  echo "  docs/secure-notes/dev-log/ (ignorado por Git)"
  echo "  scripts/                   (bootstrap + bujo-new + bujo-open + bujo-reindex + bujo)"
  echo "  .githooks/pre-commit       (v2.5 con allowlist)"
  echo "  Makefile                   (check→hook, edit→bujo-open)"
  echo ""
  echo "Próximos pasos:"
  echo "  1. cp .env.example .env    (rellena valores reales)"
  echo "  2. make check              (verifica stage limpio)"
  echo "  3. Empieza a usar:"
  echo "       make edit                                # abrir última nota"
  echo "       ./scripts/bujo new \"mi primera nota\"      # crear nota"
  echo "       make edit ID=N00                          # abrir por ID"
  echo "       ./scripts/bujo index                      # regenerar índice"
  echo "       resume mi día                             # dev-log (IA)"
  echo "       genera un runbook de esto                 # runbook (IA)"
  echo "       weekly review                             # ritual semanal"
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
# ────────────────────────────────────────────────────────────
# 11.5. Guía para novatos (docs/bujo/GUIA-PARA-NOVATOS.md)
# ────────────────────────────────────────────────────────────
if [ ! -f docs/bujo/GUIA-PARA-NOVATOS.md ]; then
  cat >docs/bujo/GUIA-PARA-NOVATOS.md <<'GUIA'
# 📓 Sistema de Notas BuJo — Guía para Principiantes

> **¿Qué es esto?** Un sistema de notas técnicas guardadas en tu repo (como un cuaderno Bullet Journal de programador). Cada nota es un archivo `.md` con un número (`N15`, `N16`…), y hay atajos para crearlas, abrirlas y organizarlas sin memorizar comandos.

> **¿Qué necesitas saber antes?** Solo esto: los comandos se escriben en la terminal, se ejecutan con `Enter`, y si algo se ve "trabado", casi siempre es que una comilla quedó abierta o abriste un editor — se arregla con `Esc` y `:q!` + `Enter`.

---

## 🧭 Los comandos que cubren el 90% del uso

| Comando | Qué hace |
|---|---|
| `make help` | Muestra todos los comandos disponibles |
| `make bujo-new TITLE="Título idea nueva"` | Crea una nota nueva (`NXX`) |
| `make edit` | Abre la **última** nota en nvim |
| `make edit ID=N15` | Abre la nota `N15` específica |
| `make edit PICK=1` | Menú para elegir nota (requiere `fzf`) |
| `make bujo-index` | Regenera el índice (`docs/bujo/INDEX.md`) |
| `make list` | Lista las últimas 20 notas BuJo |
| `make reindex` | Alias de `bujo-index` |
| `make check` | Verifica que no haya archivos sensibles antes de commitear |
| `./scripts/bujo new "Título idea nueva"` | Crea una nota nueva (`NXX`) |
| `./scripts/bujo list` | Lista las últimas 20 notas |
| `./scripts/bujo open --id N15` | Abre `N15` (equivalente a `make edit ID=N15`) |

---

## 🎯 Primer día: haz esto en orden (15 min)

### Paso 1 — Ver dónde estás

```bash
cd ~/proyectos-python/papelmaind
make help

Verás todos los comandos disponibles. No memorices nada, solo mira.
Paso 2 — Crear tu primera nota
bash

make bujo-new TITLE="Mi primera nota real" PRIORITY=high TAGS=inicio,prueba

Salida esperada:
text

✅ Creada: .../docs/bujo/notes/N15-mi-primera-nota-real.md
   ID: N15 | priority: high | tags: inicio,prueba
✅ INDEX regenerado: N notas → .../INDEX.md

Paso 3 — Abrirla y editarla
bash

make edit ID=N15

Se abre nvim (editor de texto en terminal). Verás la nota con frontmatter, comentarios y 9 bloques (Contexto, Alternativas, Decisión…).

Para escribir:

    Pulsa i (entra a modo insert).

    Escribe debajo de ## Contexto:
    text

    · Tarea: revisar X
    - El sistema usa Y
    ? ¿Por qué Z?

    Pulsa Esc (vuelve a modo normal).

    Escribe :wq y pulsa Enter (guarda y sale).

Paso 4 — Regenerar el índice
bash

make bujo-index

Salida esperada:
text

✅ INDEX regenerado: N notas → .../INDEX.md

Paso 5 — Ver el índice
bash

cat docs/bujo/INDEX.md

Verás tus notas clasificadas en:

    🔴 Alta prioridad (priority: high)

    🟡 Prioridad media (priority: normal)

    🟢 Prioridad baja (priority: low)

    ❌ Retiradas (status: cancelled o done)

Paso 6 — Guardar en Git
bash

make check
# ✅ Limpio: no hay archivos sensibles en stage

git add docs/bujo/
git commit -m "docs(bujo): N15 primera nota real"
git push origin main

Listo. Tu primera nota está creada, editada y versionada.
✍️ Cómo escribir dentro de una nota

Dentro de una nota, cada línea empieza con un símbolo (los "9 significadores BuJo"):
Símbolo	Significado	Ejemplo
·	Tarea (algo por hacer)	· Validar idempotency_key
-	Nota (hecho, información)	- El token expira a los 60 min
o	Evento (fecha, hito)	o Reunión con Mateo el 2026-10-25
*	Prioridad (crítico)	* Rompe el sync si falta el token
!	Idea / inspiración	! Exponer POST /sync/retry
?	Duda bloqueante	? ¿Redis o Postgres para las claves?
@	Esperando a alguien	@ Review de Mateo pendiente
>	Migrada (a otra nota)	> Ver N16
x	Cancelada	x Descartado: usar FIFO

No es obligatorio usarlos todos. Con ·, - y ? cubres el 80%.
🔄 Flujo diario (5 min)
Mañana
bash

cd ~/proyectos-python/papelmaind
cat docs/bujo/INDEX.md        # ver prioridades del día (🔴 primero)
make edit ID=NXX               # abrir la nota a trabajar

Durante el día (captura rápida)

Cuando surja algo que merece sobrevivir >1 semana:
bash

make bujo-new TITLE="Idea nueva" PRIORITY=high TAGS=pos,sync

Tarde
bash

make bujo-index               # regenerar índice
make check                    # verificar seguridad
git add docs/bujo/ && git commit -m "docs(bujo): NXX" && git push origin main

🐛 Si algo falla
"Mi terminal se quedó pasmada, solo veo cursor parpadeando"

Estás dentro de nvim. Sal con:

    Esc

    :q! + Enter (sin guardar)

    o :wq + Enter (guardando)

Nunca uses Ctrl+C para salir de nvim — lo mata de golpe y puede corromper el archivo.
"El commit no se hizo, bash muestra >"

Olvidaste cerrar la comilla. Pulsa Ctrl+C y repite:
bash

git commit -m "texto completo con comilla cerrada"

"El hook bloquea el commit con 🔴 ALTO: archivos sensibles"

Intentaste commitear algo prohibido (.env, papelmaind-setup.md, dev-log/*.md, etc.). Solución:
bash

git restore --staged <archivo>
git commit -m "..."

"make bujo-new no hace nada"

Verifica que estás en la raíz del repo:
bash

pwd     # debe terminar en /papelmaind
ls Makefile    # debe existir

"make edit abre un archivo vacío"

Estás intentando abrir una nota que no existe. Verifica primero:
bash

./scripts/bujo list

📂 ¿Dónde viven las notas?
text

docs/bujo/
├── INDEX.md              ← tabla de contenido (auto-generado, NO editar)
├── README.md             ← qué es esta capa
├── GUIA-PARA-NOVATOS.md  ← este archivo
└── notes/
    ├── N00-inicio-del-sistema.md
    ├── N01-configuracion-git.md
    ├── N14-revisar-idempotencia.md
    ├── N15-solucion-servidor.md
    └── N16-...

Nunca edites INDEX.md a mano — se regenera con make bujo-index y tus cambios se pierden.

Nunca borres notas con rm — usa status: cancelled para conservar el historial.
🎓 Reglas de oro

    Después de editar el frontmatter (priority:, status:, tags:, updated:) → make bujo-index.

    Siempre make check antes de commitear.

    Salir de nvim con :q! o :wq, nunca Ctrl+C.

    Comillas cerradas en git commit -m "...".

    No edites INDEX.md a mano.

    No borres notas con rm si quieres conservar historial.

    Una idea = una nota. No mezcles temas en un solo archivo.

🔗 Más información

    Arquitectura del sistema: docs/ARCHITECTURE.md

    Skills IA disponibles: docs/AUTOMATIZACION-AI-SKILLS.md

    Índice de notas: docs/bujo/INDEX.md

Última actualización: generado por bootstrap-docs.sh v2.6
GUIA
  echo "✅ Creado: docs/bujo/GUIA-PARA-NOVATOS.md"
else
  echo "⏭️ docs/bujo/GUIA-PARA-NOVATOS.md ya existe"
fi
