# Tracker — AI editorial desk

The single place to look at "what to take next". The status changes at the moment of the event,
not at the end of the day.

## Board

| # | Feature | Status | Waits for | Blocks | Wave |
|---|---|---|---|---|---|
| 1 | MCP over articles | `done` (03.08) | none | 3, 4 | 0 |
| 2 | Editorial policy corpus | `in-build` | none | 3 | 0 |
| 3 | Three roles | `spec` | 1, 2 | 4 | 1 |
| 4 | End-to-end run | `backlog` | 1, 2, 3 | 5 | 2 |
| 5 | Rework and memory | `backlog` | 4 | none | 3 |

A **wave** is a set of features that can be worked on at the same time. Wave 0 goes first, then
in numeric order. Features in the same wave do not depend on each other and do not write to the
same files.

Features 1 and 2 ran in parallel in two terminals and did not collide: the first worked in
`mcp_server/`, the second in `retrieval/`. They share exactly one file, `docker-compose.yml`,
and it is in the log below.

## Critical path

`1 → 3 → 4 → 5`

A delay on any of these four moves the defense. Feature 2 is formally off to the side, but if it
is not finished before 3 starts, the Fact checker will have no source of rules, and feature 3
will have to be started twice.

## Rules for parallel terminals

1. One feature, one terminal, one owner. We do not write into another feature's folder: if
   something is needed from a neighboring feature, it goes through a line in this file, not by
   editing its files.
2. Shared files (`docker-compose.yml`, `.env.example`, the database schema) are edited
   additively: add your own, do not rewrite someone else's. Every edit of a shared file is noted
   in the log below.
3. Commit only your own paths. Do not run `git add -A` from a feature terminal.
4. Commit the shared file in the same hour you edit it.
5. Run `git pull --rebase` before pushing.
6. The status on the board is updated at four points: started working it out, accepted the spec,
   started the code, finished.

## Change log for shared files

| Date | Feature | What changed | What the others need to know |
|---|---|---|---|
| 31.07 | 1 | `docker-compose.yml`: added the `postgres` service, port 5432 | SQLite is no longer used. The connection string is in `.env.example` |
| 02.08 | 2 | `docker-compose.yml`: added the vector database service, port 6333 | The port is taken locally in the second terminal, overridden there via `.env` |
| 03.08 | 1 | Schema: `review_notes` (JSON) and `meta` (JSON) added to `articles` | Fields added, existing ones untouched. The fixture still loads |
| 04.08 | 2 | `.env.example`: embedding model variables | The default value is left empty, everyone sets their own |
