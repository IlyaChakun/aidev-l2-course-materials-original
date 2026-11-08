#!/usr/bin/env bash
# Container start: a fresh support-tickets DB (if STS is mounted), the catalog from the template, Inspector.
set -euo pipefail

if [ -d /sts/db ]; then
  echo "support-tickets: DB from /sts/db/schema.sqlite.sql and seed.sql"
  SUPPORT_DB_PATH=/home/node/data/sts.sqlite bash /sts/db/reset.sh
  SUPPORT_DB_PATH=/home/node/data/sts.sqlite bash /sts/db/seed.sh
fi

echo "Server catalog:"
node /opt/inspector/render-catalog.mjs /opt/inspector/catalog.template.json /home/node/.mcp-inspector/mcp.json

# Inspector prints the link with the token itself: the line "MCP Inspector Web is up and running at".
exec mcp-inspector --web --catalog /home/node/.mcp-inspector/mcp.json
