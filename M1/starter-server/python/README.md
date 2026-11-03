# Starter MCP server skeleton - Python

One tool, one resource, one command to run. This is a thermometer for the environment: if the skeleton came up, the environment is ready. There is no business logic here, and there should not be.

## Versions

Snapshot as of 02.08.2026. Check for yourself before the session: `pip index versions mcp`.

| What | Version | Note |
|---|---|---|
| `mcp` (the official Python SDK) | 2.0.0, published 28.07.2026 | Installed with `pip install mcp` |
| `mcp-types` | 2.0.0 | Comes in transitively together with `mcp` |
| Protocol revision | 2026-07-28 | Negotiated automatically |
| Python | 3.10+ (checked on 3.14.6) | |

Primary sources: [PyPI `mcp`](https://pypi.org/project/mcp/), [SDK README at tag v2.0.0](https://github.com/modelcontextprotocol/python-sdk/blob/v2.0.0/README.md), [specification 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28).

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
python server.py
```

The server works over stdio and prints nothing to stdout on its own: it waits for a client. This is normal. Stop it with Ctrl+C.

## Checking without Inspector

```bash
python selfcheck.py
```

The script starts `server.py` as a separate process over stdio (the same way Inspector and the IDE do) and prints what the server returned over the protocol. Expected output:

```
protocol:      2026-07-28
server:        starter-server 0.1.0
tools:         ['ping']
resources:     ['starter://info']
ping call:     { "echo": "selfcheck", ... }
read:          { "server": "starter-server", ... }

OK: the skeleton starts, the tool and resource are visible.
```

If it ran through, the environment is set up. This is the fastest way to tell an environment problem from a code problem.

## Connecting to MCP Inspector

```bash
npx @modelcontextprotocol/inspector .venv/bin/python server.py
```

Inspector opens in the browser: the Tools tab will show `ping`, the Resources tab will show `starter://info`. Node must be installed.

The interpreter path is given explicitly on purpose. Inspector is usually started in a second terminal tab where the environment is not activated, and a bare `python` will not work there: on macOS there is no such command at all (only `python3`), and the system `python3` will not see the installed package because it lives in the venv. On Windows the path will be `.venv\Scripts\python.exe`.

There is also a headless mode, handy when you do not need a browser:

```bash
npx @modelcontextprotocol/inspector --cli .venv/bin/python server.py --method tools/list
```

About Inspector versions: take the fresh 2.x line. Inspector had two vulnerabilities, an RCE (CVE-2025-49596, fixed in 0.14.1) and an XSS escalating to command execution (CVE-2025-58444, fixed only in 0.16.6). Do not pin to an old minimum, install the current version.

## Connecting to an IDE

The specific configuration file depends on the tool, but the format is the same everywhere: command, arguments, working directory. Use **absolute** paths and the python from your own venv, otherwise the server starts in the wrong environment.

```json
{
  "mcpServers": {
    "starter-server": {
      "command": "/absolute/path/to/.venv/bin/python",
      "args": ["/absolute/path/to/server.py"]
    }
  }
}
```

## Running over Streamable HTTP

The skeleton works over stdio, and that is enough for Inspector and the IDE. But the MCP Client Tool
node in n8n cannot connect over stdio at all: it only speaks HTTP. So for part 3 of the homework the
server has to be exposed to the network, and there are exactly two ways - a bridge on top of stdio
that leaves the code untouched, and the native HTTP transport.

### stdio vs Streamable HTTP

| | stdio | Streamable HTTP |
|---|---|---|
| Who starts whom | the client starts the server as a child process itself and talks to it through its stdin/stdout | the server listens on a port in advance, the client sends ordinary POSTs to `/mcp` |
| Who owns the process | the client: close Inspector and the server is killed | you: the server lives on its own, there can be many clients at once |
| How far it reaches | only the local machine, the network is not crossed | anyone who can reach the port: a neighboring container, the LAN, the internet |
| Where state lives | in process memory you can get away with it, there is only one process | must live outside the process, otherwise behind a load balancer the next request lands on a different instance |
| Authorization | not needed: whoever started the process has the right to call the tools | needed from the first minute |
| When to use | Inspector, IDE, manual debugging | n8n, any network client, deployment |

The point is in the last two rows, the rest are consequences. On stdio the right to call a tool follows
from the right to start the process, so the question of authorization simply does not arise. As soon as the server listens
on a port, anyone who can reach that port can call your tool, and the
`Authorization` header stops being a formality. In-memory state breaks in exactly the same place: while there is
one process, a global dict works, but behind a load balancer it lies silently, without an error.

### normal: the supergateway bridge on top of stdio

[supergateway](https://github.com/supercorp-ai/supergateway) starts your stdio server as a child
process and exposes it outward over Streamable HTTP. Not a single line changes in `server.py`.

```bash
npx -y supergateway --stdio ".venv/bin/python server.py" --outputTransport streamableHttp --port 8000
```

Run the command from the skeleton folder, in a separate terminal tab; on Windows the interpreter path
will be `.venv\Scripts\python.exe`. The endpoint for the client is `http://localhost:8000/mcp`. The `/mcp` path
is the default (`--streamableHttpPath`), the port is set with `--port`.

Two things you need to know about this route so you are not surprised later.

**The bridge lets nobody in and checks nothing.** No token, no headers: whoever reaches the port
has called your tool. So the bridge is a tool for local work, not a way to expose
the server outward.

**Through the bridge the connection slides to the old revision.** The HTTP side of supergateway (3.4.3) is built on
the first-line `@modelcontextprotocol/sdk` package, which tops out at `2025-11-25`. The client
will negotiate `2025-11-25` with the bridge, the bridge will call your server over stdio with the old `initialize`, and the
server will serve it in backward-compatibility mode - this is covered below, in the block "In revision
2026-07-28 there is no `initialize` phase, but the old mode is still served". Tools work
in this setup, but revision `2026-07-28` is not reachable in it at all:
the bridge accepts the `--protocolVersion 2026-07-28` flag, but its own HTTP side answers
`Bad Request: Unsupported protocol version` and falls back to `2025-11-25`. For the homework this is
fine, but it is worth knowing.

### advanced: native Streamable HTTP

The same server, the same file, only the way of starting it changes: instead of `transport="stdio"` -
`transport="streamable-http"`.

```python
server.run(transport="streamable-http", host="127.0.0.1", port=8000)
```

Defaults: `host="127.0.0.1"`, `port=8000`, path `/mcp` (the `streamable_http_path` argument). The server
runs on uvicorn, which comes with the `mcp` package - nothing needs to be installed separately.

A bearer token check does not fit into this form of launch: it is added by the HTTP layer, not by MCP.
So we take the app and attach the middleware ourselves. `server.streamable_http_app()`
returns an ordinary Starlette app, and from there it is like any ASGI project:

```python
import os
import sys

import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from mcp.server.transport_security import TransportSecuritySettings

PORT = 8000
TOKEN = os.environ["MCP_BEARER_TOKEN"]


class BearerAuth(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        if request.headers.get("authorization") != f"Bearer {TOKEN}":
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)


if __name__ == "__main__":
    app = server.streamable_http_app(
        transport_security=TransportSecuritySettings(
            allowed_hosts=[
                f"localhost:{PORT}",
                f"127.0.0.1:{PORT}",
                f"host.docker.internal:{PORT}",   # without this line n8n in Docker gets a 421
            ],
            allowed_origins=["*"],
        ),
    )
    app.add_middleware(BearerAuth)
    print(f"starter-server: Streamable HTTP at http://localhost:{PORT}/mcp", file=sys.stderr)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
```

The token is taken from an environment variable and is not committed to the repository:
`MCP_BEARER_TOKEN=$(openssl rand -hex 32) python server.py`. The comparison is simple because the task
here is simple: prove that a request without the right header does not reach the tools.
A real check (JWT signature, introspection at the authorization server) is already
`TokenVerifier` and `AuthSettings` from the SDK, and they have a separate documentation page:
[Authorization](https://py.sdk.modelcontextprotocol.io/run/authorization/). On the first homework
you do not need to go there.

About `allowed_origins=["*"]`, it is deliberate: this is local development. If you expose the server outward,
list the domains explicitly.

**If you have the first line of the SDK** (`mcp>=1.28,<2`, the `FastMCP` class), running over HTTP looks different:
`run()` there accepts only `transport` and `mount_path`, and the host and port are set in the constructor -
`FastMCP(name="starter-server", host="127.0.0.1", port=8000)`, then
`mcp.run(transport="streamable-http")`. The `/mcp` path is the same.

### Connecting from n8n

In the MCP Client Tool node (current version 1.4) three fields are filled in:

| Field | Value |
|---|---|
| **Endpoint** | `http://localhost:8000/mcp`, the full URL with the scheme |
| **Server Transport** | `HTTP Streamable`. The `Server Sent Events` option is marked Deprecated, do not use it |
| **Authentication** | `None` for the bridge; `Bearer Auth` for the advanced server, the token goes into n8n credentials |

**n8n in Docker.** Inside the container `localhost` is the container itself, not your machine, so
the Endpoint is written as `http://host.docker.internal:8000/mcp`. The server must then listen on
`0.0.0.0`, not `127.0.0.1`: on `127.0.0.1` it is visible only to processes on its own machine, and a request
from the container will not reach it.

**n8n Cloud.** The cloud cannot reach your laptop at all, neither via `localhost` nor via
`host.docker.internal`. You need either a tunnel (Cloudflare Tunnel, ngrok) or a deployed
server instance. This is the case where self-hosted n8n next to the server saves an evening.

### Common errors at this step

**HTTP 421 on a request from Docker.** The SDK has DNS rebinding protection enabled, and it checks
the `Host` header. By default the list of allowed hosts is empty, so a request with
`Host: host.docker.internal:8000` bounces with `421 Misdirected Request` before any logic runs.
From the n8n side this looks like "the tool does not respond", and there is nothing meaningful in the server logs.
It is fixed by adding the line `host.docker.internal:<port>` to `allowed_hosts`, as in the example above. For `run()`
the same argument has the same name: `transport_security=...`.

**Host forgotten, port taken.** `host="127.0.0.1"` is the default, and when launched from Docker it silently
does not work: the server came up, the port is listened on, and from outside the container there is nothing. To be reachable from
the container you need `host="0.0.0.0"`. While you are at it, check that port 8000 is free: `lsof -i :8000`.

**The server is run over HTTP, but Inspector connects over stdio.** These are two different ways of launching,
and they do not work at the same time: the file either listens on a port or waits for a client on stdin. To check
HTTP mode, start Inspector with a URL, not a command, and do not forget the token header.

**The token matches, but you still get 401.** The comparison is against the whole string, including the word
`Bearer` and a single space. An extra newline at the end of the environment variable (a frequent gift
from `echo` instead of `printf`) breaks the comparison, while looking like the right token.

## What to change for your project

| Place in `server.py` | What you do |
|---|---|
| `@server.tool()` + the `ping` function | Replace it with your own tool. The function name becomes the tool name, the docstring becomes the description the agent uses to pick the tool. Arguments are taken from type annotations, the SDK builds the JSON Schema itself |
| `@server.resource("starter://info")` | Replace the URI and the body. The assignment requires at least one resource: the DB schema or a state summary |
| `MCPServer(name=...)` | The name of your own server |

A guideline for the assignment: 3 tools for normal, 5 for advanced. The skeleton gives one, you design the rest yourself, and that is the substance of the homework.

A resource with a parameter in the URI is registered as a resource template (advanced level):

```python
@server.resource("db://entity/{id}")
def entity(id: str) -> str:
    ...
```

Parameter names in the URI must match the function argument names, otherwise the SDK raises an error at registration.

## Common errors

**`mcp` and `fastmcp` are different packages.** `mcp` is the official SDK (currently 2.0.0), `fastmcp` is a separate third-party framework with its own numbering (version 3.4.5 as of 02.08.2026). Their imports are different and incompatible. You need `mcp` here, do not install `fastmcp`. Mixing these two is the most frequent breakage at the start.

**`FastMCP` is gone.** In line 1.x the high-level class was called `FastMCP` and lived in `mcp.server.fastmcp`. In 2.x it is called `MCPServer` and is imported as `from mcp.server import MCPServer`. If you found a snippet on the internet with `from mcp.server.fastmcp import FastMCP` and it fails with `ImportError`, that is a recipe from 1.x. Most MCP materials were written before 28.07.2026, so such snippets will keep turning up. Check against the installed package:

```bash
.venv/bin/python -c "from mcp.server import MCPServer; print(MCPServer)"
```

**`print()` to stdout pollutes the protocol.** In the stdio transport stdout is taken by JSON-RPC, and any stray output lands in the stream as a corrupted message. The connection does not necessarily break: our client, for example, complains with a parse error on the junk line and keeps working. But whether the client survives it or drops the connection depends on the client, and you should not count on leniency. The symptom, if it does not survive, looks like "Inspector does not see the server". For debugging, write to stderr: `print(..., file=sys.stderr)`.

**In revision 2026-07-28 there is no `initialize` phase, but the old mode is still served.** The revision made the protocol stateless and sessionless: `initialize`/`initialized` and the `Mcp-Session-Id` header were removed from it, `server/discover` was added instead, and each request carries its own version and capabilities in the `params._meta` envelope (key `io.modelcontextprotocol/protocolVersion`).

Backward compatibility is preserved, though, and it is important not to mix this up: **the connection picks the mode by the first request**. If a request with the envelope arrives, the new revision with `server/discover` follows. If one arrives without the envelope, the old mode is switched on, in which `initialize` still responds and returns `2025-11-25`. So "`initialize` was removed" is true of the revision itself, but not of the server's behavior.

The practical consequence is only for those who poke the server by hand with bare JSON-RPC. Without the envelope, `server/discover` returns `-32601 Method not found`, and `tools/list` returns `-32602 Invalid request parameters`. Through the SDK and Inspector the envelope is added automatically, and you do not need to think about it.
