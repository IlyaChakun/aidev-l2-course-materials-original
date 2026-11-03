# Knowledge curator — roadmap

> Updated: 04.08.2026 · Vision: [`vision.md`](vision.md) · Strategy: [`strategy.md`](strategy.md) · Backlog: [`backlog/`](backlog/)

## What we are building

A daily run of three roles: the Collector picks up new items from the subscriptions, the Rater
filters out noise and repeats, the Summarizer writes the digest. For whom and why it is done
this way: [`vision.md`](vision.md) and [`strategy.md`](strategy.md).

## Data

| What | Where it lives | Volume | Access |
|---|---|---|---|
| Sources | SQLite, table `sources` | 20 fixture records plus whatever is collected | Available |
| Feeds | 24 RSS | About 60 new items a day | Available |
| Open channels | 9 channels | About 40 messages a day | Available |
| Archive of what has been read | The same table, status `summarized` | Grows as we go | Available |
| Topics of interest | One file | 7 topics with a description | Available |

## Functional map

1. **Access to sources.** Our own MCP server over the `sources` table: reading what has been
   collected, setting a rating, status transitions with validity checks.
2. **Archive and search over it.** Items that have already been summarized, in a vector
   database. For a new item you can see whether we have written about it or not.
3. **Three roles and their prompts.** Collector, Rater, Summarizer. Each has its own input
   and its own output format.
4. **Daily run and build architecture.** One launch a day: collection, rating, summary,
   delivery. Linear. This is also where it is decided how the parts are connected: what
   starts the run on a schedule, where its state lives and what remains if a step fails in
   the middle.
5. **Preference memory.** The reaction to the digest influences future ratings. Between runs
   the system remembers which topics and sources the reader opens and which they skip.
6. **Moving the roles to a framework.** The roles move from ordinary functions to a graph of
   steps: explicit run state, retry of a failed step, resuming from the point of failure
   instead of restarting the whole day.
7. **Quality check.** A set of items with manual ratings, comparison with the system's
   rating, run traces.
8. **Cost and security.** The price of one daily run, limits, behavior when an instruction is
   written into the text of an article.
9. **Demo.** Five minutes: launch, selection from sixty items, the digest, the effect of a
   reaction.

## What we honestly do not do

- Downloading the full text of articles around a paywall: we do not do it, the decision is
  recorded in the strategy.
- Different readers with different topics: we do not do it, there is one reader.
- A web interface: we do not do it.
- Translation of items: we do not do it.
- Publishing the digest anywhere except a personal message: we do not do it.

## Stages

| Stage | What works at the end of the stage | Deadline |
|---|---|---|
| 1 | An agent from the IDE reads what has been collected through the MCP server, sets a rating and moves `collected` → `rated`. The transition `collected` → `summarized` is rejected | Week 2 |
| 2 | For a new item, search shows whether we have written about it before, with a link to the earlier summary | Week 3 |
| 3 | One launch a day: out of sixty items seven to ten remain, and the digest is ready from them | Week 4 |
| 4 | A reaction to the digest changes the next day's ratings, and this is visible on a specific topic | Week 5 |
| 5 | On a set of 100 items with manual ratings, the divergence from the system's rating is known | Week 6 |
| 6 | The price of a daily run is known, a limit is set, an instruction inside an article is not followed | Week 7 |

## Open questions

- **What counts as noise.** The Rater filters by topic description, but the descriptions are
  vague. Manual labeling of a hundred items is needed, otherwise there is nothing to check
  against. Close before the quality-check block.
- **How the reader reacts to the digest.** Buttons, a reply message or following a link. The
  whole of feature 5 depends on this. Not decided.
- **What to do with items that did not pass the filter.** They pile up in the `rated` status
  and are never summarized. Delete, keep or offer once a week, not decided.

## Later

- A weekly overview in addition to the daily one.
- A second topic with a separate digest.
- An assessment of how well a summary matched the content of the item.
