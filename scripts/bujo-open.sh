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
