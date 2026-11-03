<!--
BACKLOG REGISTRY TEMPLATE.

Filled in after the roadmap: prompt 4 from planning/prompts.md. The functional blocks of the
roadmap turn into the rows of this table, one row per block, and into folders next to this
file.

The one-folder rule: one feature is one folder, and everything written about it lives inside
it. The spec, the plan, notes, draft diagrams. None of it settles in a shared project folder.

Delete this comment when the file is filled in.
-->

# Backlog — <project name>

One feature, one folder. Inside the folder `README.md` describes the whole feature, and as
work goes on `spec.md` and `plan.md` appear next to it.

Vision: [`../vision.md`](../vision.md) · Strategy: [`../strategy.md`](../strategy.md) ·
Roadmap: [`../roadmap.md`](../roadmap.md) · Statuses and rules for parallel work:
[`TRACKER.md`](TRACKER.md)

## Features

| # | Feature | What it does | Depends on | Status |
|---|---|---|---|---|
| 1 | [<name>](feature-1/) | <one line> | none | `backlog` |
| 2 | <name> (`feature-2/`) | <one line> | 1 | `backlog` |
| 3 | <name> (`feature-3/`) | <one line> | 1, 2 | `backlog` |

The template contains one feature folder, `feature-1/`. The rest are copied from it. As soon
as a folder is created, the feature name in the table turns into a link, as in the first row.

**Statuses:** `backlog` (described, not started) · `spec` (being worked out) · `in-build`
(code is being written) · `done` (works and is checked) · `blocked` (waiting on something
external, with what exactly in parentheses)

## Order of work

```
<ASCII dependency diagram. Example of the shape:

  1 <foundation feature>
     ├─ 2 <feature>   ─┐  (2 and 3 run in parallel after 1)
     └─ 3 <feature>   ─┘
           4 <feature that needs 2 and 3>
>
```

<In one phrase: what is on the critical path and why. The critical path is the chain in
which a delay shifts everything else.>

## What is still ahead

<Roadmap blocks you have not yet got round to slicing. Names without folders. The section
shows that the backlog is incomplete on purpose, not through forgetfulness.>

- <roadmap block>
- <roadmap block>
