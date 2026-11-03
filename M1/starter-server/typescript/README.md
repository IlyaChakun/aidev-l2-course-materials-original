# Starter MCP server skeleton - TypeScript

One tool, one resource, one command to run. This is a thermometer for the environment: if the skeleton came up, the environment is ready. There is no business logic here, and there should not be.

## The package fork: why 2.x here and not `@modelcontextprotocol/sdk`

On 27.07.2026 the second line of the TypeScript SDK was released, but it came out **in new packages**. The old `@modelcontextprotocol/sdk` package stayed on the first line. Because of this, `@modelcontextprotocol/sdk@latest` gives you **not** the freshest SDK version but the first line.

| Package | Version as of 02.08.2026 | What it is |
|---|---|---|
| `@modelcontextprotocol/sdk` | 1.30.0 (published 27.07.2026) | First line. Maximum protocol revision: **2025-11-25** |
| `@modelcontextprotocol/server` | 2.0.0 (published 27.07.2026) | Second line, server part |
| `@modelcontextprotocol/core` | 2.0.0 | Common types and schemas of the second line |
| `@modelcontextprotocol/client` | 2.0.0 | Client of the second line, needed here only for `selfcheck` |

**The second line is used here, and here is the reason.** The current revision of the specification is 2026-07-28. The `@modelcontextprotocol/sdk@1.30.0` package does not support it: its list of supported versions ends at `2025-11-25`. You can check it with one command:

```bash
node -p "require('@modelcontextprotocol/sdk/types.js').SUPPORTED_PROTOCOL_VERSIONS"
# [ '2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05', '2024-10-07' ]
```

That is, a skeleton on the first line would work, but would not conform to the current revision. For the homework that is acceptable, for a starter template it is not.

A practical consequence for schemas: in the first line `inputSchema` was described by a Zod shape (a bare object `{ message: z.string() }`), in the second it is a Standard Schema, i.e. `z.object({ message: z.string() })`. Standard Schema means that instead of Zod you can use Valibot or ArkType. The old form is still accepted in the second line, but is marked deprecated.

Primary sources: [specification 2026-07-28](https://modelcontextprotocol.io/specification/2026-07-28), npm pages [`@modelcontextprotocol/server`](https://www.npmjs.com/package/@modelcontextprotocol/server) and [`@modelcontextprotocol/sdk`](https://www.npmjs.com/package/@modelcontextprotocol/sdk).

## Versions

Snapshot as of 02.08.2026. Check for yourself before the session: `npm view @modelcontextprotocol/server version`.

| What | Version |
|---|---|
| `@modelcontextprotocol/server` | ^2.0.0 |
| `zod` | ^4.2.0 (comes in as a dependency of `server`, checked on 4.4.3) |
| Protocol revision | 2026-07-28 |
| Node | **>= 22.18** (checked on 24.18.0) |

A fresh Node is needed because `.ts` is run directly here, without a build step: starting with 22.18 Node can strip types itself. There is intentionally no separate `tsconfig.json` or `tsc` in the skeleton.

## Installation

```bash
npm ci
```

`package-lock.json` sits next to it, and `npm ci` installs exactly the versions the skeleton was checked on: `@modelcontextprotocol/server` and `/client` 2.0.0, `zod` 4.4.3. This matters more than usual, because the second line came out on 27.07.2026, and a minor released in the middle of the cohort would arrive silently. `npm install` will also work, but it may update the pinned versions.

## Running

```bash
npm start        # node src/server.ts
```

The server works over stdio and prints nothing to stdout on its own: it waits for a client. This is normal. Stop it with Ctrl+C.

## Checking without Inspector

```bash
npm run selfcheck
```

The script starts `src/server.ts` as a separate process over stdio (the same way Inspector and the IDE do) and prints what the server returned over the protocol. Expected output:

```
protocol:   2026-07-28
server:     {"name":"starter-server","version":"0.1.0"}
tools:      ["ping"]
resources:  ["starter://info"]
ping call:  [{"type":"text","text":"{ \"echo\": \"selfcheck\", ... }"}]
read:       [{"uri":"starter://info", ...}]

OK: the skeleton starts, the tool and resource are visible.
```

If it ran through, the environment is set up. This is the fastest way to tell an environment problem from a code problem.

## Connecting to MCP Inspector

```bash
npm run inspector        # npx @modelcontextprotocol/inspector node src/server.ts
```

Inspector opens in the browser: the Tools tab will show `ping`, the Resources tab will show `starter://info`.

There is also a headless mode, handy when you do not need a browser:

```bash
npx @modelcontextprotocol/inspector --cli node src/server.ts --method tools/list
```

About Inspector versions: take the fresh 2.x line. Inspector had two vulnerabilities, an RCE (CVE-2025-49596, fixed in 0.14.1) and an XSS escalating to command execution (CVE-2025-58444, fixed only in 0.16.6). Do not pin to an old minimum, install the current version.

## Connecting to an IDE

The specific configuration file depends on the tool, but the format is the same everywhere: command, arguments, working directory. Use **absolute** paths, and for `node` too.

```json
{
  "mcpServers": {
    "starter-server": {
      "command": "/absolute/path/to/node",
      "args": ["/absolute/path/to/src/server.ts"]
    }
  }
}
```

An absolute path to `node` is needed because with an nvm install the right version lives inside `~/.nvm/versions/node/<version>/bin/`, not in the system PATH. An IDE launched from Finder or from a menu does not inherit the shell environment, and `"command": "node"` will not resolve for it. Look up your own path with `which node`.

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
one process, a module-level `Map` works, but behind a load balancer it lies silently, without an error.

### normal: the supergateway bridge on top of stdio

[supergateway](https://github.com/supercorp-ai/supergateway) starts your stdio server as a child
process and exposes it outward over Streamable HTTP. Not a single line changes
in `src/server.ts`.

```bash
npx -y supergateway --stdio "node src/server.ts" --outputTransport streamableHttp --port 8000
```

Run the command from the skeleton folder, in a separate terminal tab. The endpoint for the client is
`http://localhost:8000/mcp`. The `/mcp` path is the default (`--streamableHttpPath`), the port is set with
`--port`.

Two things you need to know about this route so you are not surprised later.

**The bridge lets nobody in and checks nothing.** No token, no headers: whoever reaches the port
has called your tool. So the bridge is a tool for local work, not a way to expose
the server outward.

**Through the bridge the connection slides to the old revision.** The HTTP side of supergateway (3.4.3) is built on
the first-line `@modelcontextprotocol/sdk` package - the very one whose ceiling is `2025-11-25`. The client
will negotiate `2025-11-25` with the bridge, the bridge will call your server over stdio with the old `initialize`,
and `serveStdio` will serve it in legacy mode - this is covered below, in the block "In revision 2026-07-28
there is no `initialize` phase, but the old mode is still served".
Tools work in this setup, but revision `2026-07-28`, for the sake of which the second line of
packages is used here, is not reachable in it at all: the bridge accepts the `--protocolVersion 2026-07-28` flag,
but its own HTTP side answers `Bad Request: Unsupported protocol version` and falls back.
For the homework this is fine, but it is worth knowing.

### advanced: native Streamable HTTP

In the second line HTTP is arranged differently than in the first: you do not construct the transport by hand. Instead,
`createMcpHandler` makes a handler that speaks the web-standard `Request`/`Response`, and under
Node it is wrapped once with an adapter. The adapter lives in a separate package,
`@modelcontextprotocol/node` - this is how the packages are cut in the second line: the core separately, the binding
to the runtime separately. It is already added to the skeleton's dependencies, a plain `npm install` installs it
together with the rest.

Next the server is started with plain `node:http`, and the token check becomes what it really is:
an ordinary header check before the request is handed to MCP.

```ts
import { createServer as createHttpServer } from 'node:http';
import { createMcpHandler } from '@modelcontextprotocol/server';
import { toNodeHandler } from '@modelcontextprotocol/node';

const PORT = 8000;
const TOKEN = process.env.MCP_BEARER_TOKEN ?? '';

// createServer() is the factory from this same file, the one that registers ping and starter://info.
// It is called on every request: a server instance lives for one exchange and does not accumulate state.
const handler = createMcpHandler(() => createServer());
const mcp = toNodeHandler(handler);

createHttpServer((req, res) => {
  if (req.headers.authorization !== `Bearer ${TOKEN}`) {
    res.writeHead(401, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ error: 'unauthorized' }));
    return;
  }
  void mcp(req, res);
}).listen(PORT, '0.0.0.0', () => {
  console.error(`starter-server: Streamable HTTP at http://localhost:${PORT}/mcp`);
});
```

The token is taken from an environment variable and is not committed to the repository:
`MCP_BEARER_TOKEN=$(openssl rand -hex 32) node src/server.ts`. The comparison is simple because the
task here is simple: prove that a request without the right header does not reach the tools.
The package also has a "grown-up" route - `requireBearerAuth` and `verifyBearerToken` - but it is designed
for OAuth: it requires a verifier object and rejects tokens without an expiry. A shared secret does
not fit into it, and on the first homework it is not needed.

The bridge and the native launch are easy to keep in one file: `serveStdio(createServer)` under one condition,
the code above under another, the branch chosen by an environment variable or an argument. The tool logic
does not change at all - only the way they are called from outside changes.

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

**The server listens on `127.0.0.1`, but it is called from a container.** Then the server came up, the port is listened on,
and from outside the container there is nothing. That is exactly why the example above has `'0.0.0.0'`. While you are at it, check
that the port is free: `lsof -i :8000`.

**`createMcpHandler` does not check `Host` and `Origin` - this is deliberate and it is your responsibility.**
The second line keeps validation separate from the entry point, and by default there is none at all:
a request with any `Host` will be served. While the server listens on localhost this is convenient (n8n in Docker
connects without any setup, unlike the Python skeleton next to it). As soon as the server goes
beyond the local machine, DNS rebinding protection must be enabled by hand - `hostHeaderValidation`
and `originValidation` from `@modelcontextprotocol/node`, both accept a list of allowed names.

**The server is run over HTTP, but Inspector connects over stdio.** These are two different ways of launching,
and they do not work at the same time: the file either listens on a port or waits for a client on stdin. To check
HTTP mode, start Inspector with a URL, not a command, and do not forget the token header.

**The token matches, but you still get 401.** The comparison is against the whole string, including the word
`Bearer` and a single space. An extra newline at the end of the environment variable (a frequent gift
from `echo` instead of `printf`) breaks the comparison, while looking like the right token.

## What to change for your project

| Place in `src/server.ts` | What you do |
|---|---|
| `server.registerTool('ping', ...)` | Replace it with your own tool. The first argument is the name, `description` is what the agent uses to pick the tool, `inputSchema` is the argument schema in the form `z.object({...})` |
| `server.registerResource('info', 'starter://info', ...)` | Replace the URI and the callback body. The assignment requires at least one resource: the DB schema or a state summary |
| `new McpServer({ name: ... })` | The name of your own server |

A guideline for the assignment: 3 tools for normal, 5 for advanced. The skeleton gives one, you design the rest yourself, and that is the substance of the homework.

A resource with a parameter in the URI is registered via `ResourceTemplate` (advanced level):

```ts
import { ResourceTemplate } from '@modelcontextprotocol/server';

server.registerResource(
  'entity',
  new ResourceTemplate('db://entity/{id}', { list: undefined }),
  { title: 'Entity by id' },
  async (uri, { id }) => ({ contents: [{ uri: uri.href, text: `...${id}...` }] })
);
```

## Common errors

**`@modelcontextprotocol/sdk@latest` gives the first line, not the second.** This is not a typo in the registry or a broken tag: the second line lives in other packages. If you install `sdk` and expect the second-line API, you will get an import mismatch out of nowhere. You need `@modelcontextprotocol/server` here.

**Tool schema: `z.object({...})`, not a bare object.** First-line snippets pass a shape object like `{ message: z.string() }` to `inputSchema`. In the second line the right form is `z.object({ message: z.string() })`. The old one still works, but is marked deprecated and will break one day.

**`console.log` pollutes the protocol.** In the stdio transport stdout is taken by JSON-RPC, and any stray output lands in the stream as a corrupted message. The connection does not necessarily break: our client, for example, complains with a parse error on the junk line and keeps working. But whether the client survives it or drops the connection depends on the client, and you should not count on leniency. The symptom, if it does not survive, looks like "Inspector does not see the server". For debugging, write to stderr: `console.error(...)`.

**The client speaks the old revision by default.** The second-line client's default negotiation position is `legacy`, and it will negotiate 2025-11-25 even if the server supports 2026-07-28. To get the current revision you need an explicit `versionNegotiation: { mode: 'auto' }` - this is done and commented in `src/selfcheck.ts`. It does not affect Inspector's behavior, which negotiates on its own.

**In revision 2026-07-28 there is no `initialize` phase, but the old mode is still served.** The revision made the protocol stateless and sessionless: `initialize`/`initialized` and the `Mcp-Session-Id` header were removed from it, `server/discover` was added instead, and each request carries its own version and capabilities in the `params._meta` envelope (key `io.modelcontextprotocol/protocolVersion`).

Backward compatibility is preserved, though, and it is important not to mix this up: **the connection picks the mode by the first request**. If a request with the envelope arrives, the new revision with `server/discover` follows. If one arrives without the envelope, `serveStdio` pins the old mode to the connection and serves it, so `initialize` still responds and returns `2025-11-25`. This is the default behavior, and it is switched with the `legacy` option of `serveStdio`. So "`initialize` was removed" is true of the revision itself, but not of the server's behavior.

The practical consequence is only for those who poke the server by hand with bare JSON-RPC. Without the envelope, `server/discover` returns `-32601 Method not found`, while `tools/list` the server will happily serve as for an old client. In the Python skeleton next to it the same request answers `-32602`: the SDKs behave differently, and it is better not to count on it. Through the SDK and Inspector the envelope is added automatically, and you do not need to think about it.
