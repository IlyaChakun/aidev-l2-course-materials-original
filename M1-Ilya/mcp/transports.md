# MCP transports: stdio and Streamable HTTP

MCP messages are JSON-RPC: `{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{…}}`. A transport only decides how these messages travel from the client to the server and back. The messages themselves are the same on every transport.

The spec has two standard transports: **stdio** for local servers and **Streamable HTTP** for remote ones. There was a third one, HTTP+SSE, but it has been deprecated since 2025-03-26. Streamable HTTP was introduced to replace it.

## stdio: the server as a subprocess

- The client (Claude Code, Cursor, Inspector) starts the server itself, with a command from its config, such as `npx …` or `uvx …`.
- The client writes to the server's stdin, and the server answers on its stdout. One line is one message, and a message must not contain newlines.
- Only MCP messages may go to stdout. Logs go to stderr. A stray `print()` to stdout can break the protocol. Python SDK 2.3.0 guards against this: while the server runs, it moves the real stdout pipe to another descriptor and points stdout at stderr. Other SDKs may not, so log to stderr anyway.

This is an exchange with `faq_server.py` from the stand, with one line sent by hand:

```
→ {"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"search_faq","arguments":{"query":"refund"},"_meta":{…}}}
← {"jsonrpc":"2.0","id":1,"result":{"content":[…],"isError":false,…}}
```

What stdio gives you: no network and no ports, nothing to deploy, and the server runs with the user's permissions on the user's machine. The limit: the server lives only on the client's machine, and every client needs its own process. You can't connect Notion, Sentry or any SaaS this way: you can't run the service's process locally, and the service has thousands of users.

## First attempt: HTTP+SSE (2024-11-05)

To let a server run remotely, the first revision of the spec described HTTP with two endpoints:

1. The client opens `GET /sse` and keeps that connection open for the whole session. The server's first event is the address for sending messages:
   ```
   event: endpoint
   data: /messages/?session_id=105ce2c7246a457ead91d1391579a830
   ```
2. The client sends requests as separate `POST /messages/?session_id=…`.
3. Answers to those POSTs don't come back in the POST response. They come over that open SSE stream.

What was wrong with it. In PR #206, which introduced Streamable HTTP, the spec authors named three problems with HTTP+SSE:

- **"Requires the server to maintain a long-lived connection with high availability".** Every client holds an open connection to the server for as long as it works. Serverless platforms (Lambda, Cloudflare Workers) can't do that, and a regular deploy drops the connections.
- **"Does not support resumability".** If the stream breaks, the answers the server already sent into it are lost. There is no way to recover.
- **"Can only deliver server messages over SSE".** Even a simple request with a short answer needs a separate long-lived stream. One more consequence (my reading of the design, not a quote): the POST and the stream have to land on the same server instance, or there is no one to send the answer to. So behind a load balancer such servers need sticky sessions.

## Streamable HTTP (2025-03-26)

The idea: one endpoint and plain HTTP, with an SSE stream only where it is really needed.

- One address, usually `/mcp`. Every client message is a separate `POST /mcp`.
- The server answers a request **in the response to that same POST**. The answer can be plain `application/json`, or `text/event-stream` if the server wants to send progress or its own request before the final answer. The SSE stream became an option inside a response, not a required permanent channel.
- `GET /mcp` is optional: it is a separate stream for messages the server sends on its own initiative.
- Sessions are optional too. The server may return an `Mcp-Session-Id` header in response to `initialize`. The client then sends it with every following request, and `DELETE /mcp` ends the session.
- A broken stream can be resumed: SSE events are numbered, and the client reconnects with a `Last-Event-ID` header.

The main consequence, in the words of the same PR: **"Stateless servers are now possible"**. A server that needs no sessions or streams is a plain HTTP request-response handler. It can sit behind any load balancer or run on serverless.

This is the exchange in this version, from the stand, protocol version 2025-11-25:

```
POST /mcp   {"method":"initialize",…}
← 200  content-type: text/event-stream
       mcp-session-id: 2bba522ea78e41408cd20189564bd45b
       event: message
       data: {"id":1,"result":{"protocolVersion":"2025-11-25","capabilities":{…}}}

POST /mcp   mcp-session-id: 2bba…  mcp-protocol-version: 2025-11-25
            {"method":"tools/call","params":{"name":"search_faq",…}}
← 200  text/event-stream, carrying the answer with id 2

POST /mcp   no mcp-session-id
← 400  {"error":{"code":-32600,"message":"Bad Request: Missing session ID"}}
```

This Python SDK server uses sessions by default, so it rejects a request without `Mcp-Session-Id`.

## What changed in the current revision, 2026-07-28

Streamable HTTP was taken all the way, and the protocol became stateless:

- The `initialize` handshake and sessions are gone, along with the `Mcp-Session-Id` header. Every POST stands on its own: the protocol version and the client capabilities travel in the request's `_meta`.
- Instead of the handshake there is `server/discover`: what the server can do and which versions it supports.
- New required headers: `MCP-Protocol-Version`, `Mcp-Method` and `Mcp-Name` (the name of the tool, resource or prompt). The method and the name are visible in the headers without parsing the body. If a header doesn't match the body, the server answers 400.
- The separate `GET` stream is gone: the server answers GET and DELETE with 405. If a response stream breaks, there is no resumption: the client repeats the request with a new id.
- HTTP+SSE is formally marked Deprecated and may be removed in a future revision.

The same server at the same address, with a client speaking version 2026-07-28:

```
POST /mcp   mcp-protocol-version: 2026-07-28  mcp-method: tools/call  mcp-name: search_faq
            {"method":"tools/call","params":{"name":"search_faq","arguments":{"query":"refund"},
             "_meta":{"io.modelcontextprotocol/protocolVersion":"2026-07-28",
                      "io.modelcontextprotocol/clientCapabilities":{}}}}
← 200  content-type: application/json
       {"id":2,"result":{"content":[…],"isError":false,…}}

GET /mcp
← 405
```

No session, no stream, plain JSON back. Python SDK 2.3.0 serves both old clients (with a session) and new ones (without) at one address. In Inspector, the `protocolEra` field in the stand's catalog switches between them.

## The network level

### Where MCP sits in OSI

MCP is an application-layer protocol (OSI layer 7). It defines messages and their meaning, and borrows everything below from the transport. OSI is a teaching model; in TCP/IP terms the picture is the same: MCP is the application layer, and HTTP is its carrier.

| OSI layer | stdio | Streamable HTTP |
|---|---|---|
| 7, application | MCP (JSON-RPC 2.0) | MCP (JSON-RPC 2.0) in the body of HTTP, which is also layer 7 |
| 6, presentation | UTF-8 JSON, one message per line | JSON or an SSE stream (`text/event-stream`), TLS for remote servers |
| 5, session | the process lifetime is the session | `Mcp-Session-Id` before 2026-07-28, none after |
| 4, transport | none: an OS pipe | TCP |
| 3, network | none | IP |

stdio has no network at all. On the stand, a stdio server's descriptors are two pipes from the client (moved by the SDK to fd 6 and 7) and stderr. The only sockets are the event loop's internal pair; nothing listens on a port.

SSE is not a separate protocol, unlike WebSocket: there is no `Upgrade`. It is a regular HTTP response that stays open until the server is done. This is the raw response to a POST, captured on the stand:

```
HTTP/1.1 200 OK
content-type: text/event-stream
connection: keep-alive
mcp-session-id: 39ca20fe4c5e41778bcc804504e97fe3
Transfer-Encoding: chunked

160
event: message
data: {"jsonrpc":"2.0","id":1,"result":{…}}

0
```

Each `event: message` block is one MCP message. The `0` chunk ends the response.

### How it differs from a regular HTTP API

A REST API maps operations onto HTTP: the URL names the resource, the verb names the action, the status code tells the outcome. MCP only uses HTTP as a pipe for JSON-RPC:

- **One URL, always POST.** The operation is the `method` field in the body, not the URL plus verb. Since 2026-07-28 it is duplicated in the `Mcp-Method` and `Mcp-Name` headers, so proxies, gateways and logs can see which tool is called without parsing JSON. If a header doesn't match the body, the server answers 400 (on the stand: code `-32020`, "mcp-name header does not match the request body's 'name' parameter").
- **The HTTP status is not the result.** A failed tool call is HTTP 200 with `"isError": true` in the body. On the stand, both missing arguments and an unknown tool name came back as 200. HTTP statuses describe the transport only: 202 for an accepted notification, 400 for bad headers or version, 401 for missing auth, 404 for an expired session (before 2026-07-28), 405 for GET and DELETE (since 2026-07-28).
- **One request can get several messages back.** With an SSE response, the server sends progress and notifications first and the final answer last. In REST, one request gets one body.
- **The server can ask the client.** Before 2026-07-28 the server could send its own requests (sampling, elicitation) over SSE. Since 2026-07-28 it returns an `InputRequiredResult`, and the client answers with a new request.
- **The client must accept both formats:** `Accept: application/json, text/event-stream`.

What stays the same as in any HTTP API: TLS, load balancers, and auth with a bearer token in `Authorization` (MCP uses OAuth 2.1 for this). For stdio the spec doesn't use OAuth: credentials come from the environment. A local HTTP server has one extra duty: it must check the `Origin` header and should listen only on 127.0.0.1, otherwise any web page in the user's browser can reach it (DNS rebinding).

## Summary: which one to pick

| | stdio | Streamable HTTP |
|---|---|---|
| Where the server runs | on the client's machine, as a subprocess | anywhere, at a URL |
| Who starts it | the client, with a command from its config | the service owner, in advance |
| Clients per server | one | any number |
| Access | the user's permissions, tokens in env | OAuth or a token in a header |
| Examples on the stand | filesystem, git, serena, playwright, postgres, faq | context7, notion, sentry, supabase, cloudflare |
| Typical failure | `print()` to stdout, `npx`/`uvx` not found | OAuth login missing, network, wrong URL |

Rule of thumb: your own server for yourself and your machine is stdio. A service for many users or for a team is Streamable HTTP. Don't use HTTP+SSE for new servers.

## How this was checked

On 30.10.2026 on the stand from [inspector/](inspector/): `faq_server.py` was started with `server.run("streamable-http")` and with `server.run("sse")` (mcp==2.3.0), and requests were sent by hand, including a raw HTTP/1.1 request over a TCP socket. The stdio server's descriptors were read from `/proc`. All the exchanges above are real responses, shortened with `…`.

Spec:
- [2024-11-05, HTTP+SSE](https://modelcontextprotocol.io/specification/2024-11-05/basic/transports)
- [2025-03-26, Streamable HTTP](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports) and [changelog](https://modelcontextprotocol.io/specification/2025-03-26/changelog)
- [PR #206: why Streamable HTTP](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/206)
- [2025-11-25, transports](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports)
- [2026-07-28, Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http) and [changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog)
- [2026-07-28, authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization): OAuth 2.1, and credentials from the environment for stdio
