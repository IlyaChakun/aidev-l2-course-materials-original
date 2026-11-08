#!/usr/bin/env bash
# Stand check before the lecture: one real call per catalog server,
# through the CLI of the same Inspector inside the container. The stand must be up (docker compose up -d).
#
#   bash check.sh            # all servers
#   bash check.sh faq git    # only the named ones
#
# The calls are read-only, except support-tickets: there is one rejected update_ticket (the status does not change,
# but a row appears in agent_trace; docker compose restart inspector brings back a fresh DB).
# Compatible with bash 3.2 from macOS.
set -uo pipefail
cd "$(dirname "$0")"

insp() {
  docker compose exec -T inspector mcp-inspector --cli --format json \
    --catalog /home/node/.mcp-inspector/mcp.json --stored-auth-only "$@" 2>/dev/null
}

# The call for a server; prints nothing → tools/list only; "oauth" → a remote server with browser sign-in.
call_for() {
  case "$1" in
    everything)      echo "--tool-name echo --tool-arg message=hello" ;;
    filesystem)      echo "--tool-name list_directory --tool-arg path=/home/node/workspace" ;;
    fetch)           echo "--tool-name fetch --tool-arg url=https://example.com --tool-arg max_length=200" ;;
    git)             echo "--tool-name git_log --tool-arg repo_path=/home/node/workspace --tool-arg max_count=2" ;;
    github)          echo "--tool-name get_me" ;;
    context7)        echo "--tool-name resolve-library-id --tool-arg libraryName=react --tool-arg query=hooks" ;;
    serena)          echo "--tool-name find_symbol --tool-arg name_path_pattern=check_transition --tool-arg include_body=true" ;;
    playwright)      echo "--tool-name browser_navigate --tool-arg url=https://example.com" ;;
    chrome-devtools) echo "--tool-name new_page --tool-arg url=https://example.com" ;;
    postgres)        echo "--tool-name execute_sql --tool-arg sql=STATUS_COUNTS" ;;
    cloudflare-docs) echo "--tool-name search_cloudflare_documentation --tool-arg query=Workers" ;;
    faq)             echo "--tool-name search_faq --tool-arg query=password" ;;
    support-tickets) echo "--tool-name update_ticket --tool-arg ticket_id=1 --tool-arg new_status=new --tool-arg agent=check" ;;
    notion|sentry|supabase|cloudflare) echo "oauth" ;;
  esac
}

summarize() {
  node -e '
    let s = ""; process.stdin.on("data", d => s += d).on("end", () => {
      try {
        const r = JSON.parse(s).result;
        if (r.tools) return console.log(`${r.tools.length} tools`);
        const text = (r.content || []).map(c => c.text || `[${c.type}]`).join(" ");
        console.log((r.isError ? "isError: " : "") + text.replace(/\s+/g, " ").slice(0, 110));
      } catch { console.log(s.replace(/\s+/g, " ").slice(-160)); }
    });'
}

if [ $# -gt 0 ]; then
  servers="$*"
else
  servers=$(docker compose exec -T inspector node -e \
    'console.log(Object.keys(require("/home/node/.mcp-inspector/mcp.json").mcpServers).join(" "))')
fi

fails=0
for s in $servers; do
  call=$(call_for "$s")
  if [ "$call" = "oauth" ]; then
    out=$(insp --server "$s" --method tools/list); rc=$?
    if [ $rc -eq 0 ]; then echo "ok     $s: already signed in"
    elif [ $rc -eq 3 ]; then echo "oauth  $s: responds, browser sign-in needed (Connect in the UI)"
    else echo "FAIL   $s (rc=$rc): $(printf '%s' "$out" | summarize)"; fails=$((fails+1)); fi
    continue
  fi
  if [ -z "$call" ]; then
    out=$(insp --server "$s" --method tools/list); rc=$?
  else
    # shellcheck disable=SC2086 — call arguments have no spaces inside, except the SQL below
    set -- $call
    args=()
    for a in "$@"; do
      [ "$a" = "sql=STATUS_COUNTS" ] && a="sql=SELECT status, count(*) FROM tickets GROUP BY status ORDER BY status"
      args+=("$a")
    done
    out=$(insp --server "$s" --method tools/call "${args[@]}"); rc=$?
  fi
  summary=$(printf '%s' "$out" | summarize)
  # support-tickets: we expect a rejection (rc=5, isError) with the allowed transitions — that is the check.
  if [ "$s" = "support-tickets" ] && [ $rc -eq 5 ]; then rc=0; fi
  if [ $rc -eq 0 ]; then echo "ok     $s: $summary"; else echo "FAIL   $s (rc=$rc): $summary"; fails=$((fails+1)); fi
done
echo
echo "Errors: $fails"
[ $fails -eq 0 ]
