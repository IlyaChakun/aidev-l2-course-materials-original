# Tracker — Knowledge curator

The only place where you look for "what to pick up next". The status is changed at the moment
of the event, not at the end of the day.

## Board

| # | Feature | Status | Waiting for | Blocks | Wave |
|---|---|---|---|---|---|
| 1 | MCP over sources | `done` (02.08) | none | 3, 4 | 0 |
| 2 | Archive and search | `in-build` | none | 3 | 0 |
| 3 | Three roles | `spec` | 1, 2 | 4 | 1 |
| 4 | Daily run | `backlog` | 1, 2, 3 | 5 | 2 |
| 5 | Preference memory | `backlog` | 4 | none | 3 |

A **wave** is a set of features that can be worked on at the same time. Wave 0 goes first,
then by number. Features in the same wave do not depend on each other and do not write to the
same files.

## Critical path

`1 → 3 → 4 → 5`

Feature 5 hinges on the open question from the roadmap about how the reader reacts to the
digest. Until it is closed, the feature cannot even be described properly, and this is the
main risk to the deadline.

## Rules for parallel terminals

1. One feature, one terminal, one owner. We do not write into another feature's folder.
2. Shared files (`schema.sql`, `package.json`, `.env.example`) are edited additively. Every
   edit is noted in the log below.
3. We commit only our own paths. We do not run `git add -A` from a feature terminal.
4. A shared file is committed in the same hour it is edited.
5. `git pull --rebase` before pushing.
6. The status on the board is updated at four points: started working it out, accepted the
   spec, started the code, finished.

## Change log for shared files

| Date | Feature | What changed | What the others need to know |
|---|---|---|---|
| 30.07 | 1 | `schema.sql`: `collected_at` and `rating_reason` added to `sources` | The fields are added, the fixture loads as before |
| 01.08 | 2 | `schema.sql`: table `archive_chunks` | The file is shared, edits go at the end |
| 02.08 | 1 | `schema.sql`: unique index on `url` | The Collector in feature 3 must catch the insert conflict, not crash |
| 04.08 | 2 | `package.json`: vector database client and embedding model | The first terminal needs `npm ci` before the next run |
