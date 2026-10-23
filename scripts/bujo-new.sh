#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NOTES_DIR="$ROOT/docs/bujo/notes"
TITLE="$1"

if [ -z "$TITLE" ]; then 
  echo "❌ Uso: ./scripts/bujo-new.sh 'Título de la decisión'"
  echo "   Ej:  make bujo-new TITLE=\"Sincronización POS con idempotencia\""
  exit 1
fi

# 1. Calcular siguiente ID (N00, N01, N02...)
LAST_ID=$(ls "$NOTES_DIR"/N*.md 2>/dev/null | grep -oE 'N[0-9]+' | sort -V | tail -n 1 | grep -oE '[0-9]+')
NEXT_NUM=$((10#${LAST_ID:-0} + 1))
NEXT_ID=$(printf "N%02d" $NEXT_NUM)

# 2. Generar slug kebab-case robusto (maneja tildes, mayúsculas y espacios)
SLUG=$(echo "$TITLE" | \
  iconv -t ascii//TRANSLIT | \
  tr '[:upper:]' '[:lower:]' | \
  sed -E 's/[^a-z0-9]+/-/g' | \
  sed -E 's/^-+|-+$//g')

FILENAME="$NOTES_DIR/${NEXT_ID}-${SLUG}.md"
TODAY=$(date +%Y-%m-%d)

# 3. Crear archivo con plantilla y 9 significadores
cat > "$FILENAME" << INNER_EOF
---
id: $NEXT_ID
title: "$TITLE"
created: $TODAY
updated: $TODAY
place: "$(pwd)"
tags: [pendiente]
status: open
priority: normal
links: []
---
<!-- 1. Contexto --> <!-- 2. Alternativas --> <!-- 3. Decisión -->
<!-- 4. Trade-offs --> <!-- 5. Suposiciones --> <!-- 6. Riesgos -->
<!-- 7. Métricas --> <!-- 8. Referencias --> <!-- 9. Siguiente paso -->

# $TITLE

· 
INNER_EOF

echo "✅ Creada: $FILENAME"

# 4. Regenerar índice automáticamente
echo "🔄 Actualizando índice..."
"$ROOT/scripts/bujo-reindex.sh"
