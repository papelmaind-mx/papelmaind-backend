#!/usr/bin/env bash
# consolidate_canon.sh — Une 3 partes XML, valida y corre canon_lint
set -euo pipefail

if [ "$#" -ne 4 ]; then
  echo "Uso: $0 parte1.txt parte2.txt parte3.txt salida.xml"
  exit 2
fi

OUT="$4"
echo "→ Consolidando..."
cat "$1" "$2" "$3" > "$OUT"

echo "→ Validando XML..."
if ! xmllint --noout "$OUT"; then
  echo "❌ XML malformado — revisa los cortes entre partes"
  exit 1
fi
echo "✅ XML bien formado"

if [ -f scripts/canon_lint.py ]; then
  echo "→ Ejecutando canon_lint..."
  python3 scripts/canon_lint.py --verbose "$OUT" || {
    echo "❌ Lint con issues — ver reporte arriba"
    exit 1
  }
  echo "✅ Consolidación + lint limpios"
else
  echo "⚠️  canon_lint.py no encontrado — solo se validó el XML"
fi
