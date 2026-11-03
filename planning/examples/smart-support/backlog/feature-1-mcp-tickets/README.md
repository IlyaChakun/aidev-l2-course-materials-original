# 1 · MCP over tickets

**Status:** `done` (02.08) · **Waiting for:** none · **Blocks:** 3, 4

## What it does

Our own MCP server over the `tickets` table. An agent from the IDE sees the queue, reads a
request, writes an answer and moves a ticket through the statuses. The lifecycle rules live in
the server: you cannot move `answered` back to `new`, and you cannot write an answer into an
already escalated ticket either.

## Why

The single door to the tickets for all the other parts of the system. If each role goes to the
database on its own, the rule "you cannot answer an escalated ticket" has to be repeated three
times, and the third time someone will forget it.

## Input and output

| | |
|---|---|
| **Input** | PostgreSQL with the track fixture loaded: table `tickets`, 20 records |
| **Output** | An MCP server in TypeScript: 5 tools, a resource with the database schema, the template `db://ticket/{id}`. A rejection on an invalid transition, naming the current status and the allowed ones |

Tools: `list_tickets`, `get_ticket`, `set_classification`, `write_answer`, `advance_status`.
`set_classification` writes the category and urgency into `score`, escalation goes through
`advance_status` with context for the engineer.

## Boundaries

- Accepting new requests from outside: not included, the tickets are already in the database.
- Sending the answer to the customer: not included and not planned.
- Search by the text of requests: not included, filtering by status, channel and urgency.
- Working with the solutions base: not included, that is feature 2.

## Done when

- [x] The server starts with one command and is visible in MCP Inspector
- [x] `list_tickets` with a filter by status returns the same number as a `SELECT` on the database
- [x] The queue is sorted by `score` in descending order, and this is visible on the fixture data
- [x] `advance_status` takes `new` → `answered` and `new` → `escalated`
- [x] An attempt at `answered` → `new` is rejected, and the response lists the allowed transitions
- [x] `write_answer` into an escalated ticket is rejected
- [x] An agent from the IDE processes a ticket without hints about statuses in the prompt

## Read before starting

- `M1/starter-server/typescript/README.md` in the course repository: the skeleton we started
  from, and the package version fork
- `M1/fixtures/smart-support/` in the course repository: schema and data
- `M1/guides/tool-design.md` in the course repository: the set of tools and the error contract
- `../../roadmap.md`, block 1

## Open questions

- Closed 01.08: can a ticket be escalated from `answered`. We decided it can: an answer may
  be wrong, and the path `answered` → `escalated` is allowed.
- Remaining: the transition to `escalated` accepts the context as a single text field. When
  the Escalator in feature 3 starts assembling structured context, the field will have to be
  parsed. Noted so as not to forget.
- Closed 04.08: whether to add a separate urgency field. We do not, urgency is `score` from the
  fixture. The threshold is moved into the config, the decision of 04.08 in the roadmap.
