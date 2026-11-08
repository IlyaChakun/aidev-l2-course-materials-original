#!/usr/bin/env bash
# Server check via MCP Inspector (CLI mode): all tools and resources, including an accepted and a rejected update_ticket.
# Runs on a SEPARATE DB (data/inspector-check.sqlite), does not touch the working one.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
INSPECTOR="@modelcontextprotocol/inspector@${INSPECTOR_VERSION:-2.13.0}"
DB="$ROOT/data/inspector-check.sqlite"

SUPPORT_DB_PATH="$DB" bash "$ROOT/db/reset.sh" && SUPPORT_DB_PATH="$DB" bash "$ROOT/db/seed.sh" || exit 1

# Isolated Inspector directory: the user's personal ~/.mcp-inspector/mcp.json is neither read nor written.
SCRATCH="$(mktemp -d)"
export MCP_CATALOG_PATH="$SCRATCH/catalog.json"
trap 'rm -rf "$SCRATCH"' EXIT
# Inspector takes the command as a single token, and the environment does not reach the child process:
# so the path to the temporary DB is baked into a wrapper, and update_ticket does NOT touch the working data/support.sqlite.
WRAP="$SCRATCH/run-server.sh"
printf '#!/bin/sh\nSUPPORT_DB_PATH=%s exec %s\n' "$DB" "$ROOT/scripts/server-stdio.sh" > "$WRAP"
chmod +x "$WRAP"

fails=0
# Inspector returns exit code 5 if the tool answered isError:true. For rejection checks this is the expected outcome.
run_insp() {
  echo; echo "### inspector --cli $*"
  npx -y "$INSPECTOR" --cli "$WRAP" "$@"
}
insp() {
  run_insp "$@"; rc=$?
  echo "(exit $rc, expected 0)"
  [ "$rc" -eq 0 ] || fails=$((fails+1))
}
insp_rejected() {
  run_insp "$@"; rc=$?
  echo "(exit $rc, expected 5 = tool returned isError)"
  [ "$rc" -eq 5 ] || fails=$((fails+1))
}

WORK_DB="$ROOT/data/support.sqlite"
before="$( [ -f "$WORK_DB" ] && shasum "$WORK_DB" | cut -d' ' -f1 || echo absent )"
echo "inspector version: ${INSPECTOR}"
insp --method tools/list
insp --method resources/list
insp --method resources/read --uri support://status-graph
insp --method resources/read --uri support://summary
insp --method resources/read --uri support://db-schema
insp --method tools/call --tool-name get_ticket --tool-arg ticket_id=1
insp_rejected --method tools/call --tool-name get_ticket --tool-arg ticket_id=9999
insp --method tools/call --tool-name list_tickets --tool-arg status=new --tool-arg limit=3
insp --method tools/call --tool-name update_ticket --tool-arg ticket_id=1 --tool-arg new_status=answered --tool-arg agent=inspector --tool-arg "answer=Open Settings > Security > Change password." --tool-arg category=account --tool-arg priority=low --tool-arg score=92
insp_rejected --method tools/call --tool-name update_ticket --tool-arg ticket_id=1 --tool-arg new_status=new --tool-arg agent=inspector
insp_rejected --method tools/call --tool-name update_ticket --tool-arg ticket_id=16 --tool-arg new_status=answered --tool-arg agent=inspector --tool-arg answer=x

echo; echo "### agent_trace after the run (ticket 1 and 16)"
sqlite3 -header -column "$DB" "SELECT id, ticket_id, agent, status_from, status_to, outcome, error_code FROM agent_trace WHERE agent='inspector' ORDER BY id;"
after="$( [ -f "$WORK_DB" ] && shasum "$WORK_DB" | cut -d' ' -f1 || echo absent )"
[ "$before" = "$after" ] && echo "working DB untouched: yes ($before)" || echo "working DB untouched: NO ($before -> $after)"
echo; echo "inspector-check finished, unexpected exit codes: $fails"
rm -f "$DB"
exit 0
