#!/usr/bin/env bash
# Checks the DB after the IDE scenario against the expectation and prints lines for the report. Read-only.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DB="${1:-$ROOT/data/ide-scenario.sqlite}"
python3 "$ROOT/scripts/check_expected.py" ide-scenario "$DB"; rc=$?
echo; echo "### tickets 5 and 6"
sqlite3 -header -column "$DB" "SELECT id, status, category, priority, score, substr(coalesce(answer,''),1,40) AS answer, substr(coalesce(escalation_reason,''),1,40) AS reason FROM tickets WHERE id IN (5,6);"
echo; echo "### agent_trace for tickets 5 and 6"
sqlite3 -header -column "$DB" "SELECT id, ticket_id, agent, status_from, status_to, outcome, error_code FROM agent_trace WHERE ticket_id IN (5,6) ORDER BY id;"
exit $rc
