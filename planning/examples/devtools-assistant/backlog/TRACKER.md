# Tracker — DevTools assistant

The single place to look at "what to take next". The status changes at the moment of the event,
not at the end of the day.

## Board

| # | Feature | Status | Waits for | Blocks | Wave |
|---|---|---|---|---|---|
| 1 | MCP over review tasks | `done` (03.08) | none | 3, 4 | 0 |
| 2 | Repository context | `in-build` | none | 3 | 0 |
| 3 | Three roles | `spec` | 1, 2 | 4 | 1 |
| 4 | End-to-end run | `backlog` | 1, 2, 3 | 5 | 2 |
| 5 | Risk routing | `backlog` | 4 | none | 3 |

A **wave** is a set of features that can be worked on at the same time. Wave 0 goes first, then
in numeric order. Features in the same wave do not depend on each other and do not write to the
same files.

## Critical path

`1 → 3 → 4 → 5`

Anything not on this path can be moved around. Here there is no slack on any feature: 3 starts
right after 2, and 4 depends on both.

## Rules for parallel terminals

1. One feature, one terminal, one owner. We do not write into another feature's folder.
2. Shared files (`schema.sql`, `pyproject.toml`, `.env.example`) are edited additively. Every
   edit is noted in the log below.
3. Commit only your own paths. Do not run `git add -A` from a feature terminal.
4. Commit the shared file in the same hour you edit it. An edit of `schema.sql` that lives only
   in the working copy is lost to any command from another terminal, and there is nowhere to
   restore it from.
5. Run `git pull --rebase` before pushing.
6. The status on the board is updated at four points: started working it out, accepted the spec,
   started the code, finished.

## Change log for shared files

| Date | Feature | What changed | What the others need to know |
|---|---|---|---|
| 31.07 | 1 | `schema.sql`: `findings` (JSON) and `risk_reason` added to `review_tasks` | Fields added, the fixture still loads. The fixture's `review_note` stays: it holds text for a human, while `findings` holds the structure for the roles |
| 01.08 | 2 | `schema.sql`: table `repo_chunks` | The file is shared, edited at the end. Recreate the database with the command from the README |
| 02.08 | 2 | `pyproject.toml`: added vector database and embedding dependencies | Terminal 1 needs to rebuild the environment |
| 03.08 | 1 | `schema.sql`: index on `status` and `score` | The queue is sorted by risk, without an index on 20 records there is no difference, but let it be |
