#!/usr/bin/env bash
# One-shot setup of demo 05 without the UI:
#   1) owner account via REST (local demo login),
#   2) credentials via `n8n import:credentials` from credentials/credentials.template.json,
#      filled from OPENAI_API_KEY INSIDE the container (the filled file never touches the host disk, removed right after import),
#   3) workflows via `n8n import:workflow`, publish the chat workflow, restart n8n so the chat webhook is registered.
# The key value is never printed.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; cd "$ROOT"
if [ -f .env ]; then set -a; . ./.env; set +a; fi

C="m2-demo-n8n-rag-n8n"
PORT="${DEMO05_N8N_PORT:-5681}"
BASE="http://127.0.0.1:${PORT}"
EMAIL="${DEMO05_EMAIL:-demo@example.com}"
PASSWORD="${DEMO05_PASSWORD:-Demo05Lumen2026}"
RT="/tmp/demo05"

[ -n "${OPENAI_API_KEY:-}" ] || { echo "ERROR: OPENAI_API_KEY is empty. Export it or put it into .env (never into chat)."; exit 1; }
docker ps --format '{{.Names}}' | grep -qx "$C" || { echo "ERROR: container $C is not running (make up)"; exit 1; }

# /healthz answers before DB migrations finish; running the CLI during migrations corrupts the DB.
# /healthz/readiness turns 200 only when the DB is migrated and connected.
wait_up() {
  for _ in $(seq 1 120); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' "$BASE/healthz/readiness")" = "200" ] && return 0; sleep 1
  done
  echo "ERROR: n8n is not ready on $BASE/healthz/readiness"; exit 1
}
wait_up

# 1) Owner: only on the very first run (n8n shows the setup page until an owner exists).
NEED_OWNER="$(curl -s "$BASE/rest/settings" | python3 -c 'import json,sys; d=json.load(sys.stdin); print(d.get("data", d)["userManagement"]["showSetupOnFirstLoad"])')"
if [ "$NEED_OWNER" = "True" ]; then
  code="$(curl -s -o /dev/null -w '%{http_code}' -X POST "$BASE/rest/owner/setup" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$EMAIL\",\"firstName\":\"Demo\",\"lastName\":\"Teacher\",\"password\":\"$PASSWORD\"}")"
  echo "owner created: $EMAIL (HTTP $code)"
else
  echo "owner already exists: $EMAIL"
fi

trap 'docker exec "$C" rm -rf "$RT" >/dev/null 2>&1 || true' EXIT
docker exec "$C" mkdir -p "$RT"
docker cp credentials/credentials.template.json "$C:$RT/credentials.template.json" >/dev/null
docker cp workflows/lumen-ingest.json "$C:$RT/lumen-ingest.json" >/dev/null
docker cp workflows/lumen-chat.json "$C:$RT/lumen-chat.json" >/dev/null

# 2) Credentials: fill the template from the env var inside the container, import, delete.
docker exec -e OPENAI_API_KEY "$C" node -e '
const fs = require("fs");
const tpl = fs.readFileSync(process.argv[1], "utf8");
const filled = tpl.replace("${OPENAI_API_KEY}", process.env.OPENAI_API_KEY);
JSON.parse(filled);
fs.writeFileSync(process.argv[2], filled, { mode: 0o600 });
' "$RT/credentials.template.json" "$RT/credentials.json"
docker exec "$C" n8n import:credentials --input="$RT/credentials.json" 2>&1 | grep -v -i -E 'migration|deprecat' | tail -1
docker exec "$C" rm -f "$RT/credentials.json"

# 3) Workflows.
docker exec "$C" n8n import:workflow --input="$RT/lumen-ingest.json" 2>&1 | grep -v -i -E 'migration|deprecat' | tail -1
docker exec "$C" n8n import:workflow --input="$RT/lumen-chat.json" 2>&1 | grep -v -i -E 'migration|deprecat' | tail -1
docker exec "$C" n8n publish:workflow --id=demo05LumenChat 2>&1 | grep -v -i -E 'migration|deprecat' | tail -1

echo "restarting n8n to register the chat webhook..."
docker restart "$C" >/dev/null
wait_up
echo "done. UI: http://localhost:${PORT} (login $EMAIL / see DEMO05_PASSWORD in .env.example)"
echo "next: make ingest, then make chat-url"
