# Backlog — Knowledge curator

One feature, one folder. Inside the folder `README.md` describes the whole feature, and as
work goes on `spec.md` and `plan.md` appear next to it.

Vision: [`../vision.md`](../vision.md) · Strategy: [`../strategy.md`](../strategy.md) ·
Roadmap: [`../roadmap.md`](../roadmap.md) · Statuses and rules for parallel work:
[`TRACKER.md`](TRACKER.md)

## Features

| # | Feature | What it does | Depends on | Status |
|---|---|---|---|---|
| 1 | [MCP over sources](feature-1-mcp-sources/) | Our own MCP server: reading what has been collected, rating, status transitions with validation | none | `done` |
| 2 | [Archive and search](feature-2-archive-search/) | Summarized items in a vector database, a "have we written about this before" check | none | `in-build` |
| 3 | [Three roles](feature-3-agent-roles/) | Prompts for the Collector, Rater and Summarizer, input and output contracts | 1, 2 | `spec` |
| 4 | [Daily run](feature-4-daily-digest/) | One launch a day: collection, filtering, summary, delivery | 1, 2, 3 | `backlog` |
| 5 | [Preference memory](feature-5-taste-memory/) | A reaction to the digest influences the next day's ratings | 4 | `backlog` |

**Statuses:** `backlog` (described, not started) · `spec` (being worked out) · `in-build`
(code is being written) · `done` (works and is checked) · `blocked` (waiting on something
external, with what exactly in parentheses)

## Order of work

```
  1 MCP over sources ────┐
  2 Archive and search ──┤   (1 and 2 are independent, ran in parallel)
        3 Three roles ───┘
             4 Daily run
                  5 Preference memory
```

The critical path goes through 1 → 3 → 4 → 5. Feature 2 is needed by the Rater: without it the
same story from five sources will get into the digest five times.

## What is still ahead

We will slice these after the daily run. There is no point earlier: it is unclear what to
measure and how much a run costs.

- Moving the roles to a framework: a graph of steps, state, retry of a failed step
- Quality check: a hundred labeled items, divergence from the system's rating, traces
- Cost and security: the price of a run, limits, instructions inside the text of an item
- Demo: a five-minute scenario
