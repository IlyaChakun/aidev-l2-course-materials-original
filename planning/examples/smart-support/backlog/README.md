# Backlog — Smart support

One feature, one folder. Inside the folder `README.md` describes the whole feature, and as
work goes on `spec.md` and `plan.md` appear next to it.

Vision: [`../vision.md`](../vision.md) · Strategy: [`../strategy.md`](../strategy.md) ·
Roadmap: [`../roadmap.md`](../roadmap.md) · Statuses and rules for parallel work:
[`TRACKER.md`](TRACKER.md)

## Features

| # | Feature | What it does | Depends on | Status |
|---|---|---|---|---|
| 1 | [MCP over tickets](feature-1-mcp-tickets/) | Our own MCP server: the queue, writing an answer, status transitions with validation | none | `done` |
| 2 | [Solutions base](feature-2-solutions-corpus/) | Policies and solutions in a vector database, search by the text of a request | none | `in-build` |
| 3 | [Three roles](feature-3-agent-roles/) | Prompts for the Classifier, Support and Escalator, input and output contracts | 1, 2 | `spec` |
| 4 | [End-to-end run](feature-4-end-to-end/) | A ticket on input, a draft answer or an escalation on output | 1, 2, 3 | `backlog` |
| 5 | [Clarification and memory](feature-5-clarify-loop/) | A clarifying question when data is missing, taking the customer's earlier requests into account | 4 | `backlog` |

**Statuses:** `backlog` (described, not started) · `spec` (being worked out) · `in-build`
(code is being written) · `done` (works and is checked) · `blocked` (waiting on something
external, with what exactly in parentheses)

## Order of work

```
  1 MCP over tickets ──┐
  2 Solutions base ────┤   (1 and 2 are independent, ran in parallel)
        3 Three roles ─┘
             4 End-to-end run
                  5 Clarification and memory
```

The critical path goes through 1 → 3 → 4 → 5. Feature 2 is formally off to the side, but
first-line Support has nothing to answer with without it, so it must finish before 3 starts.

## What is still ahead

We will slice these after the end-to-end run works: for now it is unclear what to measure
quality on and how much one processing costs.

- Moving the roles to a framework: a graph of steps, state, retry of a failed step
- Quality check: a labeled set of tickets, share of correct categories, share of accepted answers
- Cost and security: the price of processing, limits, instructions inside the text of a request
- Demo: a five-minute scenario
