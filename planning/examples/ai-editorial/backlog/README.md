# Backlog — AI editorial desk

One feature, one folder. Inside the folder `README.md` describes the whole feature, and as work
progresses `spec.md` and `plan.md` appear next to it.

Vision: [`../vision.md`](../vision.md) · Strategy: [`../strategy.md`](../strategy.md) ·
Roadmap: [`../roadmap.md`](../roadmap.md) · Statuses and rules for parallel work:
[`TRACKER.md`](TRACKER.md)

## Features

| # | Feature | What it does | Depends on | Status |
|---|---|---|---|---|
| 1 | [MCP over articles](feature-1-mcp-articles/) | Our own MCP server: reading articles, creating a draft, status transitions with validation | none | `done` |
| 2 | [Editorial policy corpus](feature-2-style-corpus/) | Editorial policy documents in a vector database, search for applicable rules by a fragment of text | none | `in-build` |
| 3 | [Three roles](feature-3-agent-roles/) | System prompts of the Writer, Fact checker and SEO specialist, input and output contracts | 1, 2 | `spec` |
| 4 | [End-to-end run](feature-4-end-to-end/) | A brief goes in, an article with meta tags and the `checked` status comes out | 1, 2, 3 | `backlog` |
| 5 | [Rework and memory](feature-5-rework-loop/) | Returning the draft to the Writer with comments, state between runs | 4 | `backlog` |

**Statuses:** `backlog` (described, not started) · `spec` (being worked out) · `in-build` (code
is being written) · `done` (works and is verified) · `blocked` (waiting for something external,
with the specifics in parentheses)

## Order of work

```
  1 MCP over articles ─┐
  2 Policy corpus ─────┤   (1 and 2 are independent, ran in parallel)
        3 Three roles ─┘
             4 End-to-end run
                  5 Rework and memory
```

The critical path goes through 1 → 3 → 4 → 5. Feature 2 is not directly on it, but without it the
Fact checker in feature 3 is left without rules and has nothing to check against.

## What is still ahead

Roadmap blocks we have not yet got around to slicing. We will slice them once the end-to-end run
works: right now it is unclear what exactly to check and how much it costs.

- Moving the roles to a framework: a graph of steps, state, retry of a failed step
- Quality evaluation: a set of articles with a known answer, automatic evaluation, traces
- Cost and security: the price of an article, a per-run limit, injections in source text
- Demo: a five-minute scenario
