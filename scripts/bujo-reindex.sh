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

  # Extraer campos del frontmatter (corregido: escape de comillas válido)
  id=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^id:' | head -1 | sed 's/^id:[[:space:]]*//' | tr -d "\"'" | tr -d "'")
  title=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^title:' | head -1 | sed 's/^title:[[:space:]]*//' | sed 's/^"//;s/"$//' | sed "s/^'//;s/'$//")
  status=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^status:' | head -1 | sed 's/^status:[[:space:]]*//' | tr -d "\"'" | tr -d "'")
  priority=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^priority:' | head -1 | sed 's/^priority:[[:space:]]*//' | tr -d "\"'" | tr -d "'")
  created=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^created:' | head -1 | sed 's/^created:[[:space:]]*//' | tr -d "\"'" | tr -d "'")
  updated=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^updated:' | head -1 | sed 's/^updated:[[:space:]]*//' | tr -d "\"'" | tr -d "'")
  tags=$(sed -n '/^---$/,/^---$/p' "$f" | grep -E '^tags:' | head -1 | sed 's/^tags:[[:space:]]*//' | tr -d '[]' | tr -d "\"'" | tr -d ' ')

  # Defaults
  id="${id:-?}"
  title="${title:-sin título}"
  status="${status:-open}"
  priority="${priority:-normal}"
  created="${created:-$TODAY}"
  updated="${updated:-$TODAY}"
  tags="${tags:--}"

  row="| $id | $title | $status | $tags | $created | $updated |"

  case "$status" in
    cancelled|done)
      echo "| $id | $title | $status | $updated |" >> "$RET_TMP"
      ;;
    *)
      case "$priority" in
        high)  echo "$updated|$row" >> "$HIGH_TMP" ;;
        low)   echo "$updated|$row" >> "$LOW_TMP"  ;;
        *)     echo "$updated|$row" >> "$MED_TMP"  ;;
      esac
      ;;
  esac
  count=$((count + 1))
done

# Ordenar por updated descendente
sort_rows() {
  local file="$1"
  if [ -s "$file" ]; then
    sort -t'|' -k1,1r "$file" | cut -d'|' -f2-
  fi
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
  if [ -s "$RET_TMP" ]; then
    sort -t'|' -k1,1 "$RET_TMP"
  else
    echo "| — | *ninguna* | — | — |"
  fi
  echo ""
  echo "---"
  echo "*$count notas indexadas · regenerado $TODAY*"
} > "$INDEX"

echo "✅ INDEX regenerado: $count notas → $INDEX"
