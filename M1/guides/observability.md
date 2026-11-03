# Observability of your own server: what to measure and with what

> Compiled 02.08.2026. The OpenTelemetry conventions were cross-checked against protocol revision
> `2026-07-28` by hand on 02.08.2026. SDK behavior was verified by measuring seven scenarios on a
> live `mcp` 2.0.0 server.

## Why this file

Agents do not file bug reports. You will learn about a broken contract not from a ticket but from
a graph.

Your own server in prod reveals itself in three ways: it goes silent, it lies, it burns money.
The first is caught by availability, the second by the error contract, the third by tokens.

And the mechanical reason to take this up right now: **there are no sessions in the protocol any
more, and with them went the key that all correlation rested on.** The session identifier was what
tied a dozen calls into one conversation and gave you a line in the audit. Now there is nothing to
tie them with except the trace. This is not an improvement in observability, it is moving it from
the transport into the application: before, you could skip thinking about it, now you have to.

The second peculiarity: the replacement is named not by a vendor but inside the protocol itself.
Protocol Logging is deprecated by SEP-2577, and OpenTelemetry is named as the official replacement
by SEP-414. You can argue about the backend, but not about the format.

**Boundary of this file.** Only the runtime of your own server is covered here. Tracing backends
as a product, evals and the quality of agent answers are separate topics later in the program.

---

## 1. How a trace is now assembled

| Element | Value |
|---|---|
| Client span | kind CLIENT, written by the request initiator, covers the time from sending to receiving the response. **19 attributes** |
| Server span | kind SERVER, written by the handler, covers the time from receiving to sending the result. **19 attributes**. 21 distinct between the two: seventeen shared, the client one plus `server.address` and `server.port`, the server one plus `client.address` and `client.port` |
| Span name | `{method} {target}`, where target is the name of the tool or prompt. Do not put the resource URI in the name by default: cardinality |
| Context propagation | `traceparent`, `tracestate`, `baggage` inside the request's `params._meta`, **without a DNS prefix** |
| Parenthood | "The MCP client span becomes a **parent** of the MCP server span **regardless of transport used**; span links allow recording the transport context (if present)" |
| Duplication | if a tool call is already traced by external GenAI instrumentation, the instrumentation **SHOULD NOT** create a separate span and instead adds the MCP attributes to the existing one |
| Error inside a result | "When `CallToolResult` is returned with `isError` set to `true`, this attribute **SHOULD** be set to `tool_error`". Conditionally Required level, on success the attribute is not set at all |
| Four metrics | histogram, unit `s`, bucket boundaries `[0.01 … 300]`, 14 values from 10 ms to 5 minutes. **The boundaries are not in the YAML model**, they live only in the text of the convention |

### Two reasons that cannot be merged into one sentence

**Why the keys have no prefix.** The specification: "As an exception to the prefix requirement above,
the keys `traceparent`, `tracestate`, and `baggage` are reserved for OpenTelemetry trace context
propagation", and the reason is named in the same place: "to maintain compatibility with existing implementations
and OpenTelemetry semantic conventions for MCP".

**Why `_meta` at all, and not HTTP headers.** A different question and a different answer. MCP
context is independent of the transport: one MCP request can be served by several HTTP requests
(for example, because of retries), and one streamable request can carry several MCP messages. If
you rely on HTTP propagation, the trace breaks exactly at the process boundary, and on stdio it
does not exist at all.

### Example of context propagation

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "get-weather",
    "_meta": {
      "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
      "baggage": "tenantId=acme,serverNode=DF%2028"
    }
  },
  "id": 1
}
```

`baggage` travels through the same channel, so the tenant identifier reaches the server through a
standard mechanism and you do not need to invent your own header.

### Span tree for one tool call

```
invoke_agent weather-agent          INTERNAL   trace=t1 span=s1
  ├─ chat {model}                   CLIENT     trace=t1 span=s2 parent=s1
  ├─ tools/call get-weather         CLIENT     trace=t1 span=s3 parent=s1   ← MCP client
  │    └─ tools/call get-weather    SERVER     trace=t1 span=s4 parent=s3   ← your server
  └─ chat {model}                   CLIENT     trace=t1 span=s5 parent=s1
```

**Tokens are spent by `s2` and `s5`, not by `s3` and `s4`.** On top of Streamable HTTP, HTTP spans
are added, and `s4` gets a **link** to them while remaining a child of `s3`: the transport is
visible and does not break the hierarchy.

### How to read the transport in telemetry

The convention's table has five rows, not three.

| Transport | `network.transport` | `network.protocol.name` and `.version` | `mcp.protocol.version` |
|---|---|---|---|
| stdio | `pipe` | none | any |
| Streamable HTTP | `tcp` or `quic` | `http`, version `2` | 2025-06-18 or newer |
| HTTP with SSE | `tcp` or `quic` | `http`, version `1.1` or `2` | 2024-11-05 or older |
| Custom: websockets | `tcp` | `websocket` | any |
| Custom: gRPC | `tcp` | `http`, version `2` | any |

The convention's comment verbatim: "`mcp.protocol.version` distinguishes streamable HTTP from SSE".
The word "only" must not appear here: the HTTP version also differs, but the signal is weak (the
second one permits the same 2), and what reliably distinguishes them is the protocol version.

Separately: the headers `Mcp-Method` and `Mcp-Name`, mandatory since July 28, give you metrics at
the perimeter without parsing the body. Access logs of a proxy, gateway and WAF become usable for
MCP analytics for the first time, and limits can be set on a specific expensive tool. On stdio this
layer does not and will not exist.

---

## 2. What the SDK gives you and what you add by hand

Good news. In the official Python SDK 2.0.0 your server is already traced:

```python
from mcp.server import MCPServer

mcp = MCPServer("Bookshop")

@mcp.tool()
def search_books(query: str) -> str:
    """Search the catalog by title or author."""
    return f"Found 3 books matching {query!r}."
```

Not a single line about telemetry. Verbatim from the documentation page: "Your server is already
traced. You don't have to add anything… It is there the moment you call `MCPServer(...)`".
There are no configuration keys at all: what is configured is not the SDK but the ordinary
OpenTelemetry exporter.

To make the spans visible:

```
uv add opentelemetry-sdk opentelemetry-exporter-otlp
```

and configure the exporter in the usual way. The server code does not change. The SDK's own
dependency is only on `opentelemetry-api`, so "With no SDK and no exporter installed, creating a span is
a **no-op**".

### What the SDK puts on a span and what it does not

**Puts** (`mcp/server/_otel.py`, version 2.0.0):

- always: `mcp.method.name`, `mcp.protocol.version`;
- on requests: `jsonrpc.request.id` (notifications do not have it);
- on `tools/call`: `gen_ai.operation.name = execute_tool` and `gen_ai.tool.name`;
- on `prompts/get`: `gen_ai.prompt.name`;
- on error: `error.type` and `rpc.response.status_code`, with `isError: true` the value is `tool_error`.

**Does not put:** any of the four metrics · `mcp.session.id` (and that is right, there are no
sessions) · span links to the ambient context, although the convention says SHOULD · `network.*`,
`server.address`, `client.address`.

**The client side is instrumented separately and not per the convention.** The span is named
`MCP send {method} {target}`, kind CLIENT, and carries only two attributes. The convention
requires a name without a prefix, so `MCP send ` is a deviation.

**Context propagation works:** in the measurement the server span became a child of the client
span within one trace id. If there is no context, the span attaches to the current ambient span
rather than creating an orphan.

> **This SDK emits not a single metric.** A grep over the wheel for `get_meter` and `create_histogram`
> gives zero matches. The four metrics defined in the convention are, today, on paper. Everything
> you build, you will build **from spans**.

**For those on stdio:** logs only to `stderr`. Stdout is occupied by the protocol itself, any
`print` into it breaks the JSON-RPC stream.

---

## 3. What to measure

There are deliberately no numeric thresholds on this slide, see section 7.

| Metric | What it shows | Breakdown | What to look at |
|---|---|---|---|
| Share of successful `tools/call` | health of the tool contract | by tool name | a sustained drop, not an instantaneous failure |
| **`error.type = tool_error`** | **the main error line**: wrong argument, a tool that crashed, a broken external dependency | by tool name | growth on one tool is an external dependency, growth across all is the model or the schema |
| **`rpc.response.status_code = -32602`** | **the second, independent line**: envelope and addressing errors, resource not found, a request not matching the schema | by method | means "the client is talking to the server wrongly", not "the model is confused about arguments" |
| Server-side latency | speed of the server itself | by method, percentiles | the mean hides the tail, look at p95 and p99 |
| Client-side latency | what the agent feels, network plus server | by method | the gap between client and server latency is your transport |
| RPS by method | load profile | by method | a spike in `tools/list` means the client polls instead of using the cache |
| Repeats of one call in a trace | the signature of a retry storm | by the pair "name plus argument hash" | counted within one `trace_id` |
| Tokens per step | the price of the agent's work around the tool | by trace | **counted on the neighboring LLM spans, not on the tool span** |
| Tool response size | risk of truncation and auto-compaction | by tool | approaching the client's limit |
| Share of authorization denials | security and broken clients | by client | a spike on one client is brute-forcing or a stale token |
| Tool selection share | language drift of the description | by tool | a drop after a `description` change, see the [versioning guide](versioning.md) |

The first seven rows are collected by the standard instrumentation without a single line of your
own code. The last four require your own attributes: they are not in the standard.

### Three things that are usually done wrong

**One SLO for all methods is garbage.** `tools/list` and a heavy `tools/call` have different
distributions. You have to slice by method, and within calls also by tool name.

**You have two independent error lines, not one.** This is the place where almost every dashboard
goes wrong.

The code `-32602` in the new revision is responsible for envelope and addressing errors: the wrong
protocol in `_meta`, a request not matching the schema, a resource not found. Errors in the content
of a call, that is, a wrong argument or a tool that crashed, do not land here at all: the
specification explicitly tells you to return them as a successful JSON-RPC response with an error
flag, so that the model can correct itself ("Clients **SHOULD** provide tool execution errors to
language models to enable self-correction"). In telemetry that is `error.type` with the value
`tool_error`.

Measurement of seven scenarios on a live server:

| Scenario | `error.type` | `rpc.response.status_code` | Span status |
|---|---|---|---|
| `tools/call` with valid arguments | not set | not set | UNSET |
| `tools/call`, argument of the wrong type | `tool_error` | not set | ERROR |
| `tools/call`, required argument missing | `tool_error` | not set | ERROR |
| `tools/call` of a nonexistent tool | `tool_error` | not set | ERROR |
| `tools/call`, the tool threw an exception | `tool_error` | not set | ERROR |
| `resources/read` of a nonexistent resource | **`-32602`** | **`-32602`** | ERROR |
| a request without envelope keys in `_meta` | **`-32602`** | **`-32602`** | ERROR |

The last row is the new role of the code that appeared together with statelessness: the base
section of the specification requires rejecting a request without
`io.modelcontextprotocol/protocolVersion` and `clientCapabilities` with code `-32602` and HTTP 400.

**The practical conclusion: you hang the alert on `tool_error` broken down by tool, and you read
`-32602` as "the client is talking to the server wrongly".** One of seven versus six of seven.

> Warning: **the SDK diverges from the specification on one scenario.** The specification puts an unknown
> tool under Protocol Errors, while `mcp` 2.0.0 returns `tool_error`: `ToolError` inherits from
> `MCPServerError`, not from `MCPError`, and settles in the result. A protocol error is raised only
> by an explicit `MCPError`.

**A tool execution span does not spend tokens by itself.** Tokens are spent by the model calls
around it: the one that decided to call the tool and the one that read the result. If you hang a
token counter on the tool span, you will get zero and decide the server is free.

### What is not in the standard and what you add yourself

| What is missing | Why it is your concern | Where to put it |
|---|---|---|
| **The metrics as such** | the convention defines them, but the SDK produces none | compute it yourself from spans on the backend side |
| Tokens | the standard covers the protocol, not the model calls around it | your own attributes on the trace's LLM spans |
| Cost in money | a computed quantity, the specification has no exchange rate or price list | compute at ingest, freeze on the leaf span, sum up through the parent |
| Tenant, feature, agent version | needed for cost attribution and multi-tenant breakdowns | tags on the root span, deeper via `baggage` through the same `_meta` |
| Tool response size | the protocol does not measure it, and it determines truncation | your own attribute on the server output |
| Quality of the error contract | a metric about your code, not about the protocol | share of errors without a machine-readable class |
| Network attributes and addresses | the convention describes them, the SDK does not set them | by hand, if you need a breakdown by clients |
| Service resource attributes | without them your traces are indistinguishable from others' in a shared backend | the standard OTel mechanism, configured by hand |

> Warning: **Two rules that break the system if you do not know them.** High-cardinality identifiers
> (user, session, resource URI) do not go into metric labels: the time series explodes, and
> attribution by user lives in traces and logs. And no raw emails or personal identifiers: a hash
> groups costs without dragging personal data into the observability system, from where it cannot
> be purged by retention.

---

## 4. The error contract as a telemetry breakdown

An error from your server is an interface for two parties at once: for the model, which decides
what to do next, and for telemetry, which has to break an incident down into classes.

A message like `Something went wrong` breaks both at the same time. The model does not understand
what to do and repeats the call with the same arguments, and since resumability is removed, a
repeat is indistinguishable to the server from a new call. This is a retry storm, and it comes
from your code. At the same time, in telemetry all incidents collapse into one class, and there is
nothing to build breakdowns from.

**Layering:**

- a low-cardinality class goes into an **attribute**;
- a human-readable explanation with an action plan goes into the **error text** and from there
  into the span status description;
- specific values and limits go into the **model's response body** and do not reach telemetry.

An example of a good message: not `error`, but "budget exceeded, current total 4500, limit 4000,
reduce the order".

**The metric that catches the storm:** the number of spans with the same pair "tool name plus
argument hash" within one trace. A hash, not the arguments: grouping is there, and we do not store
the content.

Full taxonomy of failure classes and the fields of a structured error: [tool design
guide](tool-design.md).

---

## 5. Idempotency: a consequence of removed resumability

The verbatim wording of the consequence:

> "Resumability is gone. No `Last-Event-ID`, no SSE event IDs. A broken response stream loses the
> in-flight request, and the client must re-issue it as a new request with a new request ID.
> **Every non-idempotent tool now needs a server-side idempotency key that it did not need before,
> because the client's retry is indistinguishable from a fresh call.**"

**Four independent sources of retries add up.** The model retries on a tool error, the tool
wrapper retries on a transient HTTP error, the orchestrator retries the whole turn on a timeout,
the provider retries internally. Four stacks on top of a non-idempotent write is self-sabotage.

| Bucket | Examples | Strategy |
|---|---|---|
| Naturally idempotent reads | `get_customer`, `check_order_status`, search | Retry freely, no key needed |
| Writes with a side effect | charge a payment, book, send an email, create a ticket | An idempotency key is mandatory on every retry layer |
| Long operations | report generation, bulk export | A key on the trigger **plus** a separate status endpoint |

### Where the key is born

This is the place where the pattern breaks most often.

- The key is **not** generated inside the tool. `uuid4()` on every call means a new key on every
  retry and completely kills the mechanism.
- The key does **not** contain timestamps or random values.
- The key is born in the calling code **before** the side effect and is **persisted into the agent's
  state** before the call.
- Ingredients: the tool call identifier, the conversation identifier, the tool name, a hash of the
  serialized arguments. It is hashed.
- Scope: the key covers an operation with an external side effect. "Key the charge, not the thought that
  led to it."

> **An open dispute about the key's anchor.** Some sources propose the tool call identifier as a
> natural anchor. The objection: "Streaming responses occasionally yield the same
> `tool_call_id` twice during compaction; treat `tool_call_id` as a useful *signal* but not as the
> idempotency key itself: **the model can synthesise new ids on retry**". A compromise that works
> for both sides: a composite key `hash(session_id, tool_name, canonicalized_args)`,
> persisted before the call.

**If the underlying API does not support keys:** a deduplication table written **in the same
transaction as the side effect**. A unique constraint on the key column is a backstop: if two
retries race and both passed the `SELECT`, the second `INSERT` fails on the constraint, is caught,
and the winner's row is read. **The arbiter is the database, not the application code.**

In the MCP schema you will have to accept the key as an explicit field and declare the behavior in
the description:

```json
{
  "name": "send_slack_message",
  "description": "Send a message. Idempotent on idempotency_key; server dedupes within 5 min.",
  "inputSchema": {
    "type": "object",
    "required": ["channel", "text", "idempotency_key"]
  }
}
```

---

## 6. Telemetry conventions lag the protocol by one revision

This is the freshest part of the file and something you will not find in overviews: the
cross-check was done by hand on 02.08.2026.

The OpenTelemetry semantic conventions for MCP exist and are fairly detailed. It is just that they
describe the 2025 version of the protocol.

- The session identifier attribute is marked as recommended and refers to revision `2025-06-18`.
  There are no sessions in the protocol.
- **Two of the four metrics measure session duration**, and they do not even have a method name:
  eight and six attributes.
- In the list of **twenty-five** methods, **seven are dead**: `initialize`,
  `notifications/initialized`, `ping`, `logging/setLevel`, `notifications/roots/list_changed`
  and both resource subscriptions.
- Two are missing: **`server/discover`**, which the server is required to implement, and
  `subscriptions/listen`.

**This is for the long term.** The conventions repository has 41 open pull requests, and not one
about the July 28 revision, about statelessness, about `discover` or about subscriptions. The
closest in meaning is the question "what does the server session duration metric actually
measure", opened on **27.01.2026**: the last activity in it was 16.06.2026, and there is still no
answer.

An illustration that is visible on the very first request: the first server span to arrive is
`server/discover`, because the SDK implements it. The convention's vocabulary does not have this
method, so there is no place for it in a dashboard built by the convention. The discrepancy is
visible on the first span of the first request.

**What to do about it:** take the mechanics, verify the lists against your revision, do not build
a dashboard on the two session metrics.

### Warning: the conventions address changed, and the old one silently serves a stub

| Address | What it serves as of 02.08.2026 |
|---|---|
| `opentelemetry.io/docs/specs/semconv/gen-ai/mcp/` | a stub "GenAI semantic conventions have moved… no longer maintained in this repository" |
| `raw.githubusercontent.com/open-telemetry/semantic-conventions/main/docs/gen-ai/mcp.md` | the same stub. The move was done in PR #3696 of 05.05.2026 |
| **`raw.githubusercontent.com/open-telemetry/semantic-conventions-genai/main/docs/gen-ai/mcp.md`** | **the full document. The working address** |

A dead address is doubly unpleasant: **it is exactly the one that the MCP `2026-07-28`
specification links to**.

**And this document currently has no version.** In the `semantic-conventions-genai` repository not
a single release has been published, the conventions exist only as the main branch. So they can be
cited only with an access date, not with a version number, and there is nothing to pin to. It is
worth knowing this **before** building a dashboard on the "standard".

Separately: the MCP section was merged into the main semantic conventions repository on
12.01.2026 and shipped in a release the same day. The references to versions v1.40, v1.41 and
v1.43 inside the document are pins to **other** documents, not the version of the MCP section.

### An open question that will be asked first

**What to replace the session identifier with as the correlation key for audit.** Neither the
protocol nor the conventions have an answer. An honest substitute is the authenticated subject
from the token plus the trace context, but that is your work.

---

## 7. Starting threshold guidelines, to be calibrated for your stack

> Warning: **Not a single number in this table rests on a measurement.** These are working
> heuristics taken from other people's practice: not an industry norm, not a specification
> requirement and not the result of a measurement. Eight of the nine rows went through checking
> and did not get a primary source. The ninth (token spend) rests on a press report quoting a
> consultant, that is, on a retelling, not on a measurement. Take them as a starting point: after
> two weeks of your own data you will set different ones.

| What | Starting guideline | What to calibrate |
|---|---|---|
| Share of successful tool calls | more than 98% | the distribution depends on how many external dependencies you have |
| Reaction threshold for tool errors | more than 20% per method, sustained for 5 minutes | heavy tools are noisier than light ones |
| Hold window for a deviation before alerting | 5-10 minutes | the shorter the window, the more false positives and learned helplessness of the on-call |
| Money looping signature | run cost above 5× the rolling median of this route | a static daily limit fires late, the anomaly earlier |
| Token investigation threshold | a sustained fourfold growth in spend per typical operation | a one-off spike does not count, persistence is needed |
| Prompt inflation | share of calls finishing by length above 5% | next come truncated answers and parsing failures |
| Price of a cache read | about 10% of the base price of input tokens | **the only number in the table that is cheap to close:** verified in a minute against your provider's public price list |
| Where to look for burners | the P95 and P99 tail by trace cost | the rule "a small share of requests produces the main part of the spend" |
| Scale of the disaster without limits | a token spend of the order of $500 million per month was publicly reported | a press report quoting a consultant, the company is not named. An order of magnitude, not a case |

---

## 8. What to write to the log and what not to

**Write:** trace and span identifiers, method, tool name, request identifier, protocol version,
transport, client identity, tenant, latency, number of retries, error class and response code,
response size, a **hash** of the arguments.

**Do not write by default:** arguments and results in full, secrets in any form, personal data
without masking **before** it reaches storage, resource URIs in span names.

**About opt-in, precisely.** The three attributes with a payload (`gen_ai.tool.call.arguments`,
`gen_ai.tool.call.result`, `gen_ai.prompt.variable`) are a property of **spans**: all three are
Opt-In, each carries the warning "This attribute may contain sensitive information". Metrics have
a different set: there only `gen_ai.prompt.variable` and `mcp.resource.uri` are opt-in, and the
tool arguments and result are absent altogether, that is, they do not reach metrics under any
settings.

> **An open fork, yours to decide.** The conventions keep the payload opt-in with a direct
> warning. The practical position is the opposite: without raw arguments and the raw response you
> can diagnose neither a parameter hallucination nor the case where the agent took a system API
> error for a valid answer. Both sides are right. Working options: a separate stream with masking
> and a short retention period, or hashes and sizes with the content recorded only while
> reproducing an incident.

**A separate circuit for mutating tools.** A trace lives for weeks and is sampled. An audit log
lives for the regulatory period and is never sampled. For tools that write, send emails or move
money, you need a second, immutable one.

---

## 9. Limits of the method

A note without which the section would be dishonest.

**A green dashboard is compatible with an unsolved task.** All four standard metrics measure the
speed and liveness of the protocol. None measures whether the agent solved the task. A fully green
MCP dashboard is perfectly compatible with a product that does not work: the agent answers,
does not crash, answers quickly and does not solve the task.

**Why the model chose a tool, no telemetry will show.** You can log which tool was chosen and with
what arguments. The reason for the choice cannot be established, nor reproducibly influenced. This
is a limit of the method, not a gap in the tooling.

**What lies nearby but is not this topic:**

- **MCP Inspector** is debugging at development time: you connect by hand to one server, it
  aggregates nothing, and it does not work after deployment.
- **Built-in Evaluations in low-code** are offline quality control of a flow before rollout, not
  runtime telemetry. The level of detail there is only the whole process at once.
- **A dashboard for connector developers** from the client's vendor (adoption, health, error
  share, public beta since 08.06.2026) shows the behavior of your connector **inside someone
  else's ecosystem**. It does not replace your own instrumentation.

---

## 10. What to check before applying

- **The conventions address.** It changed on 05.05.2026, the old one silently serves a stub, and
  the specification still links to it. Work with the `semantic-conventions-genai` repository.
- **The conventions have no version.** The main branch may change between your check and prod.
  Record the access date.
- **Open issue #313 and PR #404** in the conventions repository. If the PR is merged, the alert
  logic based on span status will change.
- **`mcp/server/_otel.py` is marked provisional.** The import has an underscore, the path may
  change.
- **The moment of cost calculation** is an open dispute: compute at ingest and freeze (then
  historical margin is not rewritten by a price change) or compute at query time (then history
  can be recalculated if there was an error in the rates). Decide before data accumulates.

Full list of primary sources with links and dates: [reading-list.md](../reading-list.md).

---

## Appendix. How to hand this file to an agent

```
Read observability.md in full. Set up observability for an MCP server for <domain>.

Work by the guide:
1. Build an end-to-end trace per section 1: where the context travels, how parenthood is set,
   what to do on stdio. Show exactly what needs to be added in my code.
2. Per section 2, separate what the SDK gives by itself and what I count by hand. The SDK does
   not emit metrics — write them yourself.
3. Set up the basic trio of metrics with the breakdowns from section 3 and a panel for the gap
   between server and client latency.
4. Formulate SLOs per section 3: separate thresholds by method classes, not one common one.
5. Describe what to write to the log and what not to, per section 8.
6. Run the result against the checklist of section 10 and show the unclosed items.

Rules: the thresholds in section 7 are starting guidelines without a primary source, present them
as guidelines and suggest what to calibrate them with. None of these metrics answers
whether the agent solved the user's task: do not pass them off as a quality metric.
```

The same file works as a review prompt: "read the guide, look at my dashboard and tell me which
of the listed breakdowns I am missing".

---

## Links mentioned in the session

Collected from the screens of this block: what I relied on out loud and what is worth opening yourself. The links are live as of the date the materials were compiled.

| What it is | Link |
|---|---|
| Registry of deprecated capabilities of the revision | [https://modelcontextprotocol.io/specification/2026-07-28/deprecated](https://modelcontextprotocol.io/specification/2026-07-28/deprecated) |
| OpenTelemetry conventions for MCP (current address) | [https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/mcp.md](https://github.com/open-telemetry/semantic-conventions-genai/blob/main/docs/gen-ai/mcp.md) |
| Conventions model: spans.yaml, metrics.yaml, registry.yaml | [https://github.com/open-telemetry/semantic-conventions-genai/tree/main/model/mcp](https://github.com/open-telemetry/semantic-conventions-genai/tree/main/model/mcp) |
| Python SDK: the OpenTelemetry page | [https://py.sdk.modelcontextprotocol.io/run/opentelemetry/](https://py.sdk.modelcontextprotocol.io/run/opentelemetry/) |
| MCP specification: Resources, the move of the "resource not found" error | [https://modelcontextprotocol.io/specification/2026-07-28/server/resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources) |
| W3C Trace Context: the traceparent and tracestate format | [https://www.w3.org/TR/trace-context/](https://www.w3.org/TR/trace-context/) |
| Connector observability, public beta status | [https://claude.com/blog/observability-for-developers-building-connectors](https://claude.com/blog/observability-for-developers-building-connectors) |
| Production deployment checklist, 16 items | [https://modelcontextprotocol.io/specification/2026-07-28/basic/transports](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports) |
| MCP Inspector: repository and command-line mode | [https://github.com/modelcontextprotocol/inspector](https://github.com/modelcontextprotocol/inspector) |
| mcp-remote: the direction of the bridge | [https://github.com/geelen/mcp-remote](https://github.com/geelen/mcp-remote) |
| MCP specification, revision changelog | [https://modelcontextprotocol.io/specification/2026-07-28/changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog) |
| MCP specification, base protocol, revision 2026-07-28 | [https://modelcontextprotocol.io/specification/2026-07-28/basic](https://modelcontextprotocol.io/specification/2026-07-28/basic) |
| MCP specification, Tools, revision 2026-07-28 | [https://modelcontextprotocol.io/specification/2026-07-28/server/tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) |
| Issue #314, the `semantic-conventions-genai` repository | [https://github.com/open-telemetry/semantic-conventions-genai/issues](https://github.com/open-telemetry/semantic-conventions-genai/issues) |
