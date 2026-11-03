# 5 · Rework and memory

**Status:** `backlog` · **Waits for:** 4 · **Blocks:** none

## What it does

Adds a return path to the run. If the Fact checker found serious comments, the draft goes back to
the Writer together with them, and the pass is repeated. Between rounds it is saved what has
already been fixed, so that the Writer does not rewrite the same thing and the Fact checker does
not repeat a closed comment.

## Why

Without this the system is linear and demands a human at the first disputed fact. It is also the
first place where state appears: without memory of the previous round the agents go in circles
and produce the same result on every pass.

## Input and output

| | |
|---|---|
| **Input** | The working end-to-end run from feature 4 |
| **Output** | A rework loop with a limit on the number of rounds. A round history in the database: what was flagged, what was fixed, what remains. The article goes to a human if the round limit is exhausted |

## Boundaries

- Branching by topics and sections: out of scope, there is one route.
- Long-lived memory across different articles: out of scope, state lives within one.
- A separate arbiter role resolving a dispute between the Writer and the Fact checker: out of
  scope, a dispute is resolved by the round limit.

## Done when

- [ ] An article with a serious comment goes to a second round automatically
- [ ] In the second round the Writer receives the comments from the first and the text it edited
- [ ] A comment closed in the first round is not repeated in the second
- [ ] When the round limit is exhausted the article stays in `draft` with the note "human needed"
- [ ] The round history is visible with a database query, and the course of work can be reconstructed from it
- [ ] A run with no comments still finishes in one round and has not slowed down

## Read before starting

- `../feature-4-end-to-end/README.md`: how the linear pass is built
- `../feature-3-agent-roles/README.md`: the comment format and the severity grades
- `../../roadmap.md`, block 5

## Open questions

- **Round limit.** The hypothesis is two, with no justification. Decide from data after the
  first runs.
- **History storage.** A separate table or a JSON field in `articles`. A separate table looks
  more correct, but it brings a migration with it, and that has to be agreed with the feature 2
  terminal.
- A debt is hanging over from feature 1: `update_body` overwrites the whole text, but here we
  need versions.
