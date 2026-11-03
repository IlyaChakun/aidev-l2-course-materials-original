# Backlog — DevTools assistant

One feature, one folder. Inside the folder `README.md` describes the whole feature, and as work
progresses `spec.md` and `plan.md` appear next to it.

Vision: [`../vision.md`](../vision.md) · Strategy: [`../strategy.md`](../strategy.md) ·
Roadmap: [`../roadmap.md`](../roadmap.md) · Statuses and rules for parallel work:
[`TRACKER.md`](TRACKER.md)

## Features

| # | Feature | What it does | Depends on | Status |
|---|---|---|---|---|
| 1 | [MCP over review tasks](feature-1-mcp-review-tasks/) | Our own MCP server: the queue, recording comments, status transitions with validation | none | `done` |
| 2 | [Repository context](feature-2-repo-context/) | Conventions, decisions and past discussions in a vector database, search by changed file | none | `in-build` |
| 3 | [Three roles](feature-3-agent-roles/) | Prompts of the Reviewer, Tester and Documenter, input and output contracts | 1, 2 | `spec` |
| 4 | [End-to-end run](feature-4-end-to-end/) | A change goes in, comments, tests and documentation come out | 1, 2, 3 | `backlog` |
| 5 | [Risk routing](feature-5-risk-routing/) | A second round for risky changes, per-file memory between runs | 4 | `backlog` |

**Statuses:** `backlog` (described, not started) · `spec` (being worked out) · `in-build` (code
is being written) · `done` (works and is verified) · `blocked` (waiting for something external,
with the specifics in parentheses)

## Order of work

```
  1 MCP over review tasks ──┐
  2 Repository context ─────┤   (1 and 2 are independent, ran in parallel)
        3 Three roles ──────┘
             4 End-to-end run
                  5 Risk routing
```

The critical path goes through 1 → 3 → 4 → 5. Feature 2 is off to the side, but without it the
Reviewer analyzes changes without knowing the project's conventions and issues general-form
comments.

## What is still ahead

We will slice these once the end-to-end run works. Right now it is unclear on which set of
changes to measure quality: this is the first of the open questions in the roadmap.

- Moving the roles to a framework: a graph of steps, state, retry of a failed step
- Quality evaluation: changes with known defects, the share found, the share of false comments
- Cost and security: the price of an analysis, limits, instructions in code comments
- Demo: a five-minute scenario
