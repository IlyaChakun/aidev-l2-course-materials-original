# 4 · End-to-end run

**Status:** `backlog` · **Waiting for:** 1, 2, 3 · **Blocks:** 5

## What it does

Connects the three roles into one pass. A ticket on input, then the Classifier sets the
category and urgency, Support looks for a solution and prepares a draft, on a refusal the
Escalator joins. On output the ticket is in the `answered` status with a draft or in the
`escalated` status with context for the engineer. There are no clarifications or retries here.

## Why

The first point where the system works as a whole. A linear pass is needed before
clarifications, because it exposes mismatches between the role contracts, and fixing them is
cheaper before branches appear.

## Input and output

| | |
|---|---|
| **Input** | Three debugged roles, the MCP server, search over the solutions base |
| **Output** | The command `npm run pipeline -- --ticket <id>`: the ticket is processed, the status changed, the result recorded. A log of the pass with the time of each step |

## Boundaries

- Clarifying questions: not included, that is feature 5.
- Processing the whole queue in a batch: not included, one ticket at a time.
- Restart from the middle after a failure: not included.
- Interface: not included, launch from the command line.

## Done when

- [ ] A ticket from the fixture is processed to a final status without manual intervention
- [ ] A run on ten different tickets goes through without crashes
- [ ] A ticket that the first line did not close reaches `escalated` with the context filled in
- [ ] A failure of any role leaves the ticket in `new`, not in an intermediate state
- [ ] The log shows the time of each role and the number of calls to search

## Read before starting

- `../feature-3-agent-roles/README.md`: the role contracts
- `../feature-1-mcp-tickets/README.md`: the allowed transitions
- `../../roadmap.md`, block 4

## Open questions

- What to do with a ticket on which the Classifier set the missing-data flag, while
  clarifications do not exist yet. Hypothesis: escalate. Clarify at the start.
