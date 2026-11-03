# Knowledge curator — product strategy

> Updated: 04.08.2026 · Vision: [`vision.md`](vision.md) · Roadmap: [`roadmap.md`](roadmap.md)

## Who it is for

One person, seven topics of interest, twenty-four feeds and nine open channels, about a
hundred new items a day and forty minutes for reading. Today they skim the headlines by hand
and put half of them off with no return.

## What it is and what it is not

**It is:** a daily selection and summarization by personal topics that learns from the
reactions of a single reader.

**It is not:** a feed reader (they already see the feed, the value is in the filtering), not a
shared news service (the preference memory of one person does not scale to many) and not an
archive with search (here the archive is an internal mechanism for finding duplicates).

## Stage

Prototype, launched manually. By the defense a working daily run on a schedule is needed,
one that has run several days in a row without intervention.

## Current priorities

1. Filtering. Out of a hundred items seven to ten must remain, otherwise the tool does not
   solve the original problem.
2. Collapsing duplicates by meaning. One story arrives from five sources, and without this
   half of the digest will be repeats.
3. A scheduled run without a human. Until this point the tool is no different from manual
   reading.
4. Preference memory. It pays off later than the rest, but without it the quality of
   selection does not grow over time.

## Decisions made

| Date | Decision | Why |
|---|---|---|
| 30.07 | Take the track as is | Statuses and fields are ready, time goes into the system |
| 30.07 | TypeScript and SQLite | The tool is personal and single-user, a separate DBMS adds nothing |
| 31.07 | Rating and summarizing are different roles | Summarizing a hundred items is expensive. Filtering first, summarizing only for those that pass |
| 01.08 | Filter by number of items, not by rating threshold | A threshold gives either an empty digest or one with forty items. A fixed number is predictable |
| 03.08 | Find duplicates by meaning, not by link | The same story arrives from five sources with different links |
| 04.08 | Public sources only, nothing that requires logging in to an account | Scraping closed content adds risks and work, and has nothing to do with the point of the project |

## Risks

| Risk | What we do |
|---|---|
| Topic descriptions are vague, and the Rater's ratings have nothing to defend them | Rewrite the descriptions in more detail or add examples of items that definitely fit and definitely do not |
| The duplicate-merging threshold merges different stories on one topic | Tune it on five variants of one story, check both sides of the error |
| In the first days the archive is empty and the duplicate check does not work | Make sure the run does not crash on an empty index. After that it is cured by time |
| Items behind a paywall pile up and are never summarized | Mark them separately, decide whether to show them as a list without a summary |

## Hypotheses to check

- Of a hundred items a day, fewer than ten are really useful. Checked by: manual labeling of
  a hundred items in the quality-check block.
- The reader's reaction to the digest improves selection within two weeks. Checked by: a
  report on how ratings changed by topic in feature 5.
- Following a link is a more honest interest signal than a button. Checked by: comparing the
  two approaches, if we get round to it. It is not yet decided how the reader reacts at all.

## What this file does not contain

Architecture and diagrams, the list of features and deadlines, the history of discussions,
current metric values.
