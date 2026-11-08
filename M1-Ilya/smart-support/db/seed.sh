#!/usr/bin/env bash
# Loads the seed. Safe to rerun: seed.sql clears the tables itself before inserting.
# If the DB does not exist yet, creates it from the DDL.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB="${SUPPORT_DB_PATH:-./data/support.sqlite}"
case "$DB" in /*) ;; *) DB="$ROOT/${DB#./}" ;; esac
[ -f "$DB" ] || bash "$ROOT/db/reset.sh"
sqlite3 "$DB" < "$ROOT/db/seed.sql"
echo "db-seed: tickets=$(sqlite3 "$DB" 'SELECT COUNT(*) FROM tickets;') agent_trace=$(sqlite3 "$DB" 'SELECT COUNT(*) FROM agent_trace;')" >&2
