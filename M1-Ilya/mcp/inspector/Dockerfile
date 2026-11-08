# syntax=docker/dockerfile:1
# MCP Inspector 2.13.0 with the servers from the top-mcp-servers.md overview, preinstalled in the image:
# nothing is downloaded during the lecture except the responses of remote servers.
# Running and checking: ../demo/README.md, section "The Inspector stand".

FROM ghcr.io/github/github-mcp-server:v2.0.3 AS github
FROM ghcr.io/astral-sh/uv:0.13.2 AS uv

# Inspector 2.13.0 requires Node >= 22.19, the 2.1.0 reference servers require Node >= 24.
FROM node:24-slim

# chromium is for Playwright MCP and Chrome DevTools MCP (there is no Google Chrome for Linux on arm64);
# git is for mcp-server-git; sqlite3 is for the support-tickets server DB.
RUN apt-get update \
 && apt-get install -y --no-install-recommends chromium git sqlite3 ca-certificates \
 && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /usr/local/bin/
COPY --from=github /server/github-mcp-server /usr/local/bin/github-mcp-server

# Python servers are installed as uv tools in /opt, binaries go to /usr/local/bin.
ENV UV_PYTHON_INSTALL_DIR=/opt/uv/python \
    UV_TOOL_DIR=/opt/uv/tools \
    UV_TOOL_BIN_DIR=/usr/local/bin \
    UV_NO_CACHE=1
# postgres-mcp: PyPI has only 0.3.0 from May 2025, and both it and main require pglast 7.2 / 7.11, which are
# no longer on PyPI. We install the commit from the overview (15c8e333) and override pglast with 7.21 from the same 7.x line.
RUN echo 'pglast==7.21' > /tmp/pg-overrides.txt \
 && uv python install 3.13 \
 && uv tool install --python 3.13 mcp-server-fetch==2026.10.28 \
 && uv tool install --python 3.13 mcp-server-git==2026.10.28 \
 && uv tool install --python 3.13 --overrides /tmp/pg-overrides.txt \
      "postgres-mcp @ git+https://github.com/crystaldba/postgres-mcp@15c8e33353546148acc2d8bd784551cf3905d1e2" \
 && uv tool install --python 3.13 serena-agent==2.1.0 \
 && uv venv --python 3.13 /opt/mcp/venv \
 && uv pip install --python /opt/mcp/venv/bin/python mcp==2.3.0
# /opt/mcp/venv is for our own servers: own-server/faq_server.py and support-tickets from STS (the same mcp==2.3.0).

RUN npm install -g --no-fund --no-audit \
      @modelcontextprotocol/inspector@2.13.0 \
      @modelcontextprotocol/server-everything@2.1.0 \
      @modelcontextprotocol/server-filesystem@2.1.0 \
      @playwright/mcp@0.0.83 \
      chrome-devtools-mcp@1.12.0 \
      figma-developer-mcp@0.13.2 \
      @azure/mcp@4.0.0-beta.4 \
 && npm cache clean --force

# mcp-server-fetch → readabilipy: if node is present on the system, the first fetch runs npm install
# in its own folder, and /opt is not writable by the node user. We install ahead of time.
RUN cd /opt/uv/tools/mcp-server-fetch/lib/python3.13/site-packages/readabilipy/javascript \
 && npm install --no-fund --no-audit --omit=dev && npm cache clean --force

# As in the official Inspector image: listen on 0.0.0.0 inside the container (the port is published outside
# on 127.0.0.1 only, see compose.yaml), do not open a browser from inside.
# Secrets (OAuth tokens, server env) live in memory only: sign in again after a restart, nothing goes to disk.
ENV HOST=0.0.0.0 \
    DANGEROUSLY_BIND_ALL_INTERFACES=true \
    MCP_AUTO_OPEN_ENABLED=false \
    MCP_INSPECTOR_SECRET_STORE=memory \
    CLIENT_PORT=6380 \
    HOME=/home/node \
    PYTHONDONTWRITEBYTECODE=1

COPY entrypoint.sh render-catalog.mjs catalog.template.json /opt/inspector/

# Sample project for filesystem, git and Serena: a git repository with a short history.
COPY --chown=node:node workspace /home/node/workspace
USER node
WORKDIR /home/node
RUN mkdir -p /home/node/.mcp-inspector /home/node/data \
 && cd workspace \
 && git init -q -b main \
 && git -c user.name=demo -c user.email=demo@example.com add README.md .gitignore \
 && git -c user.name=demo -c user.email=demo@example.com commit -qm "Add README" \
 && git -c user.name=demo -c user.email=demo@example.com add . \
 && git -c user.name=demo -c user.email=demo@example.com commit -qm "Add ticket status graph"

EXPOSE 6380
ENTRYPOINT ["/opt/inspector/entrypoint.sh"]
