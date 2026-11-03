# 4 · End-to-end run

**Status:** `backlog` · **Waits for:** 1, 2, 3 · **Blocks:** 5

## What it does

Connects the three roles into one pass. A change goes in, then the Reviewer writes comments, the
Tester prepares tests, the Documenter updates docstrings and the README. The output is a task in
the `tested` status with three artifacts. There are no repeats or branching here.

This is also where we decide where the diff comes from: the fixture gives only a textual
description of the change, but on a live repository a real one is needed.

## Why

The first point where the system works as a whole, and the first where it becomes visible that the
Tester lacks what the Reviewer produces, and the Documenter lacks both.

## Input and output

| | |
|---|---|
| **Input** | Three debugged roles, the MCP server, search over the repository context |
| **Output** | The command `python -m pipeline --task <id>`: the task is processed, the status is changed, comments are in the database, tests and documentation edits are in `out/`. A log of the pass with the time of each step |

## Boundaries

- A second round for risky changes: out of scope, that is feature 5.
- Processing several tasks in a batch: out of scope.
- Applying the edits to the repository: out of scope, everything is put into `out/`.
- Restarting from the middle after a failure: out of scope.

## Done when

- [ ] A fixture task goes through to the `tested` status with no manual intervention
- [ ] A run on ten tasks finishes without failures
- [ ] The diff is taken from the repository, not from the fixture's text field
- [ ] A failure of any role leaves the task in the previous status
- [ ] The artifacts of the three roles are in `out/` and relate to the same change
- [ ] The log shows the time of each role and the number of search calls

## Read before starting

- `../feature-3-agent-roles/README.md`: the role contracts
- `../feature-1-mcp-review-tasks/README.md`: the allowed transitions
- `../../roadmap.md`, block 4

## Open questions

- Changes over a thousand lines do not fit in the context. An open question from the roadmap,
  here it becomes blocking: we need either to split by files or to refuse with a clear error.
