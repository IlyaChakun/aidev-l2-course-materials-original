# AI-Driven Development Level 2 — course materials

Materials for AI-Driven Development, level two: production-grade product AI development.
Custom MCP servers, RAG, agents in code, evals and observability, economics and security.

The repository is filled in as the course goes: a module's materials are published by the time it starts.

## Structure

```
/
├── M1/         ← Advanced MCP: your own server, tools contract, transition validation
├── M2/         ← Context management: RAG and CAG, the eleven layers of the retrieval pipeline
├── M3/         ← Agents and context: state and memory on LangGraph, moving from n8n to code
├── planning/   ← Course project planning: templates and examples for four tracks
├── guides/     ← Cross-cutting guides outside the module program
├── other-slides/ ← Presentations outside the module program
└── ...         ← M4–M7 are added as the course progresses
```

## What is published

### Cross-cutting guides (`guides/`)

- **[CLAUDE.md: best practices and review with an agent](guides/claude-md-best-practices.md)** —
  twelve criteria for a living agent rules file plus a review protocol: you can put the whole guide
  into an agent's context and it will review your rules file itself. The criteria
  are not tied to a tool: they fit `AGENTS.md`, `.cursor/rules/*.mdc` and others.
- **[AI Code Review: what works, what doesn't, and how to build a review agent](guides/ai-code-review-guide.md)** —
  a digest on AI code review: production numbers and lessons from Uber, Cloudflare, Atlassian and others,
  benchmarks, practices that work and typical pitfalls, an analysis of review agent architectures,
  usefulness metrics, prompt techniques and a 15-item checklist for designing
  your own review agent. Every claim links to primary sources.

### M1 — Advanced MCP

- **[Homework](M1/homework.md)** — the source of truth for the text of the first module's assignment:
  submission contents, normal/advanced levels, acceptance criteria, deadlines. The text in the LMS is synced
  with this file.
- **[Module slides](M1/slides/)** — the "Advanced MCP" presentation as a single self-contained HTML file: download it and open it with a double click, no internet needed. Clicking a list item opens the breakdown, and at the end of each block a button opens the full guide on the topic.
- **[Starter server skeleton](M1/starter-server/)** — a server with one tool and one resource in Python
  and in TypeScript. It lets you check in five minutes that the environment is set up correctly: if the skeleton
  starts and is visible in MCP Inspector, the environment is ready. After that, replace the contents with your own contract.
- **[Starter fixtures for four tracks](M1/fixtures/)** — DDL for SQLite and PostgreSQL and
  20 realistic records for each of the four course projects: AI editorial office, smart
  tech support, DevTools assistant, knowledge curator. So you don't spend an evening inventing
  data. Using your own domain instead of the suggested one is also allowed.

Module details: **[M1/README.md](M1/README.md)**.

### M2 — Context management: RAG and CAG

- **[Homework](M2/homework.md)** — the source of truth for the text of the second module's assignment:
  submission contents, order of work, levels with advanced blocks, metrics with calculation examples,
  acceptance criteria.
- **[Module slides](M2/slides/)** — the "Context management: RAG and CAG" presentation as a single
  self-contained HTML file: download it and open it with a double click, no internet needed. Clicking a list
  item opens the breakdown, clicking a picture expands the diagram to full screen.
- **[Eleven helper documents](M2/artifacts/)** — one per pipeline layer:
  data preparation, metadata, chunking, embeddings, database and indexes, search and fusion,
  reranking, generation, corpus lifecycle, security, economics. Written
  so that you can hand them to an agent as context and go through your project with it layer by layer.
- **[Five reference documents](M2/reference/)** — a design checklist, a failure modes catalog,
  twelve principles, the tools landscape, corrections for the Russian language.
- **[Five worked n8n builds](M2/examples/)** — document loading, incremental
  update, an agent with four tools, a full cycle with deletion handling. They import
  into your own n8n, credentials are scrubbed and replaced with placeholders.
- **[Reading list](M2/reading-list.md)** — primary sources with a "why read this" line.
  The first two sections are needed directly for the homework.

Module details: **[M2/README.md](M2/README.md)**.

### M3 — Agents and context: state and memory on LangGraph

- **[Homework](M3/homework.md)** — moving one agent of the course project from n8n
  to code: a LangGraph loop, a checkpointer, short-term memory, a pause before an irreversible action.
  Normal and advanced levels as blocks, acceptance criteria, report skeletons.
- **[LangGraph guide for a coding agent](M3/guides/langgraph-agent-guardrails.md)** —
  the main material for the homework: handed to the agent together with the task. Rules and pitfalls of state,
  the checkpointer, interrupt, navigation; every rule has been verified by running it.
- **[LangChain Code node guide](M3/guides/langchain-code-node-guardrails.md)** — the dialect
  of the n8n code node from the session demo.
- **[Observability guide](M3/guides/observability-langsmith-langfuse-n8n.md)** — connecting
  LangSmith and Langfuse to self-hosted n8n, with verified pitfalls.
- **[Session demo](M3/examples/)** — exports of the two demo stand workflows and the code of three LangChain Code
  examples with comments. Import them into your own n8n, and plug in your own credentials.
- **[LangGraph run player](M3/langgraph-run-player/)** — a visualizer for a graph run, like a
  video recording: a timeline of nodes and model calls, a graph diagram with the active node, state step by step,
  checkpoints, cost and tokens. It works without LangSmith/Langfuse — its own callback writes the log;
  the demo on fake models runs without keys, instructions for connecting it to your own graph are inside.
- **[Module slides](M3/slides/)** — self-contained HTML: download it and open it with a double click.

Module details: **[M3/README.md](M3/README.md)**.

### Course project planning

- **[Planning templates and examples](planning/)** — five levels from vision to feature: vision,
  product strategy, roadmap, a backlog of feature folders, a README for each feature. Plus ready-made
  agent prompts for each step and four filled-in examples for the course project tracks.
  The point is that the project's idea lives in the repository, not in a conversation with an agent, and that
  features can be worked on in separate terminals without getting in each other's way.
- **[How to connect this to an agent](planning/README.md#how-to-connect-it-to-the-agent)** — a ready-made block
  for `CLAUDE.md`, `AGENTS.md` or `.cursor/rules`: a pointer to the plan files with a condition for when to
  read them. The plan's contents are not put into the agent's rules, otherwise you pay for them in context
  on every task, including those where no product decisions are made.

Not tied to a module: useful from the first week until the defense.

### Additional slides

- **[Prompting best practices](other-slides/)** — a breakdown of prompting for a coding agent:
  five elements of a prompt, five ways to give context, constraints and verification, dosing
  the task, eight anti-patterns. Same self-contained HTML: download it and open it with a double click.

Outside the module program: not tied to the homework of a specific module.

## How to use this

The skeleton and fixtures are a starting point, not a solution to the assignment. The tools contract, the rules for
validating status transitions and the test scenario are yours to design: that is the work itself.

The homework texts live here, in `M{N}/homework.md`, — this is the source of truth; the version
in the LMS is synced with them. Theory is on the learning portal; here is what is more convenient to hand over
as files.
