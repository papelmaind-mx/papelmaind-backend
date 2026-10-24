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
FILE=$(ls -t "$NOTES"/N*.md 2>/dev/null | head -1 || true)
[ -z "$FILE" ] && { echo "❌ No hay notas"; exit 1; }
exec "$EDITOR" "$FILE"
