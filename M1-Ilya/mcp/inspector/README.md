# MCP Inspector stand for the M1 lecture

Inspector 2.13.0 in Docker: the 13 servers from the [overview](../top-mcp-servers.md) are already in the list, plus our own `faq` and `support-tickets`.

```bash
cp .env.example .env            # once
docker compose up --build -d    # first build ~3 min
docker compose logs inspector | grep -A1 'up and running'   # the link with the token, port 6380
bash check.sh                   # one call per server, ends with "Errors: 0"
```

Setup, demo 2 on the stand, what to show on each server, the own server, tokens and OAuth are in the [demo guide](../demo/README.md), sections 1.3, 3 and 5.

| File | What it is |
|---|---|
| `Dockerfile` | The image: Inspector, Node and Python servers at exact versions, Chromium, GitHub MCP |
| `compose.yaml` | Inspector + Postgres for Postgres MCP Pro, mounts, port `127.0.0.1:6380` |
| `catalog.template.json` | The server list; `${VAR}` and `x-requires-*` are processed by `render-catalog.mjs` at start |
| `entrypoint.sh`, `render-catalog.mjs` | Container start: the `support-tickets` DB, the catalog, Inspector |
| `own-server/faq_server.py` | The smallest own server (section 5.4) |
| `workspace/` | Sample project for filesystem, git and Serena; becomes a git repository in the image |
| `postgres/seed.sql` | 20,000 tickets for Postgres MCP Pro |
| `check.sh` | Stand check: one real call per server |
