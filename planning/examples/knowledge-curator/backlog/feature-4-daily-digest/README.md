# 4 · Daily run

**Status:** `backlog` · **Waiting for:** 1, 2, 3 · **Blocks:** 5

## What it does

Connects the three roles into one scheduled launch. Once a day the Collector gathers new
items, the Rater filters out noise and duplicates, the Summarizer writes a summary for those
that passed the selection, and the digest goes out as one message. There are no branches and
no retries.

## Why

This is the moment the project is done for: the tool starts working on its own, without being
launched by hand. It is also where the real price of a run is first visible, because there
are sixty items, not five.

## Input and output

| | |
|---|---|
| **Input** | Three debugged roles, the MCP server, search over the archive |
| **Output** | The command `npm run digest`, which is also the scheduled one. The result is a sent message and items in the `summarized` status. A run log with the number collected, filtered out and summarized, and with the time of each step |

## Boundaries

- Accounting for the reader's reactions: not included, that is feature 5.
- A second digest on another topic: not included.
- A web interface and an archive in the browser: not included.
- Resending on a delivery failure: not included, on a failure we look at the log by hand.

## Done when

- [ ] One launch goes through the whole path without manual intervention
- [ ] Of roughly sixty collected, seven to ten remain, the number is set in the config
- [ ] Duplicates of one story from different sources get into the digest once
- [ ] An unavailable source does not crash the run, it is written to the log
- [ ] The run is launched on a schedule and works three days in a row without intervention
- [ ] The log shows the number of items at each step and the time of each role

## Read before starting

- `../feature-3-agent-roles/README.md`: the role contracts
- `../feature-2-archive-search/README.md`: how a duplicate is determined
- `../../roadmap.md`, block 4

## Open questions

- What to do with items that did not pass the filter. An open question from the roadmap, here
  it becomes practical: they pile up in the `rated` status and will never go further.
- In the first days the archive is empty and the duplicate check will give nothing. Check on
  the first run whether anything breaks on an empty index.
