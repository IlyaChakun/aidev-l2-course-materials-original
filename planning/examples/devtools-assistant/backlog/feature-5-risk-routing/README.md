# 5 · Risk routing

**Status:** `backlog` · **Waits for:** 4 · **Blocks:** none

## What it does

Adds branching to the run. A high-risk change goes through a second round: the Reviewer rereads
it taking into account its own comments from the first round and what was already reviewed in
these files earlier. A low-risk change goes through once, on the short path.

On top of that, per-file memory appears: the system remembers which comments were already issued
for this place and what the author did with them.

## Why

Without branching all changes are processed the same way, and fixing a typo costs as much as
changing authorization. Per-file memory is needed so as not to issue for the third time a comment
that the author has rejected twice.

## Input and output

| | |
|---|---|
| **Input** | The working end-to-end run from feature 4 |
| **Output** | Two run routes with a risk threshold. Per-file memory in the database: what was flagged, when, what the author did. A second round that takes the first into account |

## Boundaries

- Learning the threshold from data: out of scope, the threshold is a number in the config.
- Per-author memory: out of scope, memory is per file only.
- More than two rounds: out of scope.
- A separate arbiter role: out of scope.

## Done when

- [ ] A change with risk above the threshold goes through two rounds, below the threshold one
- [ ] In the second round the Reviewer sees its own first-round comments and does not repeat them verbatim
- [ ] A comment previously rejected by the author for this file is not issued again
- [ ] The per-file memory is visible with a database query
- [ ] The short route is noticeably faster and cheaper than the long one, the difference is visible in the log
- [ ] A run on ten tasks produces both routes, not just one

## Read before starting

- `../feature-4-end-to-end/README.md`: how the linear pass is built
- `../feature-3-agent-roles/README.md`: the comment format and severity
- `../../roadmap.md`, block 5

## Open questions

- **Memory granularity.** File, function or directory. An open question from the roadmap, here
  it will have to be closed.
- **Risk threshold.** The value is unknown. Pick it from the data of the first runs, and until
  then take the middle of the scale and write down that it was taken at random.
- **Where "the author rejected the comment" comes from.** The system has no feedback from the
  author. Either by hand, or this item moves to "Later".
- A debt is hanging over from feature 1: `write_findings` overwrites the list of comments, but
  the second round needs to append.
