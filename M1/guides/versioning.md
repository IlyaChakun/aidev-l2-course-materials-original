# Versioning your own server

> Compiled on 02.08.2026. Primary sources opened and checked 01–02.08.2026.
> The negative findings about the `Tool` object were checked by grepping the schema source of
> revision `2026-07-28`, not by the prose of the documentation.

## Why this file

You know how to version REST. That is exactly the skill that fails you here, because the
mechanics of breakage are different: **in REST the contract breaks with a response code, in MCP
it breaks silently, with not a single error in the logs.**

And a second point. If your course project is a chain of several agents, the tool contract there
is not an external interface but an internal seam. You will be the one breaking it, in your own
code, a week after submission.

---

## 1. Silent breakage

Take your server and rename the parameter `query` to `q` in a tool's schema.

In REST this is a 400: the contract is violated, the client saw an error, somebody woke up. In
MCP the schema is valid, the server answers with success, the agent keeps sending `query`, your
handler quietly drops it, the model gets an answer for an empty filter and confidently tells the
user there is no data. Not a single error anywhere.

And this is not an edge case but the default behavior: extra keys are allowed, there are no
required fields.

**Thesis: your tool's schema is a public API, only worse, because it breaks silently.**

---

## 2. Three classes of breakage

| Class | What changes | What the client sees | What catches it |
|---|---|---|---|
| **Schema** | type, required-ness, set of fields | a validation error or `-32602` | schema diff in CI |
| **Semantic** | the logic behind an unchanged schema | a correct response with a different meaning | behavioral contract tests |
| **Language** | the `description` of a tool or parameter | nothing, the tool just stops being selected | tool selection share in telemetry |

**The first class** is loud, you know how to deal with it.

**The second:** the schema is byte for byte the same, the logic inside changed. The search used
to do fuzzy matching, now it returns only exact matches. The model expects one thing, gets
another, and the drift accumulates in its reasoning.

**The third does not exist in REST as a phenomenon.** A tool's `description` is not
documentation, it is an instruction by which the model decides whether to call the tool or not.
Change the description and the probability of selection changes. A tool with the description
`Search for users` was called for searching inactive users as well. It was rewritten to `Search
for active users`, the schema did not change by a single byte, and everything that relied on
that edge case stopped working. There will be no error: the agent will substitute another tool
or skip the call.

**A working definition worth taking away:** if a description change causes a regression in a
critical scenario, it is a breaking change, regardless of whether the JSON schema is compatible.

### Four forms of silent drift, each passes strict validation

| Form | What happens | Why the validator is silent |
|---|---|---|
| Renaming with `additionalProperties` open | `query` → `q`, the old argument is quietly dropped | extra keys are allowed, there are no required ones |
| Change of meaning with the same type | `limit` went from "maximum results" to "page index" | the name and the `integer` type did not change |
| Narrowing an enum with a new default | `format: "text"` disappeared, the value is coerced to `markdown` | default substitution happens silently |
| A new required parameter | a strict server answers `-32602` | the only loud case of the four |

> Note: **"Loud" here means "the server is entitled to answer `-32602`", not "this is what
> happens by default".** In a measurement of seven scenarios on the official Python SDK 2.0.0,
> the code `-32602` was produced by exactly one scenario: reading a nonexistent resource. A
> request that does not match the schema, a nonexistent tool and execution errors all arrive as
> `tool_error`.
>
> **The consequence for you:** if you catch a breaking schema change with a test or an alert on
> `-32602`, the test will always be green. You have to catch it on `error.type = tool_error`, and
> keep `-32602` as a second, independent line meaning "the client is talking to the server
> wrongly". More in the [observability guide](observability.md).

---

## 3. What breaks and what is safe

The basis, so that this is not a matter of taste: **a schema describes a set of valid argument
objects. A change is backward compatible if and only if the new set contains the old one.** Every
call that validated yesterday also validates today. This is subtyping, it is older than MCP and
is not up for discussion.

| Breaks old calls | Safe, the old keeps working |
|---|---|
| remove a tool | add a new tool |
| remove a required field | add an optional field |
| add a required field with no default value | add a field with a default value |
| rename a field without a compatibility wrapper | widen a type (`integer` → `number`) |
| narrow a type (`number` → `integer`) | add a value to an `enum` |
| tighten a constraint (raise `minLength`, lower `maximum`) | loosen a constraint |
| remove a value from an `enum` | mark a field as deprecated |
| make an optional field required | |
| tighten `additionalProperties` from `true` to `false` | |
| rewrite a `description` if this changes tool selection | |
| change `annotations` (`readOnlyHint` from `true` to `false`) | |

**The working strategy from this table:** do not delete, do not rename, only add optional things.
When a breaking change is truly needed, a **new tool is created alongside**, and the old one
stays and delegates to it.

The July 28 revision complicated this table: schemas were raised to the full JSON Schema 2020-12
dialect, that is, they expanded the surface on which a breaking change can hide.

### Two borderline cases

**Changing a default value.** The set of valid calls does not narrow, but the behavior of a call
without the parameter changes. An open schema classifier files this as a low-severity patch.
There is no single answer in the corpus, and this is exactly the gap "compatible by schema,
incompatible by behavior".

**The output schema.** A lot is written about `inputSchema`, and about `outputSchema` there is
one thesis: adding a field to the response is safe. The other side (removing a response field or
narrowing an output enum breaks the consumer downstream) follows from the same subtyping, but is
**not explicitly worked out in the sources**: this is an inference, not a fact from a source. For
projects with a chain of agents this matters more than the input schema, because the output
contract is the seam between agents.

---

## 4. The protocol does not help you

Checked by grepping the schema source, not by prose.

| What the current revision lacks | How it was checked | What you cover it with yourself |
|---|---|---|
| a `version` field in the `Tool` object | grep over `schema/2026-07-28/schema.ts`: the only `version:` declaration belongs to `Implementation` | the version of the whole server plus your own registry |
| requirements on the tool version in a call | grep for `tool_requirements` and `toolRequirements`: zero matches in the whole file | registering the new tool in parallel alongside the old one |
| a deprecation annotation | the question was raised in issue #1915 and left unanswered | a prefix in the `description` that the model reads |
| a protocol mechanism for pinning a version on the consumer side | the proposal SEP-1575 is **closed and marked `dormant`**, no sponsor was found, last updated 11.03.2026 | a contract hash on the consumer side as a lockfile |

The composition of the `Tool` object in the revision: `name`, `title`, `description`, `icons`,
`inputSchema`, `outputSchema`, `annotations`, `_meta`.

So you have exactly one channel to the model: **the description text.**

> **About version suffixes in a tool name.** Practice: `search_files` alongside
> `search_files_v1`, the old one delegates to the new. The closed guideline from issue #1915: the
> format allows it but does not recommend it, pinning should be done through `tool_requirements`.
> The problem is that `tool_requirements` does not exist in the protocol. A curious detail: in
> the specification's own example of valid names there is `DATA_EXPORT_v2`. The dispute is open,
> but the alternative has no mechanism yet.

---

## 5. How to announce a deprecation

1. **A prefix in the description:** `[DEPRECATED: use execute_query instead] Execute a SQL query`.
   The model reads the description when choosing a tool, so that is where the marker works.
2. **The old tool stays working** and delegates to the new one with parameter mapping.
3. **The fact of calling a deprecated tool is logged as a structured metric.** Without this, the
   decision to remove it is made blind.
4. **The marker holds three things:** the name of the replacement, the shutdown date, a link to
   the migration guide with an exact parameter mapping. The single word `DEPRECATED` is not
   enough.
5. **A machine-readable changelog**, served as an MCP resource, so that the consumer can check for
   breaking changes before updating.
6. **Canary rollout:** a share of traffic to the new version plus a list of eligible clients,
   rollback comes down to zeroing the share.

```python
# Python SDK mcp 2.0.0 (28.07.2026), class renamed from FastMCP to MCPServer.
# Assembled from documented primitives, not run.
@server.tool(
    name="search_files",
    description=(
        "[DEPRECATED: use search_documents, shutdown 2026-11-01, "
        "guide docs/migrations/search-v2.md] Search over the tenant's files."
    ),
)
async def search_files(query: str, limit: int = 20) -> SearchResult:
    logger.warning("deprecated_tool_called", extra={"tool": "search_files"})
    return await search_documents(q=query, page_size=limit)
```

> **A trap that follows from section 2.** This marker itself is a language break. It changes the
> probability of the tool being selected: here that is the goal, but it must go through the same
> review and the same scenario run as any breaking change.

---

## 6. Lifecycle policy: what to copy

You do not need to write it from scratch, it is right in front of you.

| Element | How it is in the specification | What to carry over to yourself |
|---|---|---|
| Feature states | Deprecated → Removed, Active is the implicit default state | the same three, recorded in the server's README |
| Minimum window | at least twelve months before the **right** to remove | your own number, chosen by the composition of consumers |
| Emergency exception | at least ninety days with a published advisory | be sure to have one, otherwise the hole is closed outside the process |
| Obligation on deprecation | document a migration path or explicitly state that none is needed | the most underrated item: a marker without a migration path is useless |
| Public registry | a page of deprecated items with the earliest removal date | a machine-readable changelog, served as an MCP resource |
| Right to remove ≠ removal | eligible for removal and removed are different states | separate them for yourself too, otherwise a date in the calendar becomes a deadline for another team |

Verbatim about the window:

> "document a migration path (or state that none is required) and remain in the specification for
> at least twelve months, or at least ninety days under the policy's expedited-removal exception,
> before they become eligible for removal"

### What is copied is the construction, not the number

Twelve months is a period for consumers whom you do not know and cannot count. Yours are known by
name.

The protocol maintainers, explaining where the year came from, named a number more useful to you
than the year itself: the bulk of the ecosystem updates within **six to eight months**, and the
year was agreed with large vendors, and it is, verbatim, "more of a feedback period than a
definite period".

> A caveat is mandatory: the telemetry from which the six to eight months was taken is itself not
> published. This is a statement by the maintainers in an interview of 28.07.2026, not a
> measurement.

That is, the window is a decision, not a constant. Measure how long your consumers take to
update, and take your own number.

**What to copy without fail.** The emergency exception for the case of an unfixable hole,
otherwise you will have to close it outside the process. And the separation of "right to remove"
and "removal".

### A four-stage variant for a server with known consumers

- **ACTIVE.** Works normally, no warnings.
- **DEPRECATED.** Works, writes a warning to the log, description with a prefix, the replacement
  is documented.
- **SUNSET.** Returns an error pointing to the replacement, no longer executes the original
  logic.
- **REMOVED.** Deregistered, a call yields the standard "unknown tool" error.

The SUNSET stage is not in the specification's policy, and it is useful: it gives a **loud**
refusal before the tool silently disappears from the list. A public write-up proposes four weeks
each for DEPRECATED and SUNSET, but this number was not verified: treat it as an order of
magnitude.

---

## 7. How consumers find out

The mechanics changed on July 28, and this is fresh news that is in no public versioning guide.

`notifications/tools/list_changed` goes out only to those clients that opened a
`subscriptions/listen` stream with the corresponding flag, and the level there is **SHOULD, not
MUST**. All public guides written before the release (and that is the entire corpus from
February to July 2026) describe the previous separate long-lived stream. A slide or checklist
built from those articles will be wrong.

Gateway practice is stable in this respect and survives the change of mechanics:

- **push as an invalidation signal**;
- **periodic re-fetching of the list as insurance**;
- **when in doubt, fail-open**, because an extra re-fetch costs nothing, and a missed one loses
  state.

> **The position "periodic polling is an anti-pattern" is widespread and does not survive
> practice.** `listChanged` is not universal, some servers declare the capability and send
> inconsistently. Besides, the revision itself introduced `ttlMs` on list methods, that is, it
> legitimized polling with a cadence set by the server.

---

## 8. A contract hash as a lockfile

The same technique as manifest pinning in the [security guide](security-and-authorization.md),
but for a different purpose, and there is exactly one difference: **you must hash `inputSchema`
together with `description`**, and recursively sort the keys (otherwise a server that repackaged
the JSON in a different key order looks like drift).

Why this is fundamental: a parameter whose "max results" turned into "page index" keeps both its
name and the `integer` type. The schema hash will not change, the contract hash will.

Two uses:

- **the server author** runs a diff against their previous `tools/list` snapshot in CI and fails
  the build on an unconfirmed breaking change;
- **the consumer** pins hashes next to the config as a lockfile and on a mismatch does not retry
  and does not guess: it stops, logs the structural and semantic diff, and raises it outward.

A consequence worth knowing in advance: **a deprecation will light up red for a consumer with a
hash gate**, and this is the correct behavior of the gate, not a false positive.

### Tooling that already exists

| Tool class | What it does | What makes it valuable |
|---|---|---|
| Schema evolution classifier | diffs two `Tool[]` snapshots, labels each change as breaking, safe (additive) or patch, fails in CI | an acknowledgments file: a breaking change becomes a conscious decision, not an accident |
| Lockfile for contracts | takes a baseline snapshot (name, description hash, input and output schemas, annotations) and fails the build on drift | a separate class for description changes, catches a `readOnlyHint` flip, SARIF output |
| Compat gate | two independent signals: a subtyping classifier and a replay of recorded calls against the old and new schema | prints the disagreement of the signals instead of hiding it, and fails closed |

Limitations named by the authors themselves: replay is only as good as the call log is complete,
and is blind to paths that never fired. The open validator models only a few JSON Schema
keywords and will stay silent on a tightened `pattern`. And most importantly: **compatibility by
schema is not the same as compatibility by behavior.**

---

## 9. Rollout order and the migration asymmetry

In the era compatibility matrix there is an asymmetry: **"Legacy clients have no fall-forward
mechanism".** An old client cannot discover a server of the new era and adapt, it simply fails.
Only a client that itself knows both eras can discover and adapt.

**Hence the rule: dual-era first, always.** Switching straight to modern-only breaks all the
pinned internal clients at once, that is, the ones you control least. The legacy branch is
removed when telemetry showed zero legacy connections over a full cycle, not when the calendar
said it is time.

### The order of migration to stateless

1. **A static audit by grep** over the server, clients, gateway and deployment config:
   `Mcp-Session-Id`, `sessionId`, `initialize`, `notifications/initialized`, `ping`,
   `logging/setLevel`, `resources/subscribe`, `roots/list`, `sampling/createMessage`,
   `Last-Event-ID`, the `-3200x` codes, plus `sticky_session`, `sessionAffinity`,
   `affinity: ClientIP`.
2. **For each high-risk hit, answer:** what state is behind it, who owns it, how long it must
   live, who is entitled to read and change it, whether two workers can process it safely,
   whether a retry can duplicate a side effect.
3. **Roll out dual-era with modern turned off**, make sure the behavior has not changed.
4. **Turn modern on at one canary instance** behind a header or a path.
5. **A distribution test:** create state, force the next request to another worker, pass only the
   documented handle and the authenticated identity, restart the first worker and repeat.
6. **Remove the legacy branch by telemetry, not by calendar.**

**What cannot be removed together with the session:** the access token validation cache is keyed
by the token, not the connection, and stays.
**What must be extended rather than trimmed:** the list of allowed headers on the gateway and WAF.
**What breaks silently:** any dictionary that is mutated inside a tool handler. It is correct on
one instance and wrong behind round-robin.

---

## 10. The price of moving to stateless: regressions come later

The counterintuitive part. **On the day of the switch nothing breaks.** The specification
supports both eras, the SDKs ship shims, clients keep connecting. Regressions come weeks later,
and they are silent.

**First: the audit correlation key is gone.** The session identifier in production was exactly
what stitched a chain of calls into a single trail. The protocol offers no replacement. An honest
substitute is the authenticated subject from the token plus the trace context, but that is your
work, not a gift of the revision.

**Second: logs go quiet silently.** The logging level is now set in each request, and the default
is silence, not a default level. You migrated the server, forgot the client, the log stream
stopped, there is no error anywhere.

**Third: idempotency became mandatory.** Resumability is removed, a dropped response is
considered lost, the client resends the request under a new identifier, and its retry is
indistinguishable from a fresh call. Every mutating tool needs an idempotency key, which was not
required before.

**The key is born in the calling code before the side effect, not inside the handler.** A
`uuid4()` generated inside the tool will be new on every retry, and the mechanism does not work
at all. The mechanics in detail are in the [observability guide](observability.md).

**Fourth: orphaned work.** `tasks/list` was removed together with sessions ("`tasks/list` is
removed because it can't be scoped safely without sessions"). If an agent crashed in the middle
of polling and did not save the task ID, the work is computed, billed, and nobody will pick up
the result.

---

## 11. A metric that is not in the standard set

**Tool selection share.** A sharp drop after a description change points exactly to a language
breakage. This is the only way to catch the third class in production: there are no errors,
latency does not rise, the share of successful calls does not fall, the tool is simply no longer
called.

The other drift metrics (share of validation errors, retry depth, response parsing errors) are
covered in the [observability guide](observability.md).

---

## 12. What to check before applying

- **The status of SEP-1575** (pinning tool versions on the consumer side). As of 01.08.2026 the
  proposal is closed and marked `dormant`, but the domain is alive.
- **The delivery mechanics of `list_changed`.** They changed on July 28, and the entire public
  corpus on the topic describes the previous one. Check against the revision page, not against
  articles.
- **The names and commands of the tools** from section 8: none of the three classes was checked
  against a primary source, check by hand before putting them in CI.
- **SDK readiness as of a date.** In July articles you can find "only two SDK lines implement the
  protocol change", and in publications of 28–29.07 "all four Tier-1 SDKs speak the revision from
  the day of publication". The discrepancy is explained by dates, not by facts.

The full list of primary sources with links and dates: [reading-list.md](../reading-list.md).

---

## Appendix. How to hand this file to an agent

```
Read versioning.md in full. Design versioning for an MCP server for <domain>.

Work through the guide:
1. Run my set of tools through the three classes of breakage (section 2) and say which of my
   edits over the last month belong to which class.
2. Check the planned edits against section 3: breaking or safe. For each breaking one
   propose a safe alternative by registering a new tool alongside.
3. Write the text of the deprecation marker per section 5: the name of the replacement, the shutdown date, a table
   of parameter mapping.
4. Write the lifecycle policy in the README per section 6, including the emergency exception.
5. Build a contract snapshot hash gate per section 8 for my CI.
6. Run the result through the checklist of section 12 and show the unresolved items.

Rules: there is no version mechanism in the protocol, do not invent one. Do not lower
normative levels. If the guide has no number, say so directly.
```

The same file works as a review prompt: "read the guide, find breaking changes of all three
classes in my diff and show what catches each".

---

## Links mentioned in the session

Collected from the screens of this block: what I relied on out loud, and what is worth opening yourself. The links are live as of the date the materials were collected.

| What it is | Link |
|---|---|
| MCP specification: Tools, revision 2026-07-28 | [https://modelcontextprotocol.io/specification/2026-07-28/server/tools](https://modelcontextprotocol.io/specification/2026-07-28/server/tools) |
| PR #1602: proposal on tool versions, closed with the dormant label | [https://github.com/modelcontextprotocol/modelcontextprotocol/pull/1602](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/1602) |
| Versioning and compatibility policy | [https://modelcontextprotocol.io/specification/versioning](https://modelcontextprotocol.io/specification/versioning) |
| Feature lifecycle policy | [https://modelcontextprotocol.io/community/feature-lifecycle](https://modelcontextprotocol.io/community/feature-lifecycle) |
| Registry of deprecated features of the revision | [https://modelcontextprotocol.io/specification/2026-07-28/deprecated](https://modelcontextprotocol.io/specification/2026-07-28/deprecated) |
| MCP specification: era compatibility | [https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning](https://modelcontextprotocol.io/specification/2026-07-28/basic/versioning) |
| Changelog of revision 2026-07-28 | [https://modelcontextprotocol.io/specification/2026-07-28/changelog](https://modelcontextprotocol.io/specification/2026-07-28/changelog) |
| Issue #1915 in the specification repository | [https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1915](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1915) |
| Interview with the protocol maintainers, VentureBeat, 28.07.2026 | [https://venturebeat.com/orchestration/mcp-just-got-its-biggest-update-ever](https://venturebeat.com/orchestration/mcp-just-got-its-biggest-update-ever) |
| Protocol blog, release candidate post, 21.05.2026 | [https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/) |
