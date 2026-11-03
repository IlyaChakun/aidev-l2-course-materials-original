# DevTools assistant — roadmap

> Updated: 04.08.2026 · Vision: [`vision.md`](vision.md) · Strategy: [`strategy.md`](strategy.md) · Backlog: [`backlog/`](backlog/)

## What we are building

A first pass over a change by three roles: the Reviewer analyzes the diff and writes comments, the
Tester prepares tests for new functions, the Documenter updates the README and docstrings. For
whom and why exactly this way: [`vision.md`](vision.md) and [`strategy.md`](strategy.md).

## Data

| What | Where it lives | Volume | Access |
|---|---|---|---|
| Review tasks | SQLite, table `review_tasks` | 20 fixture records plus our own | Yes |
| Learning repository | Local clone | About 400 files | Yes |
| Conventions and review rules | Markdown in the same repository | 12 documents | Yes |
| Past reviews | Export of pull request discussions | 210 discussions | Yes, exported through the API |

## Functional map

1. **Access to review tasks.** Our own MCP server over the `review_tasks` table: the queue,
   recording comments, status transitions with validity checks.
2. **Repository context and search.** Conventions, architectural decisions and past discussions
   in a vector database. For a changed file, what is already known about it is returned.
3. **Three roles and their prompts.** Reviewer, Tester, Documenter. Each has its own input and
   its own output format.
4. **End-to-end run and the assembly architecture.** A change goes in, comments, tests and
   updated documentation come out. Linear. This is also where we decide how the parts are
   connected: what calls the roles, where a real diff comes from instead of the fixture text,
   where the review state lives and what remains if a step fails midway.
5. **Routing by risk and per-file memory.** A risky change goes through a second round. Between
   runs it is remembered what has already been reviewed in these files.
6. **Moving the roles to a framework.** The roles move from plain functions to a graph of steps:
   explicit review state, retry of a failed step, the two risk routes as a branch of the graph
   rather than an `if` in the run code.
7. **Quality evaluation.** A set of changes with known defects, the share found, the share of
   false comments, traces.
8. **Cost and security.** The price of analyzing one change, limits, behavior under an
   instruction embedded in a code comment.
9. **Demo.** Five minutes: a change, comments, tests, documentation, a second round on a risky
   one.

## What we honestly do not do

- Comments right in the pull request: not done, there will be no integration with the hosting.
- Running tests and checking that they pass: a stub, the decision is recorded in the strategy.
- Several repositories: not done, the `repository` field exists, but we work with one.
- Review in several languages: not done, one language.
- Automatic fixing of what is found: not done, comments only.

## Stages

| Stage | What works at the end of the stage | Deadline |
|---|---|---|
| 1 | The agent from the IDE reads the queue through the MCP server, writes comments and moves `queued` → `reviewed`. The transition `queued` → `tested` is rejected | Week 2 |
| 2 | For a changed file, search returns the applicable conventions and past discussions | Week 3 |
| 3 | A change goes in, comments and draft tests come out | Week 4 |
| 4 | A high-risk change goes through a second round, the repeat takes the first into account | Week 5 |
| 5 | On a set of changes with known defects, the share found and the share of false comments are known | Week 6 |
| 6 | The price of an analysis is known, a limit is set, an instruction in a code comment is not executed | Week 7 |

## Open questions

- **What counts as a defect in the quality evaluation.** We need a set of changes with problems
  known in advance. Assemble it by hand or take it from the history where a review found a
  problem. Not decided, close before the quality evaluation block.
- **Granularity of per-file memory.** File, function or directory. It affects the volume of what
  is stored and how useful it is.
- **What to do with changes where the diff is over a thousand lines.** Right now such changes do
  not fit in the context. Split by files or refuse, not decided.

## Later

- Running the generated tests and discarding those that fail.
- A second repository and different conventions.
- Tracking which comments the author accepted and which they rejected.
