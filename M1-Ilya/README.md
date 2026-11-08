# M1 · MCP and n8n: lecture materials

The slides, demos and example project from the M1 lecture session: MCP first, then n8n, then the session wrap-up. The homework text, the starter server, fixtures and guides are in [`../M1/`](../M1/README.md); start the homework from [`../M1/homework.md`](../M1/homework.md).

## What is here

| Path | What it is |
|---|---|
| [`mcp/slides/m1-lecture.html`](mcp/slides/m1-lecture.html) | **MCP lecture** deck. Opens in a browser with a double click |
| [`mcp/slides/mcp-spec-lifecycle-en.html`](mcp/slides/mcp-spec-lifecycle-en.html) | How the MCP specification evolved from 2024-11-05 to 2026-07-28, revision by revision: a side deck linked from the MCP lecture |
| [`mcp/top-mcp-servers.md`](mcp/top-mcp-servers.md) | An overview of 13 MCP servers worth knowing: what each does, how to connect it, what to watch out for |
| [`mcp/transports.md`](mcp/transports.md) | MCP transports: stdio and Streamable HTTP, when to use which |
| [`mcp/demo/`](mcp/demo/README.md) | **MCP demos** step by step: bad vs good error (A/B), the protocol in Inspector, the agent moving a ticket through the statuses in Claude Code. One setup script |
| [`mcp/inspector/`](mcp/inspector/README.md) | An MCP Inspector stand in Docker: the 13 servers from the overview plus our own, ready to try |
| [`n8n/slides/n8n-lecture.html`](n8n/slides/n8n-lecture.html) | **n8n lecture** deck |
| [`wrap-up/m1-wrap-up.html`](wrap-up/m1-wrap-up.html) | Session wrap-up: the summary of both parts, the homework summary, videos, frequently asked questions |
| [`smart-support/`](smart-support/README.md) | The example project the MCP demos run on: the MCP server over a ticket DB |

## Running the demos

The quickest path to see the main idea of the lecture (the server, not the prompt, guarantees the lifecycle):

```bash
bash mcp/demo/demo-setup.sh setup    # needs uv, sqlite3, make
```

Then follow [`mcp/demo/README.md`](mcp/demo/README.md), demo 3.

Keys go into `.env` files only. They are in `.gitignore`: never commit them and never paste them into a chat.
