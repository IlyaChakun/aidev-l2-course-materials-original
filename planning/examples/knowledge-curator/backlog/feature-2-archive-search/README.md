# 2 · Archive and search

**Status:** `in-build` · **Waiting for:** none · **Blocks:** 3

## What it does

Puts items that have already been summarized into a search corpus. The input is the title and
description of a new item, and the output is an answer on whether we have written about it
before, with a link to the earlier summary and a date.

## Why

The same story arrives from five sources with different titles and different links. Without a
check by meaning, half the digest consists of repeats, and the reader stops opening it.
Comparison by link does not solve this task, decision of 03.08.

## Input and output

| | |
|---|---|
| **Input** | Items in the `summarized` status from the `sources` table |
| **Output** | The `archive/` module: indexing of summaries, search. `findSimilar(title, body, k)` returns similar items with a date and a similarity score |

The index is updated after each run, not rebuilt from scratch.

## Boundaries

- Search over the full text of items: not included, we index summaries and titles.
- Indexing items that did not pass the filter: not included.
- Determining which of the duplicates is better: not included, that is the Rater's job in
  feature 3.
- Sending anything to the reader: not included.

## Done when

- [x] Indexing starts with one command, the number of chunks is printed to the console
- [x] A chunk has a link to the source item and the date of the summary
- [ ] Five variants of one story from different sources are recognized as one
- [ ] Different stories on the same topic are not merged into duplicates
- [ ] An item that did not exist before gives an empty result
- [ ] Appending after a run does not rebuild the index from scratch and does not duplicate chunks

## Read before starting

- `../feature-1-mcp-sources/README.md`: where the summaries come from
- `../../roadmap.md`, block 2
- `spec.md` next to this file

## Open questions

- **Merging threshold.** Too low merges different stories on one topic, too high misses
  duplicates. The value is tuned on five variants of one story, not decided yet.
- **What to do with updates.** An item came out, then was supplemented and came again. Is it
  a duplicate or new, not decided.
- **Cold start.** In the first days the archive is empty and the check gives nothing. It
  seems this is normal and is cured by time, but verify on the first run.
