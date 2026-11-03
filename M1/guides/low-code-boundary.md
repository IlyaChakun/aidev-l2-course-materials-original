# The boundary between low-code and code: four thresholds and exit signals

> Compiled 02.08.2026. Node schemas were pulled via programmatic access on 01.08.2026, n8n versions
> were cross-checked against GitHub Releases for the same date. Some of the figures are marked as unverified: see
> the status column.

## Why this file

The first question about low-code in production is not "how do I build an agent" but **"when does low-code
stop being enough"**. If the boundary is not drawn explicitly, it gets built up on its own, usually
wrongly: either "since we are moving to code, low-code was a toy", or "since the canvas can do everything, why do we need
code".

The file answers three questions and no others.

1. By what signals you can tell that you have hit the limit. Not by the feeling of "it got hard", but by four
   independent thresholds with mechanics under each.
2. What you lose when you leave. Six items, and without this half the analysis is one-sided.
3. Where the difference from a code framework is real, and where it is not.

---

## 1. Why the number of tools breaks first

An agent node assembles a working agent in an hour, and it falls apart not where you expect. What triggers first is neither the topology nor the load but **the number of connected tools**, and this has
mechanics behind it, not a rule of thumb.

The model is stateless. So the full schema of every connected tool goes into the prompt again
**on every turn of the loop**: not once at startup, but on every step.

A community measurement of 23.07.2026: four tools on one agent node come to roughly
**3,200 input tokens per turn**.

**The conclusion is stronger than the figure itself:** five rarely used tools cost exactly as much per turn
as five actively used ones. What is connected just in case is not free, it is just that the bill for it
is not issued as a separate line.

> The bench for this measurement is not described. Take it as an order of magnitude, not as a constant. Per-tool token
> estimates across the ecosystem differ tenfold, and there is only one right move here: measure your own
> stack. How to do it, see the [tool design guide](tool-design.md), the section on the
> price of context.

From the same measurement, also without a described bench: tool results make up about **34%**
of all input tokens over a multi-step run, with the ratio of input to output about 1.9 : 1.

### A non-obvious workaround that is almost nowhere named

On Anthropic models the agent node lets you set caching headers through HTTP options,
and **stable tool schemas benefit from `cache_control` the most**. Hence advice that runs against intuition:
**freezing the order and wording of the toolset for the session pays off more
than just cutting descriptions**. At OpenAI prefix caching is automatic from roughly 1024
tokens, but it requires byte-identity, so any reordering of tools zeroes out the gain.

The mechanics are described publicly, but there is no measurement of the savings specifically for low-code.

---

## 2. Four thresholds, and they are independent

Usually three are named. In practice there are four, they are independent of one another, and you will hit
whichever is closest. This is not a ladder you climb but four walls.

| Threshold | What to measure | Figure | Mechanics under the figure | Status of the figure |
|---|---|---|---|---|
| **1. Tools** | how many tool nodes hang on one agent node | **4–5** | the schema of each tool is serialized into the prompt again on every turn. An unused one costs as much as a working one | empirical, mechanics confirmed |
| **2. Load** | concurrent requests to the flow | **10–20** | execution is sequential by default: `batchSize` = 1, `delayBetweenBatches` = 0 ms | the threshold is empirical, **defaults pulled from the node schema** |
| **3. Topology** | nodes with branching, nesting levels, share of Code nodes | **~20**, in external overviews **30+** | before the node count, the indicator "more Code nodes than integration ones" triggers | both figures without a described bench |
| **4. Durability** | number of external calls, wait time, reversibility | **3 calls / hours / irreversible** | this is not a state machine with deterministic replay. Here the third layer begins, not low-code and not a graph | overview of layers, bench not described |

**The first threshold: whose it is.** It is set by the model and the quality of the descriptions, not by the platform. The platform
just does not hide it. The working workaround is not to cut descriptions but to split
a super-agent into specialized ones behind a router.

**The second threshold: a fact that is absent even from the official documentation.** The default execution model
is sequential. In the agent node schema `batchSize` equals one and `delayBetweenBatches`
zero. This is the only built-in rate-limiting knob, and it lives in an options collection that the
documentation does not know about. And the schema itself warns that increasing the batch size, quote,
"might impact the log output ordering".

**That is, you buy parallelism with order in the run log.** With the very tool
that people stay in low-code for.

Here also the practical minimum: production starts not with Docker on a VPS but with queue mode, Redis
and an external Postgres. The default mode runs everything on the main process, and with model calls
of twenty to sixty seconds that means timeouts.

**The fourth threshold, which is usually missing from lists.** If the task is a single read-only step shorter than
thirty seconds, you need nothing: neither canvas nor graph. But as soon as a workflow makes three
or more external calls, waits for an event for hours or performs an irreversible action, durability
stops being optional.

**The reverse boundary, so the list does not read as "everything into code":** if there are fewer than three tools
and none requires multi-step reasoning, what you need is not an agent but a chain.

> Warning: **A ceiling of "220" or "~272" parallel executions does not exist.** Neither figure
> is in the documentation. The real mechanics are different: the variable `N8N_CONCURRENCY_PRODUCTION_LIMIT`,
> default `-1`, which means control is off by default. The thesis "an instance has a ceiling, beyond it
> workers" is true even without a number.

---

## 3. What is lost when you move to code

Everything said above is only the cost. If you stop at the list of thresholds, the analysis is dishonest:
teams stay with a visual orchestrator for reasons other than prototype speed.

| What is lost | What it turns into in code | Cost of replacement |
|---|---|---|
| Visual run log | tracing that you have to set up | the log is tied to the UI and not exportable. Partially covered by OpenTelemetry export, which got public configuration API endpoints in the 2.33 branch |
| Editing in prod with the Save button | a git, build, rollout cycle | incident response speed drops by an order of magnitude |
| Ready-made integration plumbing | your own auth, pagination, retries, limits | **a permanent tax**: maintenance scales with the number of external services, it is not a one-time job |
| `Error Trigger` and the Error Workflow branch | try / except | a different recovery model: the logic is rewritten, not ported |
| Wait block and human approval in a single node | your own wait and approval queue | since version 2.30 Send and Wait responses carry `respondedAt` with an ISO-8601 timestamp |
| Hidden deployment work | server, event subscription, retry queue, checkpointer, secret manager | inherited in full on the day of the move, together with the credentials |

On the first item it is worth clarifying, because it is usually presented as a verdict: what is locked in the UI is the **raw
run data**, not observability as a whole.

**The wording that holds the whole section:** the mistake is not that you use low-code.
The mistake is the belief that the canvas is the whole map.

---

## 4. The objection "a graph is the same canvas, just in a different hand"

A prominent position, and in production teams it is often met. It is worth spelling out, not
sidestepping.

The position's arguments are strong. Both tools define a fixed graph of phases. Both are a layer
of indirection: codebases where fifty lines of plain async Python turned into two hundred
lines of framework code are documented. The tool layer is the same in both.

Arguing about which architecture is more correct is pointless. It is useful to separate the layers.

| Axis | Low-code | Code graph | Is the difference real? |
|---|---|---|---|
| Where the complexity lives | the system integration layer | the agent orchestration layer | **yes**, this is the main axis of choice |
| Role of the model | one node of a deterministic graph | the model drives the graph's transitions | **yes**, different mental models |
| State and pause | assembled on the side by a custom system | step checkpoint and pause-resume as a single primitive | **yes** |
| Tool layer | the same | the same | **no**, here the objection is right |
| Fixed graph of phases | present | present | **no**, here the objection is right |
| RBAC, SSO, audit trail | present at the platform level | absent at the open-source framework level | yes, but the source is an interested party |
| Who owns it after release | operators carry it | engineers are needed | **ownership criterion**: predicts the choice better than any technical axis |

**The formula:** if your complexity comes from external systems, the canvas's flexibility wins. If
the complexity is in how the agent thinks and advances over time, the graph has a higher ceiling.

**The symmetry without which the analysis is dishonest.** An open-source code graph has no
RBAC, no SSO and no audit trail at the framework level, and horizontally scaling a stateful graph means
that the checkpointer backend, task queues, thread management and the web wrapper you design yourself.

> The argument above is taken from a comparison page written by an interested party. The factual
> part is verifiable, the rhetorical framing is not worth carrying over.

**And the criterion that in practice predicts the choice better than any technical axis:** the ratio
of engineers to operators in the team. Whoever owns the flow after release determines the level of the
tool.

---

## 5. Three MCP points in low-code

| Point | Node | What it does | What is important to know |
|---|---|---|---|
| Server from a flow | `MCP Server Trigger`, typeVersion 2 | publishes one workflow as an MCP server, two URLs, Streamable HTTP and SSE transports, no stdio | authorization in the schema is already **four** values: `none`, `n8nOAuth2`, `bearerAuth`, `headerAuth`. With `n8nOAuth2` the flag `Require Workflow Execute Permission` appears, default `true` |
| Client inside an agent | `MCP Client Tool`, typeVersion 1.4 | connects an external MCP server as an agent tool | `options.timeout` = 60,000 ms. Since version 1.2 the default transport is `httpStreamable`, SSE is marked Deprecated. `mcpOAuth2Api` and `multipleHeadersAuth` appeared in **1.2**, not in 1.4 |
| Whole installation | instance-level MCP | a single connection point to the whole installation, search and run flows, read runs | **two** toggles are needed: general access plus an opt-in on each workflow. Bulk enabling since version **2.2.0** |

**A sharp edge worth knowing.** The `search_workflows` tool lists every workflow
the connected user has access to, **regardless of the per-workflow MCP setting**.
The documentation softens it verbatim: "it will only be able to surface previews, not the full workflow
data". That is, this is a leak of the **list**, not of the contents, and the difference is a matter of principle.

### Scope selection on the consent screen

The consent screen when connecting an MCP client uses the same scope picker as the API key modal.
Three modes: All / Read only / Custom. Five groups: **workflows · executions · credentials ·
data tables · projects/folders** (version 2.32, 21.07.2026).

Enforcement is end to end: tools outside the granted scope are neither listed nor callable. On each
group there is a pill with the number of MCP tools it unlocks.

> Warning: **A migration landmine, verbatim:** "Existing connections keep full access after the update."
> The scope model is **not retroactive**: connections created before the update keep full
> access. Check by hand, do not assume the update fixed everything.

---

## 6. The Guardrails node and one configuration trap

`nodes-langchain.guardrails`, typeVersion 2. Two operations: **Check Text for Violations**
(a violation sends items to the Fail branch) and **Sanitize Text** (replaces what it finds with placeholders).
Nine check types: `keywords`, `jailbreak`, `nsfw`, `pii`, `secretKeys`, `topicalAlignment`,
`urls`, `custom`, `customRegex`.

| Class | Types | Cost |
|---|---|---|
| Pattern-based | Keywords, PII, URLs, Secret Keys, Custom Regex | instant, no API call, deterministic, free at scale |
| LLM-based | Jailbreak, NSFW, Topical Alignment, Custom | a model call **per item** |

> Warning: **The correction that matters more than the rest.** The 0.0–1.0 threshold is the **minimum confidence
> for triggering**. So **a higher threshold = harder to trigger = a softer check**, not a stricter one.
> The opposite reading appears in overviews and produces a working error in the configuration. There is no default value
> in the schema, the default is empty: do not carry over numbers from overviews.

Other points: PII covers 20+ entity types (the documentation's advice: select only the relevant ones);
URLs has a **Block userinfo** flag, which blocks links like `user:pass@example.com`,
that is, it prevents credential injection. The node works synchronously.

**The main limitation: redaction is one-way.** Sanitize replaces personal data with
a placeholder and does not store a mapping, `[EMAIL]` cannot be decoded. For a compliance scan this is right.
For a flow that needs the value downstream this is a dead end, and it is cured by an external tokenizer:
`Webhook → Tokenize → LLM → Detokenize → CRM`.

### A layered model of agent budget control

The prompt is only guidance → memory session holds the state → a planner as a control layer →
**a programmatic budget check or human review before an expensive tool** → Max
Iterations (default 10) as an emergency brake, **not as a budget**.

```
AI Agent → Call n8n Workflow Tool → Guard Sub-workflow (session_id, estimated_cost)
         → shared state in Postgres/Redis → budget policy
         → allow → expensive tool (optionally plus human review)
         → deny  → string to the agent: "Tool execution denied: Budget limit reached."
```

The agent receives the denial as an ordinary tool response, and **the chat does not break**. A direct illustration
of the thesis about informative errors from the [tool design guide](tool-design.md).

The vendor's own position (governance blog, 24.07.2026): "Controls that live only in a design doc
will not stop a miss at 2 a.m. Guardrails belong in the execution path". And in the same place an admission that
for a hard ceiling you have to go to a Code node and wrap the tool call with your own
runtime limits. **Even the vendor sends you to code for hard limits.**

---

## 7. Long-lived state: where the built-in mechanism has its limit

The node is called **Data table** (`nodes-base.dataTable`, typeVersion 1.1), the description verbatim
"Permanently save data across workflow executions in a table". There is a separate tool variant
`nodes-base.dataTableTool` with an `ai_tool` output: **the agent writes and reads state itself**.

**Operations.** Rows: Insert · Get · Update · Upsert · Delete · If Row Exists · If Row Does Not
Exist. Tables: Create · List · Rename · Clear · Delete.

**Limits** (documentation, 27.07.2026): the total storage of all data tables of an instance is by default
**200 MiB**. A warning at 80% full, exceeding it disables manual adding and fails
executions. **Direct programmatic access from a Code node is not supported**, only through the node.
A project's data tables are by default accessible to all team members.

> The figure of 50 MB that appears in overviews is historical: it is the announcement of 23.09.2025, and the limit
> has since been raised.

Performance (third-party measurement of 19.12.2025, bench not described): a row insert takes about 8 ms
against ~1,000 ms for Google Sheets and ~50 ms for Postgres. The practical ceiling on self-hosted,
per a community thread, is 2–5 GB. The caveat here matters more than the numbers: its own query layer on top of
Postgres is not optimized the way an indexed table is, so on search and aggregation
you will hit RAM and latency, not the quota.

**When to move to a proper database:** joins, full-text search, version history and audit trail,
data must survive an instance replacement, a write-heavy profile, thousands of unique items per day.

**A ready-made pattern for the course project (dedup ledger):** first delete rows older than 48 hours
**at the very start of each execution**, then fetch the data, filter, read the IDs,
cut off those already present, send the new ones, write the new IDs with a timestamp. As a separate rule:
**always Upsert for sync**, without it retries create duplicates.

---

## 8. Operational gotchas of the MCP Server Trigger

Collected from four independent public guides, June–July 2026. No fact check was done except for the node
schema.

- The credential token **cannot be viewed after saving**. There is no need to Base64-encode it manually.
- HTTPS is mandatory.
- **Reverse-proxy response buffering breaks streaming.** The most common failure point when connecting
  through Nginx: put the `location /mcp/` block above the general `location /`.
- **In queue mode with several webhook replicas, route all `/mcp*` traffic to one dedicated
  replica.**
- The trigger has no separate Active toggle, the equivalent is **Publish**. In the 2.33 branch publish/unpublish
  endpoints were added, and activate/deactivate were marked deprecated.
- There is one required property: `path`, by default a random UUID. For prod change it to a meaningful one.
- The most common beginner mistake: a lone trigger without a single tool node.

### What really limits the cloud version, and what is a myth

**Myth:** "MCP does not work in the cloud because of the security model, you need self-hosted". Outdated.
`mcpClientTool` is an ordinary core cluster node, and instance-level MCP is enabled both in the cloud
and on self-hosted, in all editions, including the free one.

| Limitation | Essence | Workaround |
|---|---|---|
| Network reachability | the cloud cannot reach `localhost`, the endpoint must be publicly reachable over HTTPS. Private networks fail, often silently | a tunnel, a deployed instance, an IP allowlist |
| Filesystem | Read/Write File in the cloud sees only paths under `/home/node/`. Since version 2.32 the node shows a notice in the UI | external storage |
| Environment variables | `N8N_DATA_TABLES_MAX_SIZE_BYTES`, `N8N_CONCURRENCY_EVALUATION_LIMIT`, `EXECUTIONS_TIMEOUT`, `WEBHOOK_SECURITY_MODE` only on self-hosted | self-host only |
| Queue mode and worker topology | worker isolation, `--concurrency`, a dedicated replica for `/mcp*` | self-host only |
| Community nodes | in the cloud only approved partner ones. The 2.33 branch added support for verified community nodes as agent tools | wait for verification |

A self-hosted gotcha as a bonus: when `N8N_API_URL` points to `localhost`, SSRF protection
rejects loopback addresses.

---

## 9. An intermediate step: a graph inside the canvas, not instead of it

You do not have to leave entirely in order to move to code. A working intermediate step: **define the
StateGraph right in a Python code node**, leaving inputs, outputs, scheduling and notifications
on the canvas. The formula that describes it: the canvas as the operating system, the graph as the processor.

Practical value: it is a cheap step between the third and fifth stages of the course project.
You get the graph primitives without immediately paying for deployment, a checkpointer and a web wrapper.

How to reduce risk if the move is complete after all: parallel experiments, validation against a
production baseline, backward compatibility of contracts, a staged transition, circuit breakers,
explicit rollback paths. And a habit that makes the move cheap: **keep business logic outside the
framework**. Then switching the layer is a day of work, not a rewrite.

---

## 10. Case: a release documentation pipeline

A consulting case on a perimeter of a hundred-plus services. The task: assemble release documentation.
The first version lived entirely in low-code, four workflows plus a separate tool for generation.
It worked, and it worked for more than a month.

**It did not break on functionality, and this is an important part of the story.** Functionally everything was there.
It broke on the thresholds from section 2.

Where it ended up: scripts with explicit gates plus a skill.

**And the honest second half, without which the case turns into agitation:** this pipeline does not ask to go back
to low-code, because it has one consumer. Had it had a second consumer or
a non-technical owner, the answer would have been different, and the integration plumbing around it would have
stayed on the canvas.

By all formal signs this pipeline asked for MCP, and the right answer was "not needed".
**The right answer "not needed" is also a result of working it through, not a refusal to do so.**

---

## 11. The boundary is drawn along MCP

A mature system is not a choice of one of two. It is a boundary drawn along a contract.

The same server is called both from a flow on the canvas and from code, so **a move becomes a replacement
of the orchestrator, not a rewrite of the integrations**. The logic behind the contract survives a change of
orchestrator, and that is what makes a migration one-day instead of quarterly.

**Three cases where the canvas stays the right answer even in prod:**

- flows are owned by business users;
- the flow is mostly integration;
- the agent runs a few times a week, and downtime is cheap.

A hybrid is the norm of a mature system, not a defeat.

---

## 12. Figures that sound convincing but have no bench

Use them as illustration, not as argument.

- A multi-agent research workflow on four parallel agents required three nested
  subworkflows and a polling loop, and failed in 3–4% of cases on race conditions in the merge node. The same logic
  took 80 lines of Python without concurrency bugs (a public analysis of three implementations in a row,
  27.04.2026). From the same place: a premature move to a graph turns 50 lines of async Python into 200.
- With two or more worker replicas only one establishes the outgoing connection to the model,
  the rest silently fail with `TypeError: fetch failed`. Agent runs took 24–27 seconds versus
  4–6 on a single replica (issue #15528, version 1.93.0, Kubernetes, May 2025). **Relevance
  on the 2.3x branch was not checked.**
- A vendor estimate: "for 80% of standard enterprise use cases the native node is enough,
  the remaining 20% need a hybrid" (18.07.2026).
- Median added latency per step: CrewAI about 1.4–2.8 s, a code graph about 0.7–1.5 s,
  the canvas about 0.3–1.2 s. Time to productivity 1–2 days for operators on the canvas versus 4–8 days
  for production graphs (a comparative overview, 07.05.2026, method not described).
- Splitting a super-agent: 12+ tools were split into 3 agents behind a router, the prompt size dropped
  (a community thread, July 2026).

---

## 13. Versions as of the collection date

| What | Value |
|---|---|
| stable and the latest tag of the 2.33 branch | **2.32.7 / 2.33.3**, both builds of 31.07.2026 |
| size of one minor release 2.32.0 → 2.33.0 | **257 commits** |
| default `MCP Client Tool` timeout | **60,000 ms** |
| default limit of all data tables of an instance | **200 MiB** |
| scope groups on the MCP OAuth consent screen | **5** (version 2.32) |
| check types in the Guardrails node | **9** |

The number of changed files in the release is deliberately not given: "300" is the ceiling of the compare API's output,
not a measurement.

---

## 14. What to check before applying

- **The branch is updated weekly.** Everything said here about version numbers and the presence of
  endpoints lives for weeks.
- **The scope model migration landmine** (section 5) is checked by hand on your own instance, not from
  the changelog.
- **The Guardrails threshold** is interpreted in overviews the opposite way. Check the direction on your own configuration
  before you set a value.

The full list of primary sources with links and dates: [reading-list.md](../reading-list.md).
