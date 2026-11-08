#!/usr/bin/env bash
# Recreates the DB file from the DDL. Path from SUPPORT_DB_PATH (default ./data/support.sqlite).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB="${SUPPORT_DB_PATH:-./data/support.sqlite}"
case "$DB" in /*) ;; *) DB="$ROOT/${DB#./}" ;; esac
mkdir -p "$(dirname "$DB")"
rm -f "$DB" "$DB-journal" "$DB-wal" "$DB-shm"
sqlite3 "$DB" < "$ROOT/db/schema.sqlite.sql"
echo "db-reset: schema applied to ${DB#$ROOT/}" >&2
