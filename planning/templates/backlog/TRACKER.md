<!--
TRACKER TEMPLATE.

Needed when there are more than five features or when you keep several terminals going at
once. With three features and one terminal, do not create this file: the status column in the
backlog README is enough, and two tables of which only one is maintained are worse than one.

The file answers two questions: what can be picked up right now and by which rules the
parallel terminals work.

Delete this comment when the file is filled in.
-->

# Tracker — <project name>

The only place where you look for "what to pick up next". The status is changed at the moment
of the event, not at the end of the day.

## Board

| # | Feature | Status | Waiting for | Blocks | Wave |
|---|---|---|---|---|---|
| 1 | <name> | `backlog` | none | 2, 3 | 0 |
| 2 | <name> | `backlog` | 1 | 4 | 1 |
| 3 | <name> | `backlog` | 1 | 4 | 1 |
| 4 | <name> | `backlog` | 2, 3 | none | 2 |

A **wave** is a set of features that can be worked on at the same time. Wave 0 goes first,
then by number. Features in the same wave do not depend on each other and do not write to the
same files.

## Critical path

`<1 → 2 → 4 → ...>`

<One phrase: what happens to the deadline if one of these features stalls. Everything that
is not on the critical path can be moved. Everything on it cannot.>

## Rules for parallel terminals

1. One feature, one terminal, one owner. We do not write into another feature's folder: if
   you need something from a neighboring feature, it goes through a row in this file, not by
   editing its files.
2. Shared files (database schema, config, dependencies) are edited additively: you added
   your part, you did not rewrite anyone else's. Every edit to a shared file is noted in the
   log below.
3. We commit only our own paths. We do not run `git add -A` from a feature terminal: it
   would pick up someone else's unfinished work.
4. A shared file is committed in the same hour it is edited. An unsaved edit to a shared file
   lives only in the working copy, and any other command will wipe it without a trace.
5. `git pull --rebase` before pushing. There are several terminals, and history diverges fast.
6. The status on the board is updated at four points: started working it out, accepted the
   spec, started the code, finished.

## Change log for shared files

<Written at the end, old entries are not edited. Read before touching a shared file: it is
cheaper to read five lines than to find out why a neighbor's build stopped working.>

| Date | Feature | What changed | What the others need to know |
|---|---|---|---|
| <DD.MM> | <#> | <file and the gist of the edit> | <what will break if it is not taken into account> |
