# 1 · MCP over sources

**Status:** `done` (02.08) · **Waiting for:** none · **Blocks:** 3, 4

## What it does

Our own MCP server over the `sources` table. An agent from the IDE sees the collected items,
sets a usefulness rating, writes a summary and moves a source through the statuses. The
lifecycle rules live in the server: an unrated item cannot be summarized.

## Why

The single door to the sources for all the other parts. It is also protection against the
main error of the run: summarizing is expensive, and it must be technically impossible to
launch it on an unrated item.

## Input and output

| | |
|---|---|
| **Input** | SQLite with the track fixture loaded: table `sources`, 20 records |
| **Output** | An MCP server in TypeScript: 5 tools, a resource with the database schema, the template `db://source/{id}`. A rejection on an invalid transition, with the current status and the allowed ones |

Tools: `list_sources`, `get_source`, `set_score`, `write_summary`, `advance_status`.

## Boundaries

- Collecting items from feeds and channels: not included, that is the Collector's job in
  feature 3.
- Sending the digest: not included, that is feature 4.
- Search over the archive: not included, that is feature 2.
- Deleting sources: not included, there is no scenario for it.

## Done when

- [x] The server starts with one command and is visible in MCP Inspector
- [x] `list_sources` with a filter by status and topic matches a `SELECT` on the database
- [x] `advance_status` takes `collected` → `rated` → `summarized`
- [x] An attempt at `collected` → `summarized` is rejected, and the response lists the allowed ones
- [x] `write_summary` for a source in the `collected` status is rejected
- [x] `set_score` outside the range 0-100 is rejected before writing to the database
- [x] An agent from the IDE takes a source through the cycle without hints about statuses in the prompt

## Read before starting

- `M1/starter-server/typescript/README.md` in the course repository: the skeleton and the
  package version fork
- `M1/fixtures/knowledge-curator/` in the course repository: schema and data
- `M1/guides/tool-design.md` in the course repository: the set of tools and the error contract
- `../../roadmap.md`, block 1

## Open questions

- Closed 01.08: can an item that is already in `rated` be re-rated. We decided it can,
  `set_score` is allowed in the `collected` and `rated` statuses. Feature 5 will need this.
- Remaining: `set_score` does not store who set the rating and why. Preference memory in
  feature 5 will need the reason, the `rating_reason` field is added, but the server does not
  write it.
- The unique index on `url` was added 02.08. The Collector must handle the insert conflict,
  this is recorded in the tracker.
