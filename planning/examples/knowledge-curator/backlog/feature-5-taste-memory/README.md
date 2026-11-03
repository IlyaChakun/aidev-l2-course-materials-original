# 5 · Preference memory

**Status:** `backlog` · **Waiting for:** 4 · **Blocks:** none

## What it does

Teaches the system from the reader's reactions. What they opened, what they skipped, what they
marked as unneeded goes into memory and influences the next day's ratings. Between runs the
system remembers which topics and sources are consistently not read.

## Why

Without this the system gives the same quality of selection for the whole month. It is also
the only place in the project where state lives longer than one run: the other features start
each launch from a clean slate.

## Input and output

| | |
|---|---|
| **Input** | The working daily run from feature 4 |
| **Output** | Collection of reactions, preference memory in the database, use of the memory in the Rater's rating. A report on how ratings by topic changed over two weeks |

## Boundaries

- Fine-tuning the model: we do not do it. Memory is data in the context, not weights.
- Memory by authors and publications: not included, memory is by topics and sources.
- Manual tuning of weights by the reader: not included.
- Completely dropping a topic: not included, the rating is lowered, but the topic is not
  switched off.

## Done when

- [ ] A reaction to the digest reaches the database and is attached to the item
- [ ] The Rater receives the memory in its context, and this is visible in the reason for the rating
- [ ] A topic whose items were not opened for two weeks gets noticeably lower ratings, and this
      is visible in the report
- [ ] A source that the reader marked as unneeded stops getting into the digest
- [ ] The absence of reactions does not break the run: without memory the system works as before
- [ ] The memory is visible through a database query, and it can be used to reconstruct why a rating changed

## Read before starting

- `../feature-4-daily-digest/README.md`: how the daily run is built
- `../feature-3-agent-roles/README.md`: the format of the rating and the reason
- `../../roadmap.md`, block 5

## Open questions

- **How the reader reacts.** Buttons under the message, a text reply or following a link. An
  open question from the roadmap, and until it is closed the feature cannot be properly
  described. This is the first thing to decide at the start.
- **Following a link as a signal.** It is the most honest and the hardest: it needs its own
  redirect, and that is a separate piece of work. Perhaps defer it to "Later".
- **How quickly the memory should forget.** Interest changes, and an eternal memory will keep
  ratings for topics that stopped being relevant long ago.
- A debt hangs over from feature 1: `set_score` does not write the reason for the rating, and
  here it is needed.
