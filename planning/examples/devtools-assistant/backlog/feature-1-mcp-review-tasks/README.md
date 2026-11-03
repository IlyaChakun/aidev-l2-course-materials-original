# 1 · MCP over review tasks

**Status:** `done` (03.08) · **Waits for:** none · **Blocks:** 3, 4

## What it does

Our own MCP server over the `review_tasks` table. The agent from the IDE sees the queue, reads
the description of the change, writes comments and moves the task through statuses. The lifecycle
rules live in the server: skipping the review and marking a change as verified straight away is
not possible.

## Why

The single door to the review queue for all the other parts. The rule "what has not passed
`reviewed` cannot be marked `tested`" must be in one place, otherwise the three roles will
interpret it differently.

## Input and output

| | |
|---|---|
| **Input** | SQLite with the track fixture loaded: table `review_tasks`, 20 records |
| **Output** | An MCP server in Python: 5 tools, a resource with the database schema, the template `db://review-task/{id}`. A rejection on an invalid transition with the current status and the list of allowed ones |

Tools: `list_tasks`, `get_task`, `write_findings`, `advance_status`, `set_risk`.

## Boundaries

- Working with git and obtaining the diff: out of scope. The server returns `diff_summary` from
  the database and does not reach into the repository.
- Comments in the pull request: out of scope and not planned.
- Generating tests and documentation: out of scope, that is feature 3.
- Repository indexing: out of scope, that is feature 2.

## Done when

- [x] The server starts with one command and is visible in MCP Inspector
- [x] `list_tasks` with a status filter matches a `SELECT` on the database
- [x] The queue is sorted by `score` in descending order, risky ones on top
- [x] `advance_status` takes `queued` → `reviewed` → `tested`
- [x] An attempt at `queued` → `tested` is rejected, the response lists the allowed transitions
- [x] `write_findings` into a task in the `queued` status is rejected: first the transition, then the comments
- [x] The agent from the IDE takes a task through the cycle without hints about statuses in the prompt

## Read before starting

- `M1/starter-server/python/README.md` in the course repository: the skeleton we started from
- `M1/fixtures/devtools-assistant/` in the course repository: schema and data
- `M1/guides/tool-design.md` in the course repository: the tool set and the error contract
- `../../roadmap.md`, block 1

## Open questions

- Closed 02.08: whether `reviewed` can be returned back to `queued`. We decided it can: the
  author adds more changes and the task goes back into the queue. Recorded in the roadmap.
- Remaining: `write_findings` accepts the whole list of comments and overwrites the previous one.
  With the second round in feature 5 we will need to append rather than replace.
- `diff_summary` in the fixture is text, but a real change needs a real diff. Where it comes
  from is decided in feature 4.
