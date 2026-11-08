# smart-support · the M1 example project

"Smart technical support": the running example from the M1 lectures. A ticket moves through the statuses `new → answered → escalated`. This folder holds the MCP server over the ticket DB.

The MCP demos from the lecture run on this code: see [`../mcp/demo/`](../mcp/demo/README.md).

> This is one possible solution, not a template to copy. Your homework is your own domain, your own statuses and your own tool contract.

The docs and code comments are in English. The seed data, the expected results and the test data are in Russian, as in the original project: the tickets are in Russian. Tickets 5 and 9 are in English and German on purpose: they are the "other language" edge cases.

## What is inside

| Path | What it is |
|---|---|
| [`mcp_server/`](mcp_server/) | The MCP server: 3 tools (`get_ticket`, `list_tickets`, `update_ticket`) and 3 resources, Python SDK `mcp==2.3.0`. Layers: `domain` (status graph, no SDK or DB) → `repository` (SQLite) → `service` (one transaction: read → validate → write → trace) → `mcp` (tools, resources, error format) |
| [`db/`](db/) | SQLite DDL with a trigger that forbids invalid transitions, a seed of 20 tickets and 10 `agent_trace` rows, reset and seed scripts |
| [`contracts/`](contracts/) | JSON Schema of the ticket as `get_ticket` returns it |
| [`m1/`](m1/) | The IDE-client test scenario and its expected result, written down before the run |
| [`scripts/`](scripts/) | Server launch over stdio, the Inspector check, the DB check against the expected result |

## The MCP server

You need [uv](https://docs.astral.sh/uv/) (it installs Python 3.13), `sqlite3` and `make`.

```bash
make setup               # mcp_server/.venv with the pinned dependencies
make db-reset db-seed    # data/support.sqlite: 20 tickets
make test-server         # 48 tests
make selfcheck           # 19/19: a real stdio session against the server
```

Connect it to an MCP client (absolute paths):

```json
{
  "mcpServers": {
    "support-tickets": {
      "type": "stdio",
      "command": "/abs/path/to/smart-support/scripts/server-stdio.sh",
      "env": { "SUPPORT_DB_PATH": "/abs/path/to/smart-support/data/support.sqlite" }
    }
  }
}
```

Inspector without the Docker stand:

```bash
CLIENT_PORT=6390 MCP_SANDBOX_PORT=6391 npx -y @modelcontextprotocol/inspector@2.13.0 \
  "$PWD/scripts/server-stdio.sh" -e SUPPORT_DB_PATH=./data/support.sqlite --protocol-era auto
```

Use Inspector 2.12.0 or newer: 2.0.0–2.11.0 have published RCE advisories.

## All tests

```bash
make setup
make test                # scripts and server
```
