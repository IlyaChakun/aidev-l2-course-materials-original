# Designing tools and responses in MCP: the full module guide

> Compiled 02.08.2026. All primary sources were opened and checked on 01–02.08.2026.
> Schemas and naming rules follow protocol revision `2026-07-28`.

## Why this file

The tool contract is something you design yourself: the framework will not suggest it, and the
protocol only defines the shape, not the content. This is the main reference for the "how to write
a tool" block: everything covered in the session is collected here in full, with examples.

What is inside, in order of decisions:

1. what shape to give the server and where the logic lives (section 1);
2. how many tools, how to check that, and how to collapse the extra ones (sections 2–4);
3. what to write in a tool description: a canon of ten points with "bad and good" pairs (section 7);
4. how to forbid a call and how to declare a stop condition (section 8);
5. what to do when the description no longer helps: tool search, code execution, collapsing,
   resources, response limit (section 9);
6. schemas and why they do not transfer between providers (section 10);
7. the error contract: three classes of failure and the wording for each (section 11);
8. how to choose someone else's server and what to check before applying it (sections 12–13).

All numbers below come with the measurement method. In this area, numbers without a denominator
contradict each other systematically, so the "measured by" column matters more than the number
itself.

---

## 1. Server shape: a debate you will have to settle yourself

Two schools, both with measurements, both in production. There is no winner, and you need to know
both, because the second one will come to you in review.

| | "A server is a thin proxy" | "Invariants live in the server" |
|---|---|---|
| Thesis | There should be no logic in the server; it is primitive and can be read whole in one sitting. Typical size is 5–15 entry points | A server you come back to holds state and precomputes the response. It is not a mirror of the API but a boundary of capabilities |
| Separation rule | Judgment or domain knowledge is required, so it goes into the agent's system prompt. A mechanical data query goes into a tool | The deterministic belongs in code: resolving names to identifiers, permission checks, sequencing of dependent calls |
| Argument for | `list_failing_pods` looks clean, but in Kubernetes `phase=Running` does not mean "healthy": a pod can be Running and in a crash loop at the same time. The definition of "failing" is a domain judgment; it gets frozen into the server and prevents reusing it for a different query | Property search went from three agent turns down to one after a fuzzy index. Analytics went from a timeout at 30 seconds to a response in under a millisecond. "Every sum in every report was wrong until the server started converting cents on the agent's behalf" |
| Argument about the consumer | An extra layer means extra failure surfaces: client, server, transport instead of a single script | A human looks at a page and clicks on; an agent makes five calls and puts all five responses into the window. A slow response and a sixty-field blob are multiplied by every call |
| Where the removed complexity goes | Into the agent's prompt, that is, into probabilistic reasoning | Into the server code, that is, to where it is deterministic and auditable |
| What it costs | Verbosity, tokens, round-trips. Business logic ends up in the model's reasoning | Blast radius, versioning as a behavioral regression, the server turns into a product with an on-call rotation |

**Where both schools agree.** A bare one-to-one wrapper over REST is bad for everyone. Empirics
from the corpus of official servers: **80 of 87** REST-backed repositories are bare wrappers; 88.6%
of servers sit on REST. The corpus denominator is 114 repositories, and the figure is counted per
repository, not per individual tool.

**The formulation that came closest to a reconciliation.** A well-designed server is an
Anti-Corruption Layer from DDD, and the debate is not about "whether it is needed" but about
**where it lives**: inside the server if the contract is yours, or next to it on the host side if
the server is someone else's. Verbatim: "a thin adapter gives flexibility and easy tests, but high
verbosity and token cost, and pushes business logic into the model's reasoning. A thick tool lowers
the cost and the number of round-trips, moves the logic into server code, where it is deterministic
and auditable, but carries a larger blast radius. **This is not better versus worse, it is a choice
of where the complexity lives**."

Limits of the analogy to keep in mind: a classic ACL stands between two deterministic systems,
while here the consumer is probabilistic. A tool description, unlike a facade, is also an attack
surface through prompt injection. And invariants smeared across several calls are not fixed by
translation at the boundary.

### Operating rule: `start atomic, promote on signal`

Start with thin tools. Promote to aggregation only where real traces demand it. Three signals to
promote:

- a high retry rate;
- repeating sequences of the same tools;
- partial completions of multi-step operations.

### Content boundary

The formula on which practitioners of both schools converge: **encapsulate operations, not workflows.**

| Can be handed to the server | Gray zone, only with a preview | Do not hand to the server |
|---|---|---|
| Deterministic composition, validation, projection over data, permission checks, rollback preview | Summarization, ranking, task creation | Autonomous choice of a goal, irreversible business decisions, hidden multi-step planning |

Short formula: **hide complexity, not responsibility.**

---

## 2. How many tools

### Threshold corridor: who said it and with what weight

The third column matters more here than the second.

| Who | Number | Level of normativity |
|---|---|---|
| Anthropic | selection degradation **past 30–50** available tools | vendor advice in live documentation, eval not published |
| OpenAI | **fewer than 20** functions at the start of a turn | vendor advice, the source itself calls it "just a soft suggestion" |
| Google | active set of **10–20 at most** | vendor advice, Best practices section |
| Gemini API | **128** function declarations per request | hard platform limit, printed in the function calling reference (checked 03.08.2026) |
| Gemini API via Gemini CLI | **512**, live error `400 INVALID_ARGUMENT`: "At most 512 function declarations can be specified" | hard platform limit, but from the error text, not from documentation. **Does not match the documented 128** |
| Claude API | **10,000** deferred tools per request · search returns up to **5** matches | the first is a hard limit, the second is a **default**, not a ceiling. Both are printed in the Limits section (checked 03.08.2026) |
| VS Code | **128** tools per request in chat | hard client limit, checked at request time. The virtual tools threshold setting cannot be raised above 128 |
| Shopify | 0–20 manageable · 20–50 boundaries blur · 50+ "death by a thousand instructions" | **one product's experience**, engineering blog from 26.08.2025, not a conference talk and not a measurement |
| Routing degradation study | elbow of the curve at **40–60 agents** | controlled measurement on a live enterprise catalog |

Three vendors give three different numbers and none publishes an eval. The hard ceilings lie not
where people look for them at all: in the API and in the client, not in the model.

And even a hard limit does not have to be unambiguous. Google's function calling reference prints
128 declarations per request, while a live error of the same API, captured by Gemini CLI users,
says 512. Both numbers are vendor-sourced, and both are reproducible. The practical conclusion is
the same as for the whole chapter: **you learn the ceiling of your own "model + surface + version"
bundle by measuring, not by reading**. Send a deliberately excessive list of declarations and read
exactly what they refuse you on.

> **The threshold "OpenAI errors out at 75–85 tools" does not exist.** There is no primary source
> at all. The public number 128 refers to the Assistants API, which is shut down on 26.08.2026. If
> someone quotes it to you, it is folklore.

### What was actually measured

A catalog of 110 agents and 584 tools from a live enterprise assistant, three frontier models
(arXiv:2606.17519, 16.06.2026):

| What was measured | Value |
|---|---|
| Routing F1 drop as the catalog grows 51 → 584 tools | **16–23 points**. For GPT-5.4: 58.2% → 42.1% |
| Precision versus recall | 68% → 60% versus **55% → 37%**. Recall falls twice as fast |
| Oracle shortlister (the right tool is always in the set) | still **79.0% → 68.8%**: ten points of "confusion" that retrieval does not cure |
| Elbow of the curve | **40–60 agents**, the same across the three models |
| Embedding shortlisting | **52.5%** versus 50.3% for platform tool search and 42.1% with nothing |
| Fixed cohort of 731 queries | the same 14.9-point drop on the very same queries |
| Rich metadata (examples, tags, descriptions) | +4.2 points at the agent level, **less than 1 point at the tool level** |

**The conclusion that changes the recipe.** Degradation goes **through recall**: as the catalog
grows, the model more often **fails to find** the suitable tool than picks an unsuitable one. So
this is cured by discovery, not by tightening descriptions. Verbatim from the authors: "Metadata
quality complements architectural changes but does not substitute for them".

And separately: even perfect search leaves ten points of loss, because in a large catalog the
groups of functionally similar tools objectively grow. Those ten points are not cured by anything
except shrinking the catalog.

### Under control it is a cliff, not a gradual degradation

A controlled experiment on the public Pet Store API: **10 tools perfect, 20 tools nineteen out of
twenty, 107 tools complete failure** for models of both sizes.

A second number with a method: GitHub cut its Copilot MCP **from 40 tools to 13** and gained 2–5
points on SWE-Lancer and SWEbench-Verified plus or minus 400 ms of latency.

Vendor corridors describe a gradual "it gets worse". Two measurements with a method describe a
**threshold beyond which it stops working altogether**.

### What the ecosystem does

Distribution of the number of tools per server over a catalog of 32,820 servers: **median 7**,
mean 15.8, 99th percentile 138, record 824. Another measurement over a different population (only
live remote servers) gives about **19** tools per server.

Two numbers about the same thing differ threefold, and the reason is exactly the same as in this
whole area: different populations. A median of 7 is counted over the whole catalog, where the
median server is a hobby project. Nineteen is counted over those that respond at all.

### Collapsing cases

- **A server assembled in one evening on the "one tool per endpoint" principle:** it came out to
  30–40 tools and an unusable product. After rework **three** remained.
- **Collapsing via an action parameter.** `redmine-mcp-server`: **69 tools collapsed into 43**
  via the `manage_X(action=...)` pattern, of which 34 were merged into 9. A verifiable
  replacement.
- **The upper limit for which code mode was invented.** About 2,500 endpoints of one vendor: one
  tool per endpoint would have given more than a million tokens of schemas. Their server exposes
  two tools, `search` and `execute`, about 1,000 tokens regardless of the surface size. The primary
  source was not opened; the numbers match in two independent retellings.

### Working scale

| Tools in one context | What to do |
|---|---|
| 1–10 | Direct pass-through is reliable. Stay here |
| 10–20 | Attention zone: measure selection accuracy, merge duplicates, tighten names |
| 20–50 | Degradation. Split into domain subagents, each child stays in the safe zone |
| 50+ | Move to retrieval over the catalog. Direct pass-through stops being manageable |

> **Tool Search defers the tax, it does not remove it.** The documentation says so in plain text: "You
> still send every tool's full definition in the `tools` array on every request, including the
> deferred ones", and next to it "the tool definitions that search loads into context count as input
> tokens like any other tool definition". What is saved is the model's window, not traffic and not
> the bill. One thing changes: you stop paying for fifty tools that were not needed on this turn.
> The order stays "measure first, cut second, and hand only the remainder to lazy loading".

---

## 3. It is not about the count, it is about coverage

A measurement of three paradigms (web agent, MCP, terminal) on live enterprise platforms, 729 tasks,
four models, programmatic verification against the live platform (arXiv:2604.00073, 31.03.2026):

- MCP agents have the **lowest success rate**: ServiceNow **11.5–18.5%** with 93 tools;
- **ERPNext with seven tools gives the best MCP performance of the three platforms**, ServiceNow
  with 93 the worst.

The cause is mechanical, and it is the best technical argument in this section. Even when a tool
exists for an operation, it exposes a handful of fields where the underlying API accepts dozens.
The needed field is missing, and **the agent has no workaround**: a CLI or web agent will assemble
an arbitrary payload, while an MCP agent will not. If you narrow the sample to tasks that are
known to be feasible (12 types out of 33, 120 instances), Sonnet's solved share rises from the same
11.5% to 24.2%: the gap narrows, but even where the task is known to be solvable with the available
tools, the MCP agent reaches only a quarter.

> The range 11.5–18.5% is reconstructed from table 2 of the paper itself. Its text says
> 11.5–16.7%, and this discrepancy is inside a single source.

---

## 4. Design from tools

### What these primitives are

The protocol has seven of them. The server declares to the client which of them it supports, and
the client answers in kind. Further on, the guide only talks about tools, so the other six are
listed here once, so that the shares below can be read.

| Primitive | What it is | Who decides when it is used |
|---|---|---|
| **tools** | Actions with parameters and a response: `tickets_search`, `tickets_update` | The model, in the course of the task |
| **resources** | Data to read by address: a file, a document, a policy, a reference record. No side effects | The client or the user: what goes into the context is decided not by the model |
| **prompts** | Ready-made request templates that the server hands to the client. In interfaces these are a menu or slash commands | The user, by hand |
| **discovery** | The ability to notice that the tool list has changed on the fly and re-read it. Without support the list is fetched once at connection time | The client, on a server notification |
| **sampling** | A callback: the server asks the client to go to the model on its behalf, because the server has no key of its own for the model | The server asks, the user confirms |
| **elicitation** | In the middle of work the server asks the user for something missing: clarify the project, confirm a deletion | The server asks, a human answers |
| **roots** | The client declares to the server which directories or areas it may work in. This is a boundary, not a hint | The client |

The practical difference between tools and resources that is most often needed at the start: a long
policy, instruction or reference is a **resource**, not a tool. A server is not built for a single
policy at all, but if a server already exists for tools, the reference layer moves into resources,
and the agent fetches it on demand instead of carrying it in context all the time.

### Support shares

Support of the primitives across the whole client population (snapshot 01.08.2026):

**tools 100% · resources 39% · prompts 38% · discovery 19% · sampling 12% · elicitation 11% ·
roots 8%.**

Full coverage, seven primitives out of seven, belongs to only two clients: VS Code Copilot and
fast-agent. The most complete client of the ecosystem at this snapshot is not the one that is named
most often.

The rule: **we design from tools and treat everything else as progressive enhancement.** Not "do
not do it", but "do not do it first and do not build a mandatory path on it".

The source of these shares does not date its own data, so the figure carries the date of capture,
not of publication.

---

## 5. Responses cost more than schemas

You pay for the schema once, responses arrive on every call. A reproducible measurement
(Anthropic `count_tokens` on `claude-sonnet-4-5`, pinned images, deterministic run, 06.06.2026):

| What was measured | Tokens | Share of 200K window |
|---|---|---|
| GitHub MCP, default toolset, 43 tools | **10,928** | 5.5% |
| GitHub MCP, all toolsets, 82 tools | 20,404 | 10.2% |
| Playwright, 23 tools | 4,633 | 2.3% |
| **One `browser_snapshot` response** for a single page | **38,831** | 19.4% |

The Playwright schema is 2.3% of the window. One response from the same server is about **eight
times larger than its whole schema**. The conclusion "Playwright clogs the window" is correct, but
the cause is usually named wrongly: it is the responses, not the descriptions. The recipe depends
on the cause: cut the response size and design a projection, rather than throwing the server out.

For your own server one thing follows from this: **the response contract is designed on a par with
the schema.**

A side finding of the same measurement, useful to anyone who goes to measure on their own: a
keyless proxy on `o200k_base` undercounts the Claude tokenizer by 16–43% on schemas and
overestimates by about 7% on a verbose response. The proxy error does not have a single sign, so
"roughly counting" will not work: count with your own tokenizer.

> The common estimates "~42K / ~46K / ~55K tokens for the GitHub server" and "~18,000 tokens added
> to every message" **have no primary source**. No carrier names the tokenizer, the image version
> or the measurement scope. In addition, the second claim is wrong in its mechanics: definitions
> live in the system prefix and are cached. Do not use them as a basis.

---

## 6. Tool names

Revision `2026-07-28` fixed what used to be folklore:

- length **1–128 characters**;
- names are **case-sensitive**;
- allowed characters: Latin letters of both cases, digits, `_`, `-`, `.`;
- spaces, commas and other special characters **SHOULD NOT**;
- uniqueness is guaranteed **only within a single server**.

The level here is SHOULD, not MUST. Keep this in mind: swapping the level of normativity is common
here.

**An important caveat about namespacing.** Uniqueness is **not guaranteed across servers**. A client
or a proxy aggregating several servers SHOULD implement a collision resolution strategy, for
example prefixing with the server name. Separately: the server name from `serverInfo` is **not
guaranteed to be unique**, and relying on it for collision resolution SHOULD NOT be done.

**"Bad and good" pairs for names:**

| Bad | Good | Why |
|---|---|---|
| `run`, `execute`, `query`, `get` | `query_postgres`, `tickets_search` | the model chooses by name before it reads the description |
| `search` on two servers at once | `tickets_search`, `billing_search` | the protocol does not resolve collisions between servers |
| `updateTicketStatusById` | `tickets_update` | a long name adds no precision, the parameters are in the schema anyway |
| `helper`, `util`, `do_action` | `release_create` | utility names say nothing about the domain or the action |

That is, namespacing is not a matter of style but a compensation for a hole in the protocol. If you
have several servers, the lack of prefixes also breaks manifest pinning: see the
[security guide](security-and-authorization.md).

### A tool description is a prompt, and it has measurable levers

- **Prescribe "when", not only "what".** Verbatim: "Be prescriptive about *when* to call it,
  not just what it does". And an observation that changes the priority: recent models reach for
  tools **more conservatively**, and trigger conditions in the description give a measurable gain
  in should-call rate.
- **Write as for a new hire.** "Think of how you would describe your tool to a new hire
  on your team. Consider the context that you might implicitly bring: specialized query formats,
  definitions of niche terminology, relationships between underlying resources: and make it
  explicit".
- **Unambiguous parameter names.** `user_id` instead of `user`.
- **Response format affects quality no less than the description.** "Even your tool response structure:
  for example XML, JSON, or Markdown: can have an impact on evaluation performance: there is no
  one-size-fits-all solution". There is no universal response; the choice of format is a subject
  of measurement, not of taste. Teams return JSON by default because it is "machine-readable",
  without checking that the model is worse on it.
- **A `response_format` parameter as a cheap compromise.** Instead of arguing "high-signal fields
  versus technical identifiers", hand the choice to the agent: an enum parameter with the values
  `"concise"` and `"detailed"`. The chain `search_user(name='jane')` → `send_message(id=12345)`
  requires both a human-readable input and a technical output.
- **The lifetime of state is written into the description of the creating tool**, not only in the
  documentation: "baskets expire after 24 hours of inactivity". The model must see the policy at the
  moment it decides to create state.

**A live example showing that description edits work at the level of a single token.** When the web
search tool was launched, the model appended `2025` to the `query` parameter for no reason, which
shifted the search results and hurt quality. It was fixed not by code but by the wording of the
description.

### The description optimization loop run by the agent itself

1. **Prototype.** Bring the tools up and poke at them by hand, build intuition across scenarios.
2. **Task generation.** Generate dozens of "prompt → expected result" pairs. The primary source's
   requirement: tasks are grounded in real data sources, "avoid overly simplistic or
   superficial "sandbox" environments". A strong task requires several calls, potentially
   dozens.
3. **Run.** Run programmatically, with direct API calls, a simple loop per task. In the system
   prompt of the evaluation agent, ask it to output reasoning and feedback blocks **before** the
   calls: this enables chain-of-thought and makes the transcripts more useful.
4. **Refactoring by the agent.** Concatenate the transcripts and hand them to the model: it analyzes
   transcripts well and keeps implementations consistent with descriptions during mass edits.

What to read in the run metrics:

- many redundant calls → pagination and token limit parameters are set incorrectly;
- many parameter validation errors → the descriptions lack clarity or examples.

A warning that is easy to lose: "what agents omit in their feedback and responses can
often be more important than what they include". You have to read the raw transcripts, not only
the agent's complaints.

---

## 7. The tool description canon

A tool description is a prompt, and this week you will write three to five such prompts by hand.
Below is the canon: what must be in every description and how it is checked. Each point comes with
a "bad and good" pair: that pair is the working part.

### 7.1. What it does: one phrase, a verb and an object

Bad: `tickets` — "work with tickets".
Good: `tickets_search` — "Finds tickets by filters: status, assignee, date range".

A verb over data: "query tickets for the week", "change the ticket status", "create a release".
A noun without a verb does not tell the model what will happen on a call.

### 7.2. When to call: trigger conditions, not the purpose

The model will infer the purpose from the name. What it will not infer is under what conditions
this tool is preferable to its neighbor.

Bad: "A tool for searching tickets".
Good: "Call when the user asks about existing tickets or their status. To create a new ticket, use
`tickets_create`".

An observation worth keeping in mind: recent models reach for tools more conservatively than
earlier ones, so an explicit "when" gives a measurable gain in should-call rate. A prescriptive
description ("call this when…") consistently beats a descriptive one ("this tool does…").

### 7.3. Input and output format is declared explicitly, and the response format is chosen by measurement

Teams return JSON by default without checking that the model works better with it. This is a
hypothesis, not a fact: the response format is chosen by measurement on your own task set. A compact
table or line format often wins, because it is cheaper in tokens at the same completeness.

A useful parameter: the response detail level (`detail=short|full`), so that the agent decides for
itself whether it needs the whole record.

### 7.4. One to three call examples where the schema is not obvious

A call example is not a paragraph of text in the description but a ready set of arguments that the
model takes as a pattern. From the schema it knows the types, from the example how they are usually
combined.

```json
{"status": ["open", "in_progress"], "created_after": "2026-07-01", "sort": "updated_desc"}
```

Measured gain on complex parameters: from 72 to 90. From one to five per tool. With deferred
loading, examples are expanded together with the definition, that is, they do not occupy context
until the tool is needed, — this is the cheapest of the techniques in this file.

### 7.5. Critical things are written in the imperative

Bad: "It is advisable to check the budget before creating an order".
Good: "You MUST call `get_budget` before `create_order`".

A caveat about the level: the text lowers the probability of a violation but does not guarantee its
absence. The invariant is checked by code. The wording reinforces the check, it does not replace it.

### 7.6. Names are concrete

Bad: `run`, `execute`, `query`, `get`.
Good: `query_postgres`, `tickets_search`, `release_create`.

A mistake in choosing a tool is most often a name mistake, not a description mistake: the model
sees the list of names before it reads the descriptions.

### 7.7. Parameters are unambiguous

Bad: `user` (a string: name? login? identifier?).
Good: `user_id` (a string, format `U-\d+`).

Bad: `status: string`.
Good: `status: enum[open, in_progress, closed]` — the error becomes impossible at the input, rather
than diagnosed at the output.

### 7.8. Namespacing with a prefix

The protocol keeps name uniqueness only within a single server, while several servers arrive in the
agent's context at once. `search` from two different servers is a collision that the model will
resolve, at random.

Good: `tickets_search`, `tickets_update`, `billing_search`.

### 7.9. High-signal fields instead of service fields

A field stays in the response only if it changes the agent's next step.

Bad: `uuid`, `mime_type`, `etag`, `created_by_service`.
Good: `title`, `status`, `assignee_name`, `updated_at`.

Identifiers are needed for subsequent calls — we keep them, but in compact form and without
duplicating service metadata.

### 7.10. The lifetime of a temporary response is written in words

Some tools return not a finished result but a temporary object that stops working after a while:

- **cursor** — a continuation marker for the output: "here are the first fifty records and a marker
  to take the next ones from"; the server keeps it for a short time;
- **draft** — something created but not confirmed: an email draft, an unconfirmed order, an amount
  frozen on a card;
- **upload session** — an issued address where a file is uploaded in pieces, valid for a limited
  time.

Where this is written: in the text of the tool's own description — the one that the server hands to
the client together with the list of tools. It is the only text the model reads **before** the
call. The parameter schema describes types and whether fields are required, and "how long this
lives" is not expressed by a type.

Good: "The continuation marker is valid for 5 minutes. If it has expired, start the output again;
repeating the same marker is useless".

Without such a line the model learns about the expiry from an error, having already spent a call,
and usually repeats the same thing: the error did not explain what exactly went stale. The same goes
for order: if a tool makes sense only after another, this condition is also written in words —
"call only after `create_draft`".

---

## 8. When NOT to call and when to stop

A bare prohibition is the weakest form. It leaves the model without a next step and at the same
time names the forbidden action next to the tool, that is, suggests it. Phrasings such as "do not
use this tool for creation" raise the chance that this is exactly how it will be used.

Three other forms work, and one of them is missing from most examples altogether — you will have to
add it yourself.

### 8.1. Precondition: a prohibition turns into a route

Good: "Call only after the ticket identifier has been obtained through `tickets_search`".

The strongest of the three forms: it closes the wrong call and explains the right one at the same
time. It fits chains well — a tool that makes sense only second declares this in its first line.

### 8.2. Redirect: the alternative is named by name

Good: "To create a new ticket, use `tickets_create`; this tool only reads".

The name is mandatory. "Use another tool" does not work: the set is large, and the model will
take the closest by name. A redirect is especially useful where two tools are easy to confuse:
`search` and `list`, `update` and `transition`, `get` and `describe`.

### 8.3. Stop condition: an empty response is an answer, not a failure

The third element of the canon, which is absent from most examples and from typical materials.

Good: "If after two filter refinements the result is empty, assume there are no tickets and say so
to the user. Do not repeat the query with the same parameters".

**Where thirteen identical calls come from.** A repeating identical call is not a defect of the
agent but a message about a defect of the description. There are two causes:

1. the tool lacks fields, and the model fills in the missing part with repeated calls with
   different parameters;
2. no stop condition is declared, and an empty response is read as a temporary failure.

It matters most for search and list tools, where an empty response is formally valid. It is fixed
by text, not by an iteration ceiling: raising the ceiling means paying for the same defect many
times.

### 8.4. A positive wording is more reliable than a prohibition

With the same meaning, the positive form is followed more reliably, because it carries an action
and not only a boundary.

Bad: "Do not call `create_order` without checking the budget".
Good: "First check the budget through `get_budget`, then call `create_order`".

### 8.5. The boundaries are set by your agent loop

Text lowers the probability of a spiral of repeats but does not guarantee its absence: the model is
probabilistic. Hard boundaries live in your loop:

- an iteration ceiling per task;
- a retry budget for each specific tool;
- a separate counter of identical calls in a row ("the third identical call in a row — we abort and
  return a message to the agent that it has looped").

Division of responsibility: the description reduces the frequency, the loop limits the damage.
Substituting one for the other will not work in either direction.

### 8.6. Checking what you wrote: let someone who does not know your system read it

Read the description through the eyes of a person who started work today and has none of your
context. What they will ask about:

- what counts as an "active ticket"?
- dates in which time zone?
- is the filter required or can it be omitted?
- what comes back if nothing was found: an empty list or an error?
- "latest" — by creation date or by modification date?

There is one difference from the model: a newcomer will ask aloud, and you will answer. The model
cannot ask — instead of a question it makes a call at random and looks at what came back. Every
unspoken question is a spent call, extra tokens and an extra second of waiting.

Each question is closed with one line: "active — statuses `open` and `in_progress`", "all dates in
UTC", "if there are no matches, an empty list is returned, this is not an error".

**Practical rule:** if the description needs your comment aloud, it is not finished.

---

## 9. When the description no longer helps

The order of work matters more here than the techniques: **measure first, cut the catalog second,
and hand only the remainder to lazy loading.** The reverse order buys the same catalog at a higher
price.

### 9.1. Tool search is a client mechanic, not your server's

Instead of all definitions at once, the model is given a tool for searching the catalog, and it
requests what it needs at this step by itself. Your server hands out the tool list as usual and
does not know what is going on.

Measured tool selection accuracy on two public sets: **49 → 74** and **79.5 → 88.1**. For selecting
candidates inside the search, embeddings give 52.5% versus 50.3% for platform search and 42.1% with
nothing; the authors call lexical search over the catalog the worst approach.

**What this changes in design.** The description must be self-sufficient — it reaches the model in
isolation from its neighbors. And names with prefixes become more important: that is how the tool
is found by search.

**Where exactly it is enabled, three ways:**

1. **In your own code over the API.** A server-side catalog search tool is added to the request to
   the model, and your own tools are marked with a deferred loading flag: they are declared, but
   their schemas do not go into the context until search surfaces them. At Anthropic these are
   `tool_search_tool_regex_20251119` and `tool_search_tool_bm25_20251119` plus
   `defer_loading: true` on the other tools. Restriction: the search tool itself cannot be
   deferred, and at least one regular tool must remain in the set, otherwise the request is
   rejected with an error.
2. **In a ready-made client.** Agent clients do this themselves: they keep tool headers, and pull
   in full descriptions when a tool is needed. As a server author you do not influence this.
3. **On your own server** — your own search tool with a detail level, see 9.4. The only one of the
   three ways that works with any client.

**Enabling checklist:** ten or more tools, or definitions totaling more than ten thousand tokens,
or you aggregate several third-party servers in one agent. When not to: a small stable set that the
agent uses in full in almost every task — there search adds an extra turn and an extra point of
failure.

### 9.2. Code execution: the agent writes a script instead of a chain of calls

A mode in which, instead of calling tools one at a time, the agent writes a short program: it calls
them on its own, processes intermediate responses in code and returns only the result upward. The
code runs in a sandbox on the client or platform side, **not on your MCP server** — your server
still simply answers calls, only now it is code that makes them.

A published measurement on one scenario: **150,000 tokens versus 2,000**.

Where the difference comes from. The saving is not in the code itself but in the fact that the
intermediate data does not reach the model's window. A classic scenario: export ten thousand rows
from one system, filter and match them, write five rows to another. With ordinary calls all ten
thousand rows pass through the context twice — for reading and for writing. With code execution the
filtering happens inside the program, and only the result comes back up. The second source of
savings: tool definitions lie in files and are read on demand, rather than all being loaded up
front.

An honest framing: this is the scale of the problem, not a recipe for the first week. With three
to five tools the sandbox does not pay off.

### 9.3. Collapsing by hand: an action parameter instead of a tool per endpoint

The most applicable technique, and it requires neither search nor a sandbox.

Bad: 40 endpoints run through a generator → 40 tools: `ticket_create`, `ticket_update`,
`ticket_close`, `ticket_assign`, `ticket_comment`…

Good: one tool with an action parameter:

```json
{
  "name": "manage_ticket",
  "description": "Creates, updates and closes tickets. The operation is chosen by the action parameter.",
  "input_schema": {
    "type": "object",
    "properties": {
      "action": {"type": "string", "enum": ["create", "update", "close", "assign", "comment"]},
      "ticket_id": {"type": "string"},
      "fields": {"type": "object"}
    },
    "required": ["action"]
  }
}
```

A verifiable case: `redmine-mcp-server` collapsed **69 tools into 43** with this pattern, of which
34 were merged into 9.

**When collapsing is harmful.** If the actions diverge in access rights, in reversibility or in
input schema so much that `fields` turns into a dumping ground — keep separate tools. Collapsing is
good where the actions are homogeneous and share one object.

### 9.4. Your own `search_tools` with a detail level

No protocol magic: this is your own tool on your own server. It accepts a query and a detail level
and returns a list of your own tools:

- `level=names` — names only;
- `level=brief` — names with a one-line description;
- `level=full` — the full definition with the schema.

The agent first takes the list of names, then expands what it needs. This is progressive
disclosure, without a sandbox and without rewriting the architecture — half an hour of work. A
caveat: the catalog is still declared, and tool headers remain in the context; the detail level
cuts the size of the response, not the fact that the tools exist.

### 9.5. A long policy moves into a resource, a link stays in the description

The boundary rule verbatim: **into the description goes that without which the call will be wrong;
into a resource, that without which it will be suboptimal.**

What moves into a resource: the database schema, formatting policy, a table of codes, a status
reference, a report template. The specification gives two forms — a resource link and an embedded
resource.

### 9.6. The response is cut at a limit, and the truncation is silent

A tool response is cut by default at 25,000 tokens. It is more dangerous than an explicit error
because the truncation is silent: the preview is cut from the head, the needed identifiers go past
the cutoff, and the model starts inventing them. That is, the limit turns into fabrication of data,
not into a rejection.

What to do on your own server:

- pagination by default;
- the cursor is declared right in the tool description (see 7.10);
- your own safeguard on response size with an honest `result_too_large` error, a `size_bytes` field
  and a hint on how to narrow the query.

### 9.7. The guarantee is your code: an output validator plus a retry

A declared schema is a promise, not a check (why exactly, see the section on schema
non-portability below). Since the provider may have silently simplified it, the only guarantee is
your own code that looks at the actual result.

Two places:

- **the tool output** is checked by your server before returning the response: assembled the object
  → ran it through your own validator against your own schema → returned it;
- **the agent output** is checked by your code on the client side, in the same place where you call
  the model.

On failure we do not throw an exception but repeat the request, embedding the text of the
validation error: "field `status` is required, allowed values are `open`, `in_progress`,
`closed`". This is usually enough for the model on the first try, because the error names a
specific field and a specific requirement.

This directly affects a pair of two agents where the output of one goes as the input to the other:
the seam between them is held by a validator, not by the provider's promise.

---

## 10. Schemas

### JSON Schema 2020-12 (SEP-2106)

- A schema without a `$schema` field is considered **2020-12**. Implementations **MUST** support
  at least 2020-12 and **SHOULD** document which other dialects they understand. An unfamiliar
  dialect **MUST** be handled with a clear error, not silently.
- `inputSchema` keeps the mandatory root `type: "object"`, but now accepts **any** 2020-12
  keywords: `anyOf` / `oneOf` / `allOf` / `not`, `if` / `then` / `else`,
  `$ref` / `$defs`.
- `outputSchema` has **no restrictions at all** on the root type: array, primitive, composition.
- `structuredContent` is any JSON value.
- **Backward compatibility.** A server returning an array or a primitive in `structuredContent`
  **MUST** also return the serialized JSON as a text block: old clients may reject a non-object
  `structuredContent`. The asymmetry is one-way.
- **Schema security.** Implementations **MUST NOT** automatically dereference external `$ref` URIs
  and **SHOULD** limit schema depth and validation time. This is direct protection against SSRF and
  a schema bomb via someone else's manifest.

A small thing that catches you on the very first server: **a tool without parameters**. The
recommended notation is `{ "type": "object", "additionalProperties": false }`. The variant
`{ "type": "object" }` is also valid, but accepts any object. `inputSchema` **MUST** be a valid
schema object, not `null`.

### Schema non-portability between providers

`structuredContent` (data that the **server** puts into the result) and the provider's structured
outputs (a restriction of the **model's generation** by a schema) are different things with similar
names. The specification states this explicitly: "`structuredContent` is server-produced result data and is
**unrelated to** LLM "structured outputs"".

Support map for May–July 2026:

| Construct | OpenAI strict | Anthropic strict | Gemini |
|---|---|---|---|
| `anyOf` in properties | accepts | accepts | accepts (since November 2025) |
| `anyOf` **at the root** | rejects | | |
| `oneOf` | rejects | rejects | **silently drops the keyword** |
| `allOf`, `not`, `if`/`then`/`else`, `dependentRequired`, `dependentSchemas` | rejects | limited or none | no |

The worst case here is the third column in the `oneOf` row: the schema is quieter than declared and
there is no error.

### Deterministic order of `tools/list`

> "Servers **SHOULD** return tools in a deterministic order (i.e., the same ordering across
> requests when the underlying set of tools has not changed). Deterministic ordering enables
> clients to reliably cache the tool list and improves LLM prompt cache hit rates when tools are
> included in model context".

This is a free cost optimization that is easy to miss. If the server builds the list by iterating
over a dictionary or by a database query without `ORDER BY`, the order floats from request to
request, the prompt prefix is new every time, and the prompt cache misses.

Nearby: `tools/list` supports pagination (`cursor` / `nextCursor`) and caching
(`ttlMs`, `cacheScope`). For the trap with `cacheScope` on a list filtered by permissions
see the [multi-tenancy guide](multi-tenancy.md).

### `x-mcp-header`: a tool parameter as an HTTP header

A new mechanic of the revision. `x-mcp-header` is set in the JSON schema of a parameter, and a
client over Streamable HTTP mirrors the parameter value into the `Mcp-Param-{name}` header. The
point: load balancers, proxies and WAFs route and meter requests without parsing the body.

Restrictions: primitives only (`integer`, `string`, `boolean`; `number` is **forbidden**), the
value is non-empty, HTTP token syntax, no CR/LF, case-insensitively unique within the schema, only
properties statically reachable from the root. The client **MUST** drop a tool with a violation
from the `tools/list` output, so that one crooked definition does not break the others.

> Attention: the specification warns directly: **do not mark sensitive parameters with `x-mcp-header`**
> (passwords, keys, tokens, personal data). Header values are visible to network intermediaries.

### `input_required` is a regular branch of the contract

Every result carries `resultType`. The core values: `complete` and `input_required`. The practical
consequence for design: a tool that lacked data now has a protocol way to say so, instead of
returning `isError` and hoping that the model will ask the user again.

---

## 11. The error contract

The most frequent reader of your error output is a language model inside a retry loop. Unlike a
human, it takes every word literally. An error message has stopped being documentation of the
failure: it has become an instruction injected into the context of the next attempt. A precise
error ends the loop in one attempt, a vague one accelerates a spiral: wrong fixes, workarounds,
hallucinated flags, a burned budget.

A separate argument for this approach: an instruction in the error text arrives **exactly when the
context is relevant**, whereas a negative instruction in the agent's rules file fades over a long
session.

### Two mechanisms of the specification, and the split is by meaning

| Mechanism | What goes there | How it is delivered |
|---|---|---|
| **Protocol Errors** | problems with the request structure, "which models are unlikely to be able to fix": unknown tool, malformed request, server error | a regular JSON-RPC error |
| **Tool Execution Errors** | "actionable feedback that language models can use to self-correct and retry with adjusted parameters": API rejections, input validation errors, business logic errors | a result with `isError: true` |

The routing rule: clients **MAY** show protocol errors to the model, "though these are
less likely to result in successful recovery", but **SHOULD** show execution errors.

From this comes a design decision that is usually made by accident: **the choice between a JSON-RPC
error and `isError: true` is a decision about whether to give the model a chance to recover.**
Throwing an exception outward is cheap, but it will go into the protocol branch and most likely
will not reach the model.

A sample of good text straight from the specification:

```
"Invalid departure date: must be in the future. Current date is 08/08/2025."
```

Three things in one line: what is wrong, by what rule that is determined, and the data from which
the correct value can be assembled.

### Three failure classes and three different texts

| Class | Example | What the model should do | How to word it |
|---|---|---|---|
| **Validation or bad input** | a typo in a city, a missing field, a value out of range | fix the argument and retry | name the field, the value and the expected format |
| **Temporary failure** | timeout, rate limit, 503, network failure | wait and repeat the same call | say in words "temporary", "try again", give `retry_after_ms` |
| **Permanent failure** | the record does not exist, no permissions, the capability is not supported | stop retrying, change path or ask the user | say **"do not retry"** explicitly |

The words **temporary**, **try again**, **do not retry**, **permanent** are read literally. For a
permanent failure "do not retry" must be written **explicitly**: otherwise a strong model will
loop, being sure it is fixing something fixable.

The production extension adds four classes: **auth/permission** (retry only after the token is
refreshed, stop mutating operations), **rate limit** (retry with backoff, do not spam identical
calls), **conflict** (409, optimistic locking: first read the current state, do not retry blindly)
and **partial success** (a batch of 8 out of 10: retry only the failed identifiers, **never**
replay the successful ones).

### "Bad and good" pairs for each class

Below are ready-made texts. The left column is found in production more often than the right.

**The fork before the text: where the error will go**

```python
# Bad: goes into the protocol branch, the model sees the fact of refusal without an explanation
raise ValueError("ticket 42 not found")

# Good: reaches the model as a regular tool response, and it can recover
return {
    "isError": True,
    "content": [{"type": "text",
                 "text": "Ticket 42 does not exist. Ticket identifiers start with TCK-"}],
}
```

**Validation**

| Bad | Good |
|---|---|
| `Invalid input` | `Invalid departure date: must be in the future. Current date is 08/08/2025` |
| `Validation failed` | `Field assignee_id rejected: user U-91 is not a member of project PRJ-4. Available assignees: U-12, U-30, U-77` |
| `Error in parameters` | `Field limit is out of range: got 5000, maximum is 100. Retry with limit ≤ 100` |

Half the job is "Invalid departure date": the field is named, but what is wrong with it and what it
should be is not said. The third part of the formula (data for the correct value) is what
distinguishes a working error from a brush-off.

**Temporary failure**

| Bad | Good |
|---|---|
| `Service unavailable` | `The service is temporarily unavailable, retry in 2 seconds` + `retry_after_ms: 2000` |
| `Try again later` | `Rate limit: 100 requests per minute exhausted, retry in 12 seconds` + `retry_after_ms: 12000` |

A retryability flag without an interval is an incorrect error, not a half-measure: the agent will
either hit too fast and run into the rate limit, or back off for an arbitrary time and break the
scenario.

**Permanent failure**

| Bad | Good |
|---|---|
| `Operation is impossible` | `Rejected permanently, do not retry the request: the user has no permissions on project PRJ-4. Access is granted by the project owner` |
| `Failed to update` | `Do not retry this call: ticket TCK-42 has been deleted. To create a new one, use tickets_create` |

"Operation is impossible" is read by the model as a description of the current state, not as a
prohibition on retrying, and it goes for a second round.

**A hint that works without a trip to the documentation**

| Bad | Good |
|---|---|
| `Invalid status. See the API documentation` | `Invalid status draft. Allowed values: open, in_progress, closed` |
| `Use another tool` | `This tool only reads. To create a ticket, use tickets_create` |

To open the documentation, the agent needs a tool that reads by address, and it may not be in the
set at all. Everything needed for the next step is in the error text itself.

**An invalid state transition: three parts in one line**

| Version | Text |
|---|---|
| bad | `Invalid status transition` |
| half | `Cannot move the ticket from closed to in_progress` |
| whole | `Cannot move ticket TCK-42 from closed to in_progress: a closed ticket is reopened only through reopened. Transitions available now: reopened, archived` |

Three parts: which transition was requested and from which status → which rule fired → the list of
statuses available right now. It is returned as a result with `isError: true`, not as an
exception. And separately: the invariant is checked by code — the error text explains the refusal,
it does not enforce it.

**About the `-32602` code.** This is "invalid params" from JSON-RPC, a transport-level protocol
error. On the current SDK it arrives in exactly one scenario out of seven checked: when reading a
nonexistent resource. Everything else — a wrong parameter type, a missing required field, an
invalid value — arrives as a regular tool error. "A strict server is entitled to answer
`-32602`" and "this is how it will be by default" are different statements. Practical conclusion:
do not count on the client distinguishing your validation errors by code — the model will
distinguish them, and by text.

### Structured error fields

| Field | Why |
|---|---|
| `code` | a stable machine identifier on which you can branch. **Do not reuse a code between versions** |
| `message` | one short declarative phrase. No stack traces |
| `field` | the path to the offending input field |
| `allowed_values` | a concrete enum, range, regex or schema fragment **that the agent can copy** |
| `hint` | an imperative one-liner: "Use ISO 8601 datetime in UTC", "Reduce limit to ≤100" |
| `retryable` | `true` **only** for temporary failures |
| `severity` | `info` / `warning` / `error` / `fatal`: drives escalation |
| `retry_after_ms` | required when `retryable: true` because of a rate limit |
| `suggested_value` | a ready value that the agent substitutes without reasoning |
| `category` | `validation` / `auth` / `rate_limit` / `state` / `dependency` / `internal` |
| `request_id` | for human audit |

Three rules on top of the table:

- **`retryable: true` without `retry_after_ms` is an incorrect error.** The agent will either
  retry too fast and worsen the rate limit window, or back off for an arbitrary time.
- **`severity: fatal` is a stop signal.** A tool that sets `fatal` on a rate limit causes premature
  escalation to a human. A tool that sets `error` on a deleted resource causes endless repair
  loops. And `severity` is not tied to the HTTP status: a 200 OK can carry a `warning`.
- **`hint` must work without a trip to the documentation.** "See documentation" is a bad hint: it
  forces a call to a tool the agent may not have.

### The error contract is also a telemetry cut

A message like `Something went wrong` breaks two parties at once. The model does not understand
what to do and repeats the call with the same arguments, and since resumability has been removed,
the repeat is indistinguishable to the server from a new call. This is a retry storm, and it comes
from your code, not from the agent's stupidity. At the same time in telemetry all incidents
collapse into one class, and there is nothing to build cuts from.

Decomposition by layers: the low-cardinality class goes into a telemetry attribute, the
human-readable explanation with an action plan goes into the error text, and concrete values and
limits go into the body of the response to the model and do not reach telemetry. In detail in the
[observability guide](observability.md).

---

## 12. How to choose someone else's server (and why health numbers are meaningless without a definition)

An inoculation against other people's reports, useful both to those who install other people's
servers and to those who read industry analytics.

| | Measurement A | Measurement B |
|---|---|---|
| Figure | **4.1% dead** (79.6 / 15.2 / 4.1 / 1.2) | **52% dead** (52 / 31 / 17) |
| Population | the whole official registry, 14,559 entries | 1,847 projects, deduplicated from seven sources |
| "Dead" means | the entry was removed from the registry **or** all declared entry points are broken. **401 and 403 count as alive** | a disjunction of four conditions: no commits for 90+ days plus an open bug · installation breaks on clean Python 3.12 or Node 20 · 5xx on half the probes over 72 hours · an unpatched CVE with no maintainer response for 30 days |
| The question it answers | "will this registry entry respond right now" | "can this project be relied on in production" |

**Three of the four conditions of the second measurement are not about availability at all.** These
are two different quantities, not two dimensions of one.

A third party calculated the difference experimentally: a full pass over 10,716 remote endpoints
showed that counting auth-gated servers as dead **inflates the failure rate about fivefold**
("treating auth-gated servers as down would inflate the failure rate about fivefold"). The
twelvefold gap is assembled from this fivefold factor plus the difference in populations plus the
three months between the measurements.

Two more ways to get any figure:

- **The denominator.** The first attempt by the same author covered **2.8% of the registry** (297
  entries out of 10,716) and gave a rosier picture by a factor of two. The cause was named by the
  author himself: a sample from the registry is biased toward entries published earlier, and they
  are better maintained.
- **Metric substitution.** One tracker reports "alive rate 99.0%", another gives 82.8%. There is no
  contradiction: the first counts the share of entries with `status: active` **in the metadata**,
  the second actually knocks on the endpoints.
- **A second-order denominator.** "How many MCP servers are there in the world in total" for the
  same week: 19.4 thousand in the official registry, 61.4 thousand in one aggregator, 69.4 thousand
  in the deduplicated union. All three are correct and answer different questions. The rule in
  plain text: **a number of servers without naming the registry is not a number.**

### A portrait of the ecosystem's median server

**6 commits in its whole life · 1 maintainer · 0 tests in CI · 142 days since the last commit ·
2 open unanswered issues.** One feature (a single contributor) predicted **78%** of the "dead"
classifications.

Our own crawl of the official registry on **01.08.2026** (a full pass over the API, 195 pages,
`version=latest`): **19,435** unique servers, of which **9,731 (50.1%)** declare a remote endpoint.
This is our measurement, not a publication: it is reproducible with the same command, but not
confirmed by an independent source.

Half of the registry is installed only locally, that is, it requires pulling someone else's code
onto your machine. Next to it are two numbers from other slices, and they must not be added to the
previous ones: **17.2%** of remote endpoints do not respond (**07.2026**, denominator 9,326 remote
out of 18,849 registry entries), about **55.8%** of servers work without any authentication
(another population, not re-verified against the primary source).

The difference between 19,435 and 18,849 is different slice dates on a growing registry, not a
dispute between measurements. Exactly the case for which the reading list says "a number of
servers without naming the registry and the slice date is not a number": in one paragraph there are
four figures and three different populations.

A practical selection rule: do not look at stars or at the fact of being present in a listing, but
at the method by which health was measured, the number of maintainers and the date of the last
commit.

---

## 13. What to check before applying

- **Three pages of vendor thresholds** (Anthropic, OpenAI, Google) are not dated, and the whole
  triple of figures rests on them.
- **Hard platform limits** were cross-checked on 03.08.2026 against vendor docs and error texts and
  change along with API versions. It is cheaper to measure your own ceiling than to read it off:
  one deliberately excessive submission of declarations answers the question more precisely than
  any documentation page.
- **Ecosystem figures go stale within a month**, the composition of catalogs within weeks.
- **The schema support map** changed twice in half a year: check your own "provider + version"
  pair before you build composition into `inputSchema`.

The full list of primary sources with links and dates: [reading-list.md](../reading-list.md).

---

## Appendix A. Tool description skeleton

Copy as is and fill in. The order of the blocks is not random: the model reads top to bottom and
the first two lines decide whether the tool will be chosen at all.

```
<What it does: one phrase, verb + object.>

When to call: <trigger conditions, not the purpose>.
When NOT to call: <a precondition or a redirect by name to a neighboring tool>.

Input: <what is required, what is optional, in what units and time zone>.
Output: <what comes back, which fields, what an empty result means>.
Stop: <when to stop trying; what to treat as an answer rather than a failure>.
Lifetime: <if the response is temporary — how long it lives and what to do when it has expired>.

Call example: <1–3 ready sets of arguments, if the schema is not obvious>.
```

A filled-in example:

```
Finds tickets by filters: status, assignee, date range.

When to call: the user asks about existing tickets or their status.
When NOT to call: to create a new ticket, use tickets_create; this tool only reads.

Input: status — enum[open, in_progress, closed]; assignee_id — format U-\d+; dates in UTC, ISO 8601.
Output: up to 50 tickets, fields id, title, status, assignee_name, updated_at. No matches —
an empty list is returned, this is not an error.
Stop: if after two filter refinements the list is empty, assume there are no tickets and tell
the user. Do not repeat the query with the same parameters.
Lifetime: the continuation marker is valid for 5 minutes; if it has expired, start the output again.

Call example:
{"status": ["open", "in_progress"], "created_after": "2026-07-01", "sort": "updated_desc"}
```

---

## Appendix B. Error text templates

| Class | Template | Required fields |
|---|---|---|
| Validation | `<Field> <what is wrong>: <which rule>. <Data for the correct value>` | `field`, `allowed_values` or `suggested_value` |
| Temporary failure | `<What> is temporarily unavailable, retry in <N> seconds` | `retryable: true`, `retry_after_ms` |
| Permanent failure | `Rejected permanently, do not retry the request: <reason>. <What to do instead>` | `retryable: false` |
| No permissions | `No permissions on <object>. Access is granted by <who>. Do not retry this call` | `category: auth`, `retryable: false` |
| Conflict | `Record <id> was changed by another process. Read the current state and retry with the new version` | `category: state` |
| Partial success | `Processed 8 of 10. Failed: <id>, <id>. Retry only these` | list of failed identifiers |
| Response too large | `The result is too large (<N> bytes). Narrow the query: <how exactly>` | `size_bytes`, concrete advice |
| Invalid transition | `Cannot move <object> from <A> to <B>: <rule>. Available now: <list>` | list of allowed transitions |

Three rules on top of the templates: do not reuse `code` between versions, set `retryable: true`
only for genuinely temporary failures, and never return a stack trace in `message`.

---

## Appendix C. Review checklist before submission

Go through it for every tool. The items people stumble on most often are marked [common mistake].

**Name and boundaries**

- [ ] the name contains the domain and the action, not `run` / `get` / `execute`;
- [ ] there is a server prefix, if the agent will have more than one server;
- [ ] [common mistake] the tool does not duplicate a neighboring one in meaning — otherwise merge them or separate them with a redirect.

**Description**

- [ ] the first phrase: verb + object;
- [ ] there is a "when to call" through conditions, not the purpose;
- [ ] there is a "when not to call": a precondition or a redirect by name;
- [ ] [common mistake] there is a stop condition, if the tool is a search or list tool;
- [ ] [common mistake] there is a lifetime, if the response is temporary (cursor, draft, upload session);
- [ ] the critical part is written in the imperative and backed up by a check in code.

**Schema**

- [ ] parameters are unambiguous: `user_id`, not `user`;
- [ ] enums instead of free strings where the set of values is finite;
- [ ] the schema is flat, without Pydantic/Zod inheritance that produces `allOf`;
- [ ] [common mistake] 1–3 call examples where the schema is not obvious.

**Response**

- [ ] the response has only the fields that change the agent's next step;
- [ ] there is pagination and a safeguard on size;
- [ ] [common mistake] the output is validated by your code, not assumed to be guaranteed.

**Errors**

- [ ] a domain failure is returned as a result with `isError: true`, not as an exception;
- [ ] every error names the field, the value and the rule;
- [ ] temporary ones have `retry_after_ms`, permanent ones have an explicit "do not retry";
- [ ] [common mistake] the hint works without a trip to the documentation.

**The set as a whole**

- [ ] no more than ten tools in one context, or there is a justification;
- [ ] homogeneous actions are collapsed through an action parameter;
- [ ] the iteration ceiling and the counter of identical calls are in place in the agent loop.

---

## Appendix D. How to hand this file to an agent

The guide is written so that it can be put into an agent's context and yield design by rules rather
than by taste. A working prompt:

```
Read tool-design.md in full. Design the set of tools of an MCP server for <domain>.

Work by the guide:
1. First decide on the shape of the server (section 1) and explain the choice in one phrase.
2. Propose a set of tools and justify their number by section 2. If there are more than ten,
   show the collapse through an action parameter (section 9.3).
3. Write a description for each tool by the skeleton from Appendix A. All ten points of the canon
   (section 7) must be covered or explicitly marked as not applicable.
4. For every prohibition use a precondition or a redirect, not a bare prohibition (section 8).
   For search and list tools be sure to add a stop condition.
5. For each failure class give an error text by the templates from Appendix B.
6. At the end run yourself through the checklist of Appendix C and show which items are not closed and why.

Do not invent numbers and thresholds: if the needed number is not in the guide, say so directly.
```

The same file works as a review prompt: "read the guide, run my server through Appendix C and show
the violations with quotes from my code".

---

## Links mentioned in the session

Collected from the screens of this block: what I relied on aloud, and what is worth opening yourself. The links are live as of the date the materials were compiled; SDK documentation pages are not dated and change without warning.

| What it is | Link |
|---|---|
| Scaling Enterprise Agent Routing | [https://arxiv.org/abs/2606.17519](https://arxiv.org/abs/2606.17519) |
| Anthropic, Tool search tool | [https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) |
| Building production-ready agentic systems, 26.08.2025 | [https://shopify.engineering/building-production-ready-agentic-systems](https://shopify.engineering/building-production-ready-agentic-systems) |
| PolicyLayer: catalog snapshot of 32,820 servers, 01.07.2026 | [https://policylayer.com/research/state-of-mcp](https://policylayer.com/research/state-of-mcp) |
| Anthropic: Advanced tool use (tool search, code execution) | [https://www.anthropic.com/engineering/advanced-tool-use](https://www.anthropic.com/engineering/advanced-tool-use) |
| MCP specification: tool errors and isError | [https://modelcontextprotocol.io/specification](https://modelcontextprotocol.io/specification) |
| Google, Function calling docs, live page | [https://ai.google.dev/gemini-api/docs/function-calling](https://ai.google.dev/gemini-api/docs/function-calling) |
| OpenAI, Function calling guide, live page | [https://developers.openai.com/api/docs/guides/function-calling](https://developers.openai.com/api/docs/guides/function-calling) |
