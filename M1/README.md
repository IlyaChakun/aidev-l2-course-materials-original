# Module 1. Advanced MCP

## About the module

The first module covers the execution layer of the course project: your own MCP server over an internal database, through which the agent works with an entity rather than just reading it.

The requirement for the server is set as an invariant: **an agent without hints takes the entity through its lifecycle and cannot make an invalid transition**. Everything else follows from this: the set of tools, their descriptions, and what the server replies to a wrong attempt.

This folder holds four things: the homework text, a scaffold for checking your environment, starter data, and guides on the module's topics. You design the tool contract yourself; that is the substance of the assignment.

## What is in this folder

| File or folder | Why |
|---|---|
| [`homework.md`](homework.md) | **The module homework** — the source of truth for the assignment text: what to submit, the normal/advanced levels, acceptance criteria, deadlines |
| `slides/` | The module slides as one self-contained HTML file: opens with a double click, guides embedded inside |
| `starter-server/python/` | Starter scaffold in Python: one tool, one resource, launched with one command. `mcp` SDK 2.x. Has its own README with installation, connecting to Inspector and a breakdown of typical errors |
| `starter-server/typescript/` | The same in TypeScript, `@modelcontextprotocol/server` 2.x packages. The README explains the version fork: why not `@modelcontextprotocol/sdk` |
| `fixtures/` | Starter data for the four course project tracks: `schema.sql` for SQLite and PostgreSQL plus 20 records in each. Has its own README with one-command loading |
| `guides/` | Seven guides on the module's topics, see the table below |
| `images/` | Illustrations for the assignment: an example of an assembled n8n chain |
| `examples/` | Export of the example n8n workflow from the assignment: import it via Workflow → Import from File |
| `reading-list.md` | Primary sources with links, dates and a "why read this" line. Plus a list of claims for which a primary source was searched for and not found |

## Guides

| Guide | What it covers |
|---|---|
| [Protocol revision 2026-07-28](guides/protocol-revision-2026-07-28.md) | What changed, what was removed, what became mandatory, a twelve-item migration checklist, the era compatibility matrix, SDK versions, ecosystem readiness on the measurement date |
| [Tool design](guides/tool-design.md) | How many tools and by what measurements, how to name them, which schemas, the error contract, the debate over server shape, how to choose someone else's server |
| [Security and authorization](guides/security-and-authorization.md) | Five code requirements plus a sixth, the norm for responding to an unauthorized call, the asymmetry of server and client obligations, a table of the three authorization revisions, a working-minimum checklist, a timeline of nineteen incidents across thirty identifiers |
| [Multi-tenancy](guides/multi-tenancy.md) | Where the tenant comes from after sessions are removed, tool-level RBAC, the public tool-list cache trap, three isolation layers and five leak surfaces besides SQL, four isolation tests |
| [Versioning your server](guides/versioning.md) | Three classes of schema breakage, a "breaks or additive" table, a lifecycle policy as a model, the compatibility window, idempotency, rollout order |
| [Observability](guides/observability.md) | What to measure, how a trace is now assembled, two independent error lines, the error contract as a cut, the state of telemetry conventions, starting threshold guidelines |
| [The low-code / code boundary](guides/low-code-boundary.md) | Four thresholds for moving to code, the mechanics of overpaying for tool definitions, what is lost in the move, where the difference from a code graph is real |

The guides can be read independently of each other and refer to each other by topic. If you only have time for one, take the first: the specification came out on July 28, and almost the whole corpus of texts about MCP on the internet was written before it.

## How to use this

**Step 1. Check the environment.** Bring up the scaffold on your stack and make sure it is visible in MCP Inspector. This is five minutes and one command. The scaffold is intentionally empty: it has one tool that does nothing with data, and one resource. If it comes up, the environment is ready.

Both implementations have a `selfcheck` that starts the server over stdio and prints what it returned over the protocol. It is there to separate an environment problem from a code problem: if `selfcheck` passed but Inspector does not see the server, the issue is the connection, not the server.

**Step 2. Take the data.** Pick the folder for your track in `fixtures/`, load the schema and records. The records are spread across all lifecycle statuses, so there is something to test both a successful pass and a rejection on. Using your own domain instead of the suggested one is also allowed.

**Step 3. Replace the scaffold's contents with your own.** The places where this is done are marked with comments in the code. A guideline for scope: 3 tools at the normal level, 5 at advanced. At least one resource: the database schema or a state summary. At advanced, a resource template of the form `db://entity/{id}` is added to it.

**Step 4. Check from Inspector and from your IDE.** Both commands are given in the scaffolds' READMEs.

## How to read the numbers in the guides

Every number comes with its measurement method: the snapshot date, the denominator, the detection method. This is not pedantry. In this field three loud numbers "about the same thing" usually measure three different quantities, and without a method column they contradict each other.

Where there is no support, it says so directly. The threshold table in the observability guide goes under an explicit header, "starting guidelines, calibrate to your stack": eight of the nine numbers in it went through verification and found no primary source, and the ninth rests on a press report, not a measurement. The claims that did not survive verification are collected in a separate section of `reading-list.md`, together with what exactly is wrong with them.

## Versions

Both ecosystems released major versions at the end of July 2026, and a significant part of what has been written about MCP refers to the previous ones. The exact versions, publication dates and links to primary sources are in each scaffold's README. That is also where the two traps that cost the most time are covered: `mcp` vs `fastmcp` in Python, and `@modelcontextprotocol/sdk` vs the second-line packages in TypeScript.

The current protocol revision: 2026-07-28. Both scaffolds conform to it.

All links in the guides were checked on 02.08.2026, and the specification URLs were rechecked on 03.08.2026. What goes stale first and how fast: the last section of `reading-list.md`.

---

*The first module of the HSS AI-dev L2 course. The next module: the second — context management,
RAG on Qdrant for the course project.*
