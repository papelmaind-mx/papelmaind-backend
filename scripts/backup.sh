#!/usr/bin/env bash
# Backup PostgreSQL (canon Makefile backup): pg_dump gz + retención 30 días
set -euo pipefail
STAMP=$(date +%Y%m%d_%H%M%S)
OUT_DIR="${BACKUP_DIR:-./backups}"
mkdir -p "$OUT_DIR"
PGHOST="${PGHOST:-localhost}" PGPORT="${PGPORT:-5433}" \
PGUSER="${PGUSER:-papelmind}" PGDATABASE="${PGDATABASE:-papelmind}" \
pg_dump | gzip > "$OUT_DIR/papelmind_$STAMP.sql.gz"
echo "✅ backup: $OUT_DIR/papelmind_$STAMP.sql.gz"
find "$OUT_DIR" -name "papelmind_*.sql.gz" -mtime +30 -delete
