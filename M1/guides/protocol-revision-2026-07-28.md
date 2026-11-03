# Protocol revision 2026-07-28: what changed and how to migrate

> Compiled 02.08.2026. All primary sources were opened and checked on 01–02.08.2026.
> The revision came out on July 28. Almost everything a search engine returns for the word MCP was written before it.

## Why this file

This is the fifth revision of the protocol and, in the maintainers' words, "the largest revision of the protocol
since launch". The problem is not the revision itself but its age: the body of texts about MCP, including search
engine caches, tutorials and ready-made notebooks, describes the pre-revision model. You can check it
in a minute: the cached copy of the versioning page says "The current protocol version is
2025-11-25", while a live request to the same address returns `2026-07-28`.

The file answers two questions. What of what has already been written is no longer true. And what of the new
material cannot be obtained by updating a dependency.

---

## 1. There are no more sessions

This is not an optimization but a change of model. Removed:

- the `initialize` and `initialized` methods (SEP-2575);
- the `Mcp-Session-Id` header (SEP-2567);
- the standalone GET stream and resumability via `Last-Event-ID` (SEP-2575).

The protocol version and client capabilities now travel in the `_meta` of **every** request, under the key
`io.modelcontextprotocol/protocolVersion`. The wording of the specification: "This implies that an open
connection, such as a STDIO process, is not a conversation or session". You may keep a process open,
but you may not treat it as a conversation.

**Why this was done.** Session-based servers live poorly behind a load balancer and leak memory if
sessions are not cleaned up. In the new model any instance anywhere can serve any request, and the server
can be put on serverless and edge without the plumbing of sticky sessions.

**And an admission after the fact.** SEP-2567 describes the old model verbatim: "Possession is not
authorization". It also names a specific implementation: the session manager of the official Python SDK
routed by `Mcp-Session-Id` without checking that the authenticated identity on the request matched
the one that created the session. A leaked identifier meant session hijacking by any other
authenticated principal. Removing sessions here is not a loss but a fix.

> **Do not confuse this with deprecation.** The twelve-month window discussed in section 6 covers
> Roots, Sampling, protocol Logging and dynamic client registration. Sessions are not
> deprecated, they are **removed**. There is no transition window.

**What to do with your own cross-call state.** Anything that has to outlive a request is bound
to an explicit identifier (a state handle) that the client passes on every call. The specification
describes this section as non-normative, but requires validating authorization against the handle on
every call: owning a handle is not by itself authentication.

---

## 2. Three things you will not get from an SDK update

Each requires changes in your handlers, not a dependency bump.

| What | Norm | Details |
|---|---|---|
| `server/discover` | "Servers **MUST** implement it" | The client may skip it and send a working request right away. The server has no such choice |
| `resultType` in every result | required | Values `complete` and `input_required`. The client must treat a missing field as `complete` |
| `ttlMs` and `cacheScope` | required on six operations | Not five: the sixth is `server/discover` itself. Only for results with `resultType: complete` |

**The `resultType` trap.** A third value, `task`, is brought by the Tasks extension. A client that
strictly parses two values breaks on such a server.

**Full form of the `server/discover` response:**

```json
{"jsonrpc":"2.0","id":"discover-1","result":{
  "resultType":"complete",
  "supportedVersions":["2026-07-28"],
  "capabilities":{"tools":{},"resources":{}},
  "_meta":{"io.modelcontextprotocol/serverInfo":{"name":"ExampleServer","version":"1.0.0"}},
  "instructions":"This server provides weather and resource utilities.",
  "ttlMs":3600000,"cacheScope":"public"}}
```

Two non-obvious things in this response.

`serverInfo` lives **in the result's `_meta`, not in the body** of `DiscoverResult`. This is a late change
to the specification (PR #3002), made after the release candidate, and SDKs built against the pre-#3002 form broke
the connection in both directions.

The specification itself declares `serverInfo` self-reported and unverifiable: clients SHOULD NOT
rely on it in security decisions.

Separately, on the `instructions` field: this is text that the client puts into the model's system prompt.
In other words, the server gained a second channel of text straight into the model's context, besides tool
descriptions. The consequences for manifest pinning are covered in the
[security guide](security-and-authorization.md).

---

## 3. Requests to the client now go only through MRTR

Server-initiated requests are banned entirely. Verbatim:

> "Servers **MUST** send server-to-client requests (such as `roots/list`,
> `sampling/createMessage`, or `elicitation/create`) using the MRTR pattern. The previous pattern
> of server-initiated requests is no longer supported. This is a breaking change."

The mechanics in four steps:

| Step | Who | What |
|---|---|---|
| 1 | client | `tools/call` |
| 2 | server | `input_required` result, with the data request and `requestState` inside |
| 3 | client | collects the answer from a human, **repeats the original call** with the answers and the same `requestState`; the JSON-RPC `id` must be different |
| 4 | server | restores the state, performs the action |

Allowed on exactly three methods: `prompts/get`, `resources/read`, `tools/call`. On any other
"Servers **MUST NOT** send `InputRequiredResult` responses on any other client requests".

The server **MUST NOT** assume that the client will execute the request and come back at all.

The integrity requirements for `requestState` (this is one of the strictest wordings in the whole
specification) are covered in the [security guide](security-and-authorization.md).

Separately: elicitation is **not** deprecated, it is simply delivered through MRTR now. Half of the
overviews confuse this.

---

## 4. Headers and error codes: the layer that fails silently

### Three required headers on POST

| Header | When required | Note |
|---|---|---|
| `MCP-Protocol-Version` | always | the value MUST match the request's `_meta` |
| `Mcp-Method` | always | the method name |
| `Mcp-Name` | on `tools/call`, `resources/read`, `prompts/get` | non-ASCII is encoded with the sentinel `=?base64?{...}?=` |

Verbatim: "These headers are **REQUIRED** for compliance". A header that does not match the body is
HTTP 400 and code `-32020`.

For legacy traffic: respond 405 to GET and DELETE, and ignore `Mcp-Session-Id` and `Last-Event-ID`.
The level here is **SHOULD, not MUST**, and the scope is narrow: this is how the specification advises a server
that supports only this revision to respond.

> **The infrastructure landmine that costs more than everything else listed.** A WAF, reverse proxy
> or firewall rule that strips unknown `Mcp-*` headers fails every request, and from the outside it
> looks like a client bug. Before migrating, walk the whole request path: CDN, WAF, proxy,
> load balancer.

### Error codes

| Code | Name | When |
|---|---|---|
| `-32020` | `HeaderMismatch` | a header did not match the body, together with HTTP 400 |
| `-32021` | `MissingRequiredClientCapability` | the server needs a capability the client did not declare; `data` lists the missing ones |
| `-32022` | `UnsupportedProtocolVersion` | `data.supported` lists the versions the server supports |
| `-32602` | Invalid params | resource-not-found moved here from `-32002` (SEP-2164). Clients SHOULD keep accepting `-32002` from old servers |
| `-32000..-32019` | legacy range | allocating new codes there is **MUST NOT** |
| `-32020..-32099` | reserved for the specification | inventing your own codes there is **MUST NOT** |

A detail that explains discrepancies in other people's materials: the codes were renumbered during the development
of the revision itself (`-32001`→`-32020`, `-32003`→`-32021`, `-32004`→`-32022`). Everything written from the draft
names the old values.

The move of resource-not-found from `-32002` to `-32602` is exactly where the tests of homemade clients silently
fail. Grep your code for hardcoded values.

---

## 5. What else was removed and what became required

| Removed | SEP | Became required | SEP |
|---|---|---|---|
| `initialize` and `initialized` | 2575 | `server/discover` | 2575 |
| The `Mcp-Session-Id` header | 2567 | `resultType` in all results | 2549 |
| Standalone GET stream and resumability via `Last-Event-ID` | 2575 | `ttlMs` and `cacheScope` on six operations | 2549 |
| `ping`, `logging/setLevel`, `notifications/roots/list_changed` | 2577, 2575 | `Mcp-Method` and `Mcp-Name` on POST | 2243 |
| Server-initiated requests | 2322 | Deterministic `tools/list` order (SHOULD) | 2549 |
| `tasks/list` | 2663 | JSON Schema 2020-12 in tool schemas | 2106 |

Two consequences that are usually noticed a week after the migration.

**`tasks/list` was removed together with sessions.** If an agent crashed in the middle of polling and did not save
the task ID, the work is orphaned: it is being computed, it is being billed, and nobody will pick up the result.

**SSE resumability was removed, so idempotency became mandatory.** A broken response is considered
lost, the client resends the request under a new identifier, and its retry is indistinguishable from a fresh
call. Every mutating tool needs an idempotency key, which was not required before. Details in the
[versioning guide](versioning.md).

**The `notifications/tools/list_changed` notification changed its mechanics.** It goes out only to those
clients that opened a `subscriptions/listen` stream with the corresponding flag, and the level there is
SHOULD, not MUST. All public guides written before the release describe the previous separate stream.

---

## 6. Deprecations: the only part of the revision with a calendar

| Feature | SEP | Marked | Migration | Earliest removal |
|---|---|---|---|---|
| Roots | 2577 | 2026-07-28 | tool parameters, resource URIs, server config | the first revision on or after **2027-07-28** |
| Sampling | 2577 | 2026-07-28 | a direct call to the LLM provider's API | same |
| Protocol Logging | 2577 | 2026-07-28 | `stderr` on stdio, OpenTelemetry | same |
| Dynamic client registration (DCR, RFC 7591) | PR #2858 | 2026-07-28 | CIMD (client metadata documents) | same |
| HTTP+SSE | 2596 | 2025-03-26 | Streamable HTTP | **disputed, see below** |

Window rules that are usually told incorrectly:

1. **The window is counted from the release** of the revision in which the feature is first marked Deprecated,
   not from the date the SEP reached Final. Verbatim: "measured from the release of the specification
   revision in which the feature is first marked Deprecated, not from the date the SEP reaches
   Final".
2. A minimum of twelve months. Shortening is allowed only for an active risk with a published advisory,
   and even then not below ninety days.
3. **So far zero features have been removed under this policy.** The Removed section of the registry is empty:
   "No features have been removed under this policy yet".
4. Eligibility for removal is not removal. Eligible for removal and removed are different states.

**The reason sampling was deprecated is not security.** According to SEP-2577 the selection criterion is the weakest
ratio of adoption to implementation complexity. Security comes as a side effect.

> ### An open discrepancy inside a single primary source
>
> The deprecation window for HTTP+SSE is stated with two different time frames on the same domain. The registry of deprecated
> features: "Three months after SEP-2596 reaches Final". The release blog: "with a year-long
> offramp". Both quotes are verbatim.
>
> Resolving it without picking a winner: the registry itself says it is "a derived view kept consistent with
> the per-feature deprecation notices and changelog entries, **which are the normative records**".
> That is, the three-month period is normative, and the "year" is the blog's wording, which looks like a carry-over
> of the twelve-month default from the neighboring paragraph.
>
> The practical conclusion is wider than one time frame: **check a feature's status in the registry, not in the blog.**

> ### A second open discrepancy: the status of the Tasks extension
>
> Overviews call it official. Meanwhile the extension's page links to a repository with the
> prefix `experimental-ext-`, which by the organization's own rules means experimental
> status. Tasks is absent from the extensions matrix entirely. It looks like documentation
> out of sync, and there is nothing to verify it with. Treat the question as open.

---

## 7. Era compatibility and rollout order

Modern is `2026-07-28` and later, Legacy is `2025-11-25` and earlier. **Era is a property of the server,
not of the request.**

| Client | Server | Result |
|---|---|---|
| Modern | Modern | works |
| Modern | Legacy | **fails**. The worst variant: the server silently handles an era-ambiguous method with legacy semantics, and from the outside it looks like success |
| Dual-era | Modern | works |
| Dual-era | Legacy | works, falls back to `initialize` |
| Legacy | Modern | **fails**, a legacy client has no fall-forward mechanism |
| Legacy | Dual-era | works |

Detecting a legacy server and adapting is something **only a dual-era client** can do. For a pure
modern client the corresponding row of the matrix reads "Fails". On stdio there is no HTTP status
that shows the era, so a dual-era client SHOULD send `server/discover` first.

**Hence the rollout order rule: dual-era first, always.** The asymmetry here determines not
the architecture but the sequence of actions. An old client has no way to detect a
modern-only server and adapt, it simply fails. Switching straight to modern-only breaks all
pinned internal clients at once, that is, the ones you control least.
The legacy branch is removed when telemetry has shown zero legacy connections over a full cycle,
not when the calendar says it is time.

---

## 8. Checklist for migrating your own server

1. Implement `server/discover`.
2. Read the protocol version and client capabilities from the `_meta` of every request.
3. Stop issuing session identifiers, respond 405 to GET and DELETE.
4. Validate the three required headers against the request body.
5. Move cross-call state into explicit handles with a TTL and binding to the authenticated
   user on your side.
6. Replace server-initiated requests with `InputRequiredResult` and a repeated call.
7. Add `ttlMs` and `cacheScope` on the six operations. A permission-filtered `tools/list`
   must be `private`, see the [multi-tenancy guide](multi-tenancy.md).
8. Replace `-32002` with `-32602`, grep the code for hardcoded error code values.
9. Make a decision on dual-era and record it in the server's README.
10. Walk the whole request path looking for stripping of `Mcp-*` headers: CDN, WAF, proxy, load balancer.
11. Add an idempotency key to every mutating tool.
12. Check that token validation is called in every handler, not once at
    connection time (there is nothing left to hook onto at connection time).

---

## 9. SDK versions as of 01.08.2026

| Package | Version | What matters |
|---|---|---|
| `mcp` (PyPI) | **2.0.0**, 28.07 13:45:28Z | `1.29.0` came out at 13:41:40Z, less than four minutes earlier. The head of the v1 line is `1.29.0`, and the pin `mcp>=1.28,<2` will pull exactly that |
| `mcp-types` | 2.0.0 | `mcp.types` remained as a permanent alias, old imports do not break |
| `fastmcp` (standalone) | **3.4.5** (27.07), beta `4.0.0b1` (28.07) | the 4.0 line has been in alphas since 21.07. The sessionless revision is carried by the beta |
| `@modelcontextprotocol/sdk` (npm) | **1.30.0**, 27.07 | there are no other dist-tags at all. The second line moved to nine new package names |
| TypeScript SDK v2 | 2.0.0, nine packages | published in a single salvo within 6 seconds. Among them is a `codemod` for the v1 → v2 migration |
| Inspector | 2.0.0 (`v1-latest` = 1.0.1, `next` = 2.0.0-rc.3) | |

Two facts from the Python v2 release: the Tasks extension (SEP-2663) was **not included** in 2.0.0; the request body
limit is 4 MiB by default, configurable via `max_body_size`, and anything above it is HTTP 413.

A trap for those who just updated the package: in TypeScript SDK v2 the authorization requirements are implemented
as an **SDK-level opt-in**, verbatim "they apply on every era once enabled". Updating the dependency
does not by itself give you conformance.

The version forks across both ecosystems are covered in the starter READMEs:
[Python](../starter-server/python/README.md), [TypeScript](../starter-server/typescript/README.md).

---

## 10. Ecosystem readiness on the measurement date

A census dated 22.07.2026 of all servers in the official registry that could be reached
with a conformant keyless request. The denominator is **4,937** servers (out of 18,032 registered).
The tool is MIT-licensed, the JSONL dataset is CC BY, and each row is reproducible with one command.

| Number | What it means |
|---|---|
| **0** | servers are ready on all four required signals |
| **4,225 (85.6%)** | require migration |
| **805 (16.3%)** | still issue `Mcp-Session-Id`, of which **528** are hard-wired to it |
| **37 / 39 / 40** | implement `server/discover` · hold the routing headers · are one condition away from ready |
| **81.2% (4,010)** | already carry calls without a handshake |

**The zero has to be read correctly here, otherwise the figure is dishonest.** It comes from the requirement to pass
all four signals at once: `server/discover`, calls without a handshake, session independence,
enforcement of the routing headers. On the main one of them the ecosystem is already at 81.2%. The authors of the measurement
write themselves: "The ecosystem is closer to the stateless core than the zero suggests".

**A second mandatory clarification.** There is an independent measurement made the same way ten days earlier
(12.07.2026, 4,356 servers, three signals out of four). It found **one** ready server, not zero,
and five servers demonstrably speaking `2026-07-28`.

A formulation you can take away: two independent tools that diverged by ten days
give the same order of magnitude. Out of more than four thousand publicly reachable servers, **zero or one** are ready.
And both measurements were made against a ruleset marked release candidate: neither has a recheck against
the final text of the specification as of 01.08.2026.

---

## 11. What the revision gives for the future

Three mechanisms introduced by the same revision turn "trust in the vendor" into verifiable
commitments.

- **A lifecycle policy** with an earliest-removal date on a single page.
- **An extensions framework**: experimental things live separately from the normative core.
- **A conformance suite** (SEP-2484): without a scenario in it, a Standards Track SEP does not reach Final.
  The same suite tiers SDKs: Tier 1 requires a 100% pass rate, Tier 2 requires 80%, relegation if
  even one test fails for four weeks in a row. The denominator is narrow: applicable required tests,
  excluding pending, skipped, experimental and `disputed`. The tests apply from 23.01.2026,
  tiering from 23.02.2026.

The maintainers write directly: "This release contains breaking changes. We don't intend for that to be
the norm". Indirect support for the same: the draft revision has accumulated zero changes since 28.07.

---

## 12. What to check before applying this

The specification is dated by revision, while SDK and vendor pages are not dated at all. SDK versions
and ecosystem figures go stale fastest.

- **Whether a readiness recheck against the final text has appeared.** Both measurements were made against a
  ruleset marked `-rc`. If a recheck has come out, the "zero" figure may have changed.
- **SDK versions.** Both ecosystems released major versions a day before and on the day of the revision's release,
  and the lines are live.
- **Page addresses.** The authorization section in this revision is split into four pages, and links to
  the old single-page anchor break.

The full list of primary sources with links and dates: [reading-list.md](../reading-list.md).

---

## Revision change checklist: what the server does

Eleven places the revision touched in server code. If you are writing a server from scratch this week, read this as requirements for the first version, not as a migration: there will be nothing to redo. If the server is already up, this is the list of changes.

### server/discover: the server MUST implement it
> The client may skip it and send a request right away, the server has no such choice at all

Verbatim: "Servers MUST implement it". The asymmetry is deliberate: the server must answer, the client may skip asking. A server without a discover response is formally non-conformant, even if in practice everything works with it.

Full form of the response:

{"jsonrpc":"2.0","id":"discover-1","result":{"resultType":"complete","supportedVersions":["2026-07-28"],"capabilities":{"tools":{},"resources":{}},"_meta":{"io.modelcontextprotocol/serverInfo":{"name":"ExampleServer","version":"1.0.0"}},"instructions":"This server provides weather and resource utilities.","ttlMs":3600000,"cacheScope":"public"}}

Field by field. supportedVersions is the list of revisions the server is ready to speak, and this is exactly where it is decided whether you are dual-era or modern-only. capabilities replace what used to be reported at the handshake. instructions is what the model will read before the first call.

Two non-obvious things about serverInfo. First: it lives in the result's _meta, not in the body of DiscoverResult; this is a late change to the specification after the release candidate, and SDKs built against the old form broke the connection in both directions. Second: the specification itself declares serverInfo self-reported and unverifiable, and clients SHOULD NOT rely on it in security decisions.

The SDK gives the basic skeleton of the response, you assemble the content.

### resultType in every result
> Complete or input_required, and a third value is brought by an extension and breaks clients

A missing field is read by the client as complete. The third value task is brought by the Tasks extension, and a client that strictly parses only two values breaks on a server with the extension.

On errors resultType is not returned: an error is a JSON-RPC error and has its own shape.

### ttlMs and cacheScope on six operations, not five
> And only for complete results: the sixth operation is usually lost in the enumerations

The sixth operation is server/discover itself, it is regularly lost in the enumerations. Results with a different resultType do not have these fields.

The semantics of ttlMs: a missing field is treated by clients as zero, that is, no caching. Clients SHOULD NOT treat the TTL as a polling interval; those who poll anyway MUST apply jitter and backoff.

If you do not return ttlMs at all, formally that is a non-conformance, in practice the client will take a conservative default and will not cache. That is, you will not break, you will pay for every list again.

The semantics of cacheScope public versus private is covered in the tenants block: there it gives a separate leak surface.

### _meta: protocol version and capabilities are required
> Client information is only SHOULD, and a missing required field is a rejection

Keys in the _meta of every request:

1. io.modelcontextprotocol/protocolVersion, string: required.
2. io.modelcontextprotocol/clientCapabilities, ClientCapabilities: required.
3. io.modelcontextprotocol/clientInfo, Implementation: not required, SHOULD.
4. io.modelcontextprotocol/logLevel, LoggingLevel: not required.
5. io.modelcontextprotocol/subscriptionId: only on subscription notifications.
6. traceparent, tracestate, baggage: an exception to the prefix rule, W3C Trace Context.

A missing required field is -32602 and HTTP 400. If the server needs a capability the client did not declare, the response is MissingRequiredClientCapabilityError, code -32021, with data.requiredCapabilities.

### Requests to the client are banned: MRTR only
> Only on three methods, MUST NOT on the rest, and elicitation is perfectly alive meanwhile

MRTR is multi-round tool response: instead of a request to the client the server responds with InputRequiredResult, and the client repeats the same call with the answers and necessarily with a different JSON-RPC id.

Verbatim: "Servers MUST send server-to-client requests (such as roots/list, sampling/createMessage, or elicitation/create) using the MRTR pattern". Allowed on exactly three methods: prompts/get, resources/read, tools/call. And separately: "Servers MUST NOT send InputRequiredResult responses on any other client requests".

This also clears up a common confusion: elicitation is not deprecated. It is alive, it is just delivered through MRTR, not as a separate request from the server.

### Three required headers on POST
> Verbatim REQUIRED for compliance, and a mismatch with the body is a rejection at the very entrance

MCP-Protocol-Version, Mcp-Method and, for the same three methods, Mcp-Name. Verbatim: "These headers are REQUIRED for compliance".

A header that does not match the request body is HTTP 400 and code -32020. Non-ASCII in a tool name is encoded with a sentinel of the form question mark, base64, content. At the same time the tool naming rule itself in the specification is SHOULD, not MUST, including length and uniqueness: the normative level here is lower than is usually told.

Why the headers appeared at all, the motive was publicly named by one of the large vendors: they let you read the values needed for logging and secret scanning without parsing the request body. Previously this required deep packet parsing on every request.

### -32002 became -32602, the range -32020..-32099 is taken
> Putting your own codes there is MUST NOT, and clients must keep accepting the old code

resource-not-found moved from -32002 to -32602. Clients are recommended to keep accepting the old code from old servers. This is exactly where the tests of homemade clients that hardcoded numbers silently go red.

New codes: -32020 HeaderMismatch, -32021 MissingRequiredClientCapability, -32022 UnsupportedProtocolVersion. The whole range -32020..-32099 is reserved for the specification.

A common misreading: -32602 does not come back on any malformed argument. The specification separates protocol errors from tool execution errors: invalid arguments are returned in the result with isError, not as a JSON-RPC error. On the current SDK -32602 comes back in exactly one scenario out of seven, when reading a nonexistent resource.

### GET and DELETE from an old client: respond 405
> The level here is SHOULD, not MUST, and the scope is narrow: only for a modern-only server

The Mcp-Session-Id and Last-Event-ID headers are ignored meanwhile. The scope is narrow: this is how the specification advises a server that supports only this revision to respond.

Here is a second case of a substituted level: "Servers SHOULD return tools in a deterministic order". A deterministic tools/list order is SHOULD, not MUST. The normative level is easy to substitute here, and I will not do that.

### Grep before the migration: twelve strings across the code
> Mcp-Session-Id, initialize, ping, Last-Event-ID and eight more strings to grep

The full list to grep: Mcp-Session-Id, sessionId, initialize, ping, logging/setLevel, resources/subscribe, roots/list, sampling/createMessage, tasks/list, tasks/result, Last-Event-ID, the literals -32001…-32004.

What was removed and what became required, in full, with SEP numbers:

1. initialize (2575) → server/discover, MUST (2575).
2. Mcp-Session-Id (2567) → resultType in all results (2549).
3. GET stream together with resumability via Last-Event-ID (2575) → ttlMs and cacheScope on 6 operations (2549).
4. ping and logging/setLevel (2577, 2575) → Mcp-Method and Mcp-Name on POST (2243).
5. Server requests (2322) → JSON Schema 2020-12 in schemas (2106).
6. tasks/list (2663) → tools/list order, SHOULD (2549).

The SEP numbers are given from the changelog, I did not verify each one individually: this is a pointer to where to look, not a guarantee.

One line about JSON Schema 2020-12: the dialect is full, and structuredContent is any JSON value, not necessarily an object. The analysis of the contract is in the tools block.

About subscriptions/listen: the method exists, but in homework week you will not make any decisions about it, so it stays here as a single line.

And a breakage that grep cannot catch: "Any dictionary mutated inside a tool handler is correct on one instance and wrong behind round-robin. This is silent, not an error".

### A WAF or proxy that strips Mcp-* fails everything
> From the outside it looks like a client bug, so people look in the wrong place and find it not right away

A WAF, reverse proxy or firewall rule that strips unknown Mcp-* headers fails every one of your requests. It is a landmine costlier than everything else on the list precisely because the symptom leads in a different direction.

Before migrating, walk the whole request path: CDN, WAF, proxy, load balancer. Any layer can strip, the symptom is the same. The cheapest way to check: stand up an echo endpoint behind the same perimeter and see what reached it.

### Checklist for migrating your own server: ten items
> The order of work for this week, from the discovery method to walking the request path

1. Implement server/discover.
2. Read the protocol version and client capabilities from the _meta of every request.
3. Stop issuing session identifiers, respond 405 to GET and DELETE.
4. Validate the three required headers against the request body.
5. Move cross-call state into explicit handles with at least 128 bits of entropy.
6. Replace server-initiated requests with InputRequiredResult plus a repeated call.
7. Add ttlMs and cacheScope on the six operations.
8. Replace -32002 with -32602 and grep the code for hardcoded numeric values.
9. Make a decision on dual-era mode: if other people's pinned clients call you, it is mandatory.
10. Walk the whole request path looking for stripping of Mcp-* headers: CDN, WAF, proxy, load balancer.

---

## Where server state lives after sessions are abolished

There are no more sessions, and the state moved into a handle that the server gives to the client and gets back. Below: what survives a restart, how long a handle must be, where to validate it and which storage to take for your topology.

### stdio is a personal tool, HTTP is a team service
> SSE is only legacy: some platforms no longer support it, rather than deprecating it

The boundary runs along the data and the number of consumers, not along sophistication. stdio: one process, one machine, in-memory state gets away with it. Streamable HTTP: several instances behind a load balancer, so state must live outside the process.

By the public cross-section roughly 59% of servers are already on Streamable HTTP and 34% on stdio, that is, remote has become the default.

On the transport legacy separately: on some platforms the deprecation of HTTP+SSE is no longer a deprecation but a refusal. The verbatim wording of one of the large enterprise platforms: "The deprecated two-endpoint HTTP+SSE transport is not supported". That is, you cannot rely on SSE not because it is impolite but because you will not get connected.

### What survives a restart and what lives for one run
> Five layers of state, and the first three you no longer control in any way

1. Protocol state (version, capabilities, client identity): lives for one request, everything travels in the _meta of every request.
2. Transport state (an open subscriptions/listen stream): one connection, not recoverable.
3. A request in flight (a tools/call being processed): until the stream breaks. A break means the request is lost.
4. Application state (a basket, a draft, import progress): as long as the handle lives in your storage.
5. A Tasks extension task: the identifier is durable until the response is sent, the TTL is set by the server.

The practical meaning of the breakdown: the first three layers you no longer control, the fourth is entirely yours, and it is the one that determines the architecture.

### There is no resumability: a break is a lost request
> The client MUST resend with a new identifier, the repeat is indistinguishable from a new one

Verbatim: "Resumability is gone. No Last-Event-ID, no SSE event IDs. A broken response stream loses the in-flight request, and the client must re-issue it as a new request with a new request ID".

From this comes a consequence worth keeping in mind through the whole next screen: a client's repeat is indistinguishable from a new call.

### A handle is a de facto bearer token: at least 128 bits
> Opaque and not derived from predictable inputs: the protocol has no such concept

First about the status: the section on stateful tools is marked non-normative, the protocol has no concept of a handle. Verbatim from SEP-2567: "There is no handles/* method, no handle type in the schema, no wire-level concept of a handle at all... The normative content of this SEP is the removal; the guidance is what fills the gap". Looking for a stateHandle field in the schema is useless: on the wire it is an ordinary string in an argument.

The entropy requirement: at least 128 bits of cryptographically strong entropy, that is, a UUIDv4 or 22 or more URL-safe base64 characters. Never derive it from predictable inputs, always limit its lifetime.

This is a requirement for unauthenticated servers, where a handle inevitably becomes a bearer token. For authenticated ones it is not superfluous either.

### Write the TTL and retention policy in the tool description
> The model must see them at the moment of decision, and it never reads the README

The wording "state lives while the connection is open" no longer applies, because there is no connection as a unit of lifetime.

A sample from the specification of how this looks in the description of the creating tool: "returns a basket_id; baskets expire after 24h idle". This is read by the model, not by a human, and read at the moment of deciding whether to call the tool.

### An expired handle returns an intelligible error
> Not "invalid argument": from an intelligible error the model corrects itself and moves on

A sample: "basket bsk_a1b2c3 has expired". From such an error the model is able to correct itself and create the basket again. From "invalid argument" it cycles through arguments and leaves.

This is a special case of a general rule: errors in MCP are written for the model, not for a human in a log. We cover the full error contract in the seventh block.

### Validate the handle and auth context pair on every call
> Ownership is not authorization, and handles end up in chat logs and subagent prompts

Handles end up in chat logs, clipboards and subagent prompts. So for authenticated servers a pair is checked on every call: the handle itself and the identity from the token of this request.

This is exactly the requirement whose absence cost the ecosystem three CVEs on the old session mechanics. The difference is that now it is your responsibility in the tool code, not the behavior of the SDK: the binding mechanics are covered in the tenants block.

### A handle goes into the chat transcript and survives a restart
> Sessions did not give this: a conversation reopened on another device and it is back there

Handles land in the tool result, hence in the dialogue transcript. Any client that saves chats saves the handles automatically.

Reopening a conversation after a client restart or on another device puts the handle back in front of the model without any recovery machinery. This is a plus that you pay for with the entropy requirement and the mandatory pair check on every call.

### Storage by topology: SQLite, Redis, Postgres
> On serverless and a read-only filesystem never SQLite: the file is visible only to its own process

1. One process, no external services: SQLite in WAL mode. In-process, no network hop, a single writer.
2. Several workers behind a load balancer: Redis. Native TTL, concurrent writes, fractions of a millisecond.
3. You already have Postgres and need audit: PostgreSQL. ACID and queries, TTL by hand.
4. Serverless or a read-only filesystem: Redis or Postgres, never SQLite. A local file is visible only to its own process.

A split by data type if the server has grown: active metadata in Redis, the audit trail in Postgres, large tool outputs in object storage, semantic memory in a vector database, policy config in a database or a config service.

There is no standard solution for a handle store, there are early libraries: you can look at them, but it is too early to build on them.

### Redis is necessary but not sufficient: a failure analysis
> The failure lived a layer above the storage: Redis was connected and never queried

An analysis of a public incident on a container runtime, 24.07.2026. The team moved state into managed Redis, and it did not help. The failure happened a layer above: the session manager did not find the Mcp-Session-Id in its internal instance map and returned 404 before the tool code was even called. Redis was connected and never queried.

The authors' conclusion verbatim: "Redis is necessary for state durability... Redis is not sufficient, and for current protocol versions, it is not even reachable when the failure occurs".

The 2026-07-28 revision removes this very door: the identifier arrives as an ordinary tool argument. Redis remained the right storage, the key changed.

---

## Idempotency key: where it is born and what guarantees it

There is no resumability in the protocol any more: the client resends a broken call under a new identifier, and for the server it is a new call. Everything below follows from this.

### The idempotency key is born in the calling code
> Before the side effect, not inside the handler: otherwise the key is new on every retry

This is the place where the pattern breaks most often. uuid4() inside a tool means a new key on every retry and kills the mechanism completely. There must be no timestamps or random values in the key.

The key is born in the calling code before the side effect and is persisted into the agent's state before the call. Ingredients: the tool call identifier, the conversation identifier, the tool name, a hash of the serialized arguments.

The scope of the key: it covers the operation with an external effect, not the reasoning that led to it. The authors' formulation: "Key the charge, not the thought that led to it".

### Three buckets: reads, writes, long operations
> The key is mandatory for two buckets out of three, and four sources of retry add up

1. Naturally idempotent reads (get a customer, check an order status, search): retry freely, no key needed.
2. Writes with a side effect (charge a payment, book, send an email, create a ticket): the key is mandatory at every retry layer.
3. Long operations (report generation, bulk export): a key on the trigger plus a separate status endpoint.

Why this is not paranoia: four independent sources of retry add up. The model retries on a tool error, the tool wrapper on a transient HTTP error, the orchestrator retries the whole turn on a timeout, the provider retries inside itself.

The machine-readable signal for the client is the tool annotations: readOnlyHint, destructiveHint, idempotentHint, openWorldHint. idempotentHint with the value true allows the client an automatic retry. Creating operations and model-backed tools get false by definition.

### The dedup window is documented in the field description
> Not in the README, which the model does not read: the window lives in the schema field description

How this looks in the tool schema:

{"name":"send_slack_message","description":"Send a message. Idempotent on idempotency_key; server dedupes within 5 min.","inputSchema":{"type":"object","required":["channel","text","idempotency_key"],"properties":{"channel":{"type":"string"},"text":{"type":"string"},"idempotency_key":{"type":"string","description":"Unique per send-intent. Reuse the same key to retry safely."}}}}

The key is a required schema field, not an internal server detail: only the calling side can generate it.

### The dedup table is written in the same transaction as the effect
> The arbiter is the database, not the code: a unique constraint catches the race that was slept through

If the underlying API does not support keys, keep your own deduplication table and write it in the same transaction as the side effect. A unique constraint on the key column is a backstop: if two retries race and both passed the read, the second INSERT fails on the constraint, the failure is caught, and the winner's row is read.

Three tests without which a writing tool is not ready for prod:
1. Timeout after success: the operation went through, the response was lost. The retry must return the cached result.
2. Error before the server: the retry must perform the operation for the first time.
3. Race of identical keys: one executes, the second gets the cached result, the effect fires once.

And separately: durable execution engines do not replace the key. The journal protects only the steps inside the engine, and as soon as a step goes out to someone else's API, the "exactly once" guarantee degrades to "execute until it confirms". Plus the engine itself adds another layer of retries.

---

## Deprecation windows of the protocol itself

The time frames the protocol assigned to its own removed mechanisms. Useful as a sample of construction, not as your calendar.

### Deprecations: a window of ≥12 months, zero removed so far
> The window is counted from the revision's release, not from the date the SEP reached Final status

Marked Deprecated on 28.07.2026: Roots, Sampling, Logging and dynamic client registration. The earliest removal is the same for all: the first revision released on or after 28.07.2027.

Two things are usually told incorrectly. The window is counted from the release of the revision in which the feature is first marked Deprecated, not from the date the SEP reached Final: verbatim "measured from the release of the specification revision in which the feature is first marked Deprecated, not from the date the SEP reaches Final". And zero removed so far under this policy: "No features have been removed under this policy yet", checked on 01.08.2026.

The window can be shortened only for an active risk with a published advisory, and even then not below 90 days.

So as not to relax anyone: 12 months applies to Roots, Sampling and Logging. Sessions are not deprecated, they are removed, there is no window at all.

Where to migrate: sampling to a direct call to the model provider's API, roots to tool parameters, resource URIs or server config, protocol logging to stderr for stdio and OpenTelemetry for everything else.

### HTTP+SSE: three months versus a year across two sources
> Two primary sources on the same domain give different time frames, and only one is normative

The transport itself was marked Deprecated back on 26.03.2025, that is, long before this revision. The dispute is about the removal time frame.

Two primary sources on the same domain give different time frames, and both quotes are verbatim. The registry of deprecated features: "Three months after SEP-2596 reaches Final". The release blog of 28.07.2026: "with a year-long offramp".

The resolution is not by authority but by the source's self-definition. The registry says about itself: "a derived view kept consistent with the per-feature deprecation notices and changelog entries, which are the normative records". That is, the registry is derived from the per-feature notices and the changelog, and it is they that are normative, and they state the three-month period. The "year" in the blog looks like a carry-over of the twelve-month default from the neighboring paragraph about Roots, Sampling and Logging.

Why this is in the session: not for the time frame, few people care about HTTP+SSE. For the technique. A feature's status is checked in the registry and in the changelog, not in the release blog, and this conflict is the only living example in the whole revision where the difference is visible in one click.

---

## Links mentioned in the session

Collected from the screens of this block: what I relied on out loud, and what is worth opening yourself.

| What it is | Link |
|---|---|
| Era compatibility, the client × server matrix | [https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning) |
| state-of-mcp: the census tool and dataset | [https://github.com/RoninForge/state-of-mcp](https://github.com/RoninForge/state-of-mcp) |
| mcp-spec-check: an independent check of the same thing | [https://github.com/Roee-Tsur/mcp-spec-check](https://github.com/Roee-Tsur/mcp-spec-check) |
| MCP blog, the release candidate post, 21.05.2026 | [https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/) |
| MCP specification | [https://modelcontextprotocol.io/specification/versioning](https://modelcontextprotocol.io/specification/versioning) |
| MCP specification 2026-07-28, Base Protocol | [https://modelcontextprotocol.io/specification/2026-07-28/basic/index](https://modelcontextprotocol.io/specification/2026-07-28/basic/index) |
| MCP specification repository, docs/seps/2567-sessionless-mcp.mdx | [https://github.com/modelcontextprotocol/modelcontextprotocol](https://github.com/modelcontextprotocol/modelcontextprotocol) |
