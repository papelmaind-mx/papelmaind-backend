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
