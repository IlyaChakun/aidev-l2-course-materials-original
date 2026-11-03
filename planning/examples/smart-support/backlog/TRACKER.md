# Tracker — Smart support

The only place where you look for "what to pick up next". The status is changed at the moment
of the event, not at the end of the day.

## Board

| # | Feature | Status | Waiting for | Blocks | Wave |
|---|---|---|---|---|---|
| 1 | MCP over tickets | `done` (02.08) | none | 3, 4 | 0 |
| 2 | Solutions base | `in-build` | none | 3 | 0 |
| 3 | Three roles | `spec` | 1, 2 | 4 | 1 |
| 4 | End-to-end run | `backlog` | 1, 2, 3 | 5 | 2 |
| 5 | Clarification and memory | `backlog` | 4 | none | 3 |

A **wave** is a set of features that can be worked on at the same time. Wave 0 goes first,
then by number. Features in the same wave do not depend on each other and do not write to the
same files.

## Critical path

`1 → 3 → 4 → 5`

A delay on any of the four shifts the defense. Only feature 2 has slack, and it is already
used up: the chunking of the policies was redone twice.

## Rules for parallel terminals

1. One feature, one terminal, one owner. We do not write into another feature's folder: if
   you need something from a neighboring feature, it goes through a row in this file.
2. Shared files (`docker-compose.yml`, `.env.example`, migrations) are edited additively.
   Every edit is noted in the log below.
3. We commit only our own paths. We do not run `git add -A` from a feature terminal.
4. A shared file is committed in the same hour it is edited.
5. `git pull --rebase` before pushing.
6. The status on the board is updated at four points: started working it out, accepted the
   spec, started the code, finished.

## Change log for shared files

| Date | Feature | What changed | What the others need to know |
|---|---|---|---|
| 30.07 | 1 | Migration `001_init`: the fixture plus an index on `status` | Data loading is now through migrations, not through `psql -f` |
| 01.08 | 1 | Migration `002`: `category` and `escalation_context` added to `tickets` | Fields added, existing ones untouched. Urgency lives in `score` from the fixture |
| 02.08 | 2 | `docker-compose.yml`: a vector database service | The second terminal needs to rebuild the environment before running |
| 03.08 | 2 | Migration `003`: table `corpus_chunks` for document metadata | Does not overlap with `tickets`, but migrations are numbered continuously, the next number is 004 |
| 04.08 | 1 | `.env.example`: `URGENCY_THRESHOLD` added, the urgency threshold is read from the config | We take the threshold from the config, not from the prompt. It is compared with `score`, scale 0-100 |
