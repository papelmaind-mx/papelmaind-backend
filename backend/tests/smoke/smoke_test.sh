#!/usr/bin/env bash
# ============================================================
# PapelMaind — Smoke Test E2E (CHK-12)
# Requiere: API corriendo (make dev) · jq · curl
# Flujo: health → login → me → refresh → catálogo → lote → FEFO → RLS
# ============================================================
set -euo pipefail

BASE="${BASE_URL:-http://localhost:8000/api/v1}"
PASS=0; FAIL=0

check() { # name expected_status actual_status
  if [ "$2" = "$3" ]; then echo "  ✅ $1 ($3)"; PASS=$((PASS+1));
  else echo "  ❌ $1 (esperado $2, obtuvo $3)"; FAIL=$((FAIL+1)); fi
}

echo "== 1. Health =="
check "GET /health" 200 "$(curl -s -o /dev/null -w '%{http_code}' $BASE/health)"
check "GET /ready"  200 "$(curl -s -o /dev/null -w '%{http_code}' $BASE/ready)"

echo "== 2. Login admin_a =="
LOGIN=$(curl -s -X POST $BASE/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"admin_a","password":"AdminA123!"}')
ACCESS=$(echo "$LOGIN" | jq -r .access_token)
REFRESH=$(echo "$LOGIN" | jq -r .refresh_token)
[ "$ACCESS" != "null" ] && { echo "  ✅ access_token emitido"; PASS=$((PASS+1)); } || { echo "  ❌ sin token"; FAIL=$((FAIL+1)); }

echo "== 3. GET /auth/me =="
ME=$(curl -s $BASE/auth/me -H "Authorization: Bearer $ACCESS")
check "me.username == admin_a" "admin_a" "$(echo "$ME" | jq -r .user.username)"
check "me.rol == admin" "admin" "$(echo "$ME" | jq -r .tenant.rol)"

echo "== 4. Refresh ROTACIÓN =="
NEW=$(curl -s -X POST $BASE/auth/refresh -H 'Content-Type: application/json' \
  -d "{\"refresh_token\":\"$REFRESH\"}")
NEWREFRESH=$(echo "$NEW" | jq -r .refresh_token)
[ -n "$NEWREFRESH" ] && [ "$NEWREFRESH" != "$REFRESH" ] \
  && { echo "  ✅ refresh rotado (nuevo emitido)"; PASS=$((PASS+1)); } \
  || { echo "  ❌ refresh no rotó"; FAIL=$((FAIL+1)); }
REPLAY=$(curl -s -o /dev/null -w '%{http_code}' -X POST $BASE/auth/refresh \
  -H 'Content-Type: application/json' -d "{\"refresh_token\":\"$REFRESH\"}")
check "replay del refresh viejo → 401" 401 "$REPLAY"

echo "== 5. Catálogo (unidad + impuesto + artículo) =="
# Idempotente: si el seed ya creó PZA/IVA 16% (409), se toma del listado
UM_CODE=$(curl -s -X POST $BASE/catalog/unidades-medida -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"clave":"PZA","nombre":"Pieza"}' | jq -r '.id // empty')
if [ -z "$UM_CODE" ] || [ "$UM_CODE" = "null" ]; then
  UM_CODE=$(curl -s $BASE/catalog/unidades-medida -H "Authorization: Bearer $ACCESS" | jq -r '.[] | select(.clave=="PZA") | .id')
fi
IMP=$(curl -s -X POST $BASE/catalog/impuestos -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' -d '{"nombre":"IVA 16%","tipo":"iva","tasa":"0.1600"}')
IMP_ID=$(echo "$IMP" | jq -r '.id // empty')
if [ -z "$IMP_ID" ] || [ "$IMP_ID" = "null" ]; then
  IMP_ID=$(curl -s $BASE/catalog/impuestos -H "Authorization: Bearer $ACCESS" | jq -r '.[] | select(.nombre=="IVA 16%") | .id')
fi
TS=$(date +%s)
SKU_RUN="CUADERNO-$TS"
ART=$(curl -s -X POST $BASE/catalog/articulos -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' \
  -d "{\"sku\":\"$SKU_RUN\",\"descripcion\":\"Cuaderno 100 hojas\",\"unidad_medida_id\":\"$UM_CODE\",\"impuesto_id\":\"$IMP_ID\",\"precio_base\":\"35.5000\"}")
ART_ID=$(echo "$ART" | jq -r '.id // empty')
[ -n "$ART_ID" ] && [ "$ART_ID" != "null" ] && { echo "  ✅ artículo creado $SKU_RUN ($ART_ID)"; PASS=$((PASS+1)); } || { echo "  ❌ artículo: $ART"; FAIL=$((FAIL+1)); }

echo "== 6. Lotes FEFO (30d=10 + 365d=20) =="
D30=$(date -d "+30 days" +%F 2>/dev/null || date -v+30d +%F)
D365=$(date -d "+365 days" +%F 2>/dev/null || date -v+365d +%F)
L1=$(curl -s -X POST $BASE/inventory/lotes -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' \
  -d "{\"articulo_id\":\"$ART_ID\",\"numero_lote\":\"L30-$TS\",\"fecha_vencimiento\":\"$D30\",\"cantidad_actual\":\"10.000\"}")
L2=$(curl -s -X POST $BASE/inventory/lotes -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' \
  -d "{\"articulo_id\":\"$ART_ID\",\"numero_lote\":\"L365-$TS\",\"fecha_vencimiento\":\"$D365\",\"cantidad_actual\":\"20.000\"}")
STOCK=$(curl -s $BASE/catalog/articulos/$ART_ID -H "Authorization: Bearer $ACCESS" | jq -r .stock_actual)
check "stock_actual == 30.000" "30.000" "$STOCK"

echo "== 7. Hard-allocate FEFO 15 =="
ALLOC=$(curl -s -X POST $BASE/inventory/allocate -H "Authorization: Bearer $ACCESS" \
  -H 'Content-Type: application/json' \
  -d "{\"articulo_id\":\"$ART_ID\",\"cantidad\":\"15.000\"}")
check "stock restante == 15.000" "15.000" "$(echo "$ALLOC" | jq -r .stock_actual_restante)"
LOTES=$(curl -s "$BASE/inventory/lotes?articulo_id=$ART_ID" -H "Authorization: Bearer $ACCESS")
CERCANO_ESTADO=$(echo "$LOTES" | jq -r '.[0].estado')
CERCANO_QTY=$(echo "$LOTES" | jq -r '.[0].cantidad_actual')
check "lote cercano (L30) agotado" "agotado" "$CERCANO_ESTADO"
check "lote cercano cantidad == 0.000" "0.000" "$CERCANO_QTY"
check "lote lejano parcial == 15.000" "15.000" "$(echo "$LOTES" | jq -r '.[1].cantidad_actual')"

echo "== 8. RLS cross-tenant (admin_b) =="
LOGIN_B=$(curl -s -X POST $BASE/auth/login -H 'Content-Type: application/json' \
  -d '{"username":"admin_b","password":"AdminB123!"}')
ACCESS_B=$(echo "$LOGIN_B" | jq -r .access_token)
LIST_B=$(curl -s $BASE/catalog/articulos -H "Authorization: Bearer $ACCESS_B" | jq length)
check "admin_b ve 0 artículos de A" "0" "$LIST_B"
CROSS=$(curl -s -o /dev/null -w '%{http_code}' $BASE/catalog/articulos/$ART_ID \
  -H "Authorization: Bearer $ACCESS_B")
check "admin_b GET artículo de A → 404" 404 "$CROSS"

echo ""
echo "=========================================="
echo "  SMOKE: $PASS OK · $FAIL FAIL"
[ "$FAIL" = "0" ] && echo "  ✅ SMOKE TEST PASADO (CHK-12)" || { echo "  ❌ FALLAS DETECTADAS"; exit 1; }
