# 4 · End-to-end run

**Status:** `backlog` · **Waits for:** 1, 2, 3 · **Blocks:** 5

## What it does

Connects the three roles into one pass. A brief goes in, then the Writer writes a draft, the Fact
checker verifies it, the SEO specialist prepares the meta tags, and the article is saved in the
`checked` status together with the comments. There are no returns or repeats here: strictly
forward, once.

## Why

The first point where the project stops being a set of parts. A linear pass is needed before
loops, because it shows where the contracts between the roles do not match, and that is cheaper
to fix before branching is added.

## Input and output

| | |
|---|---|
| **Input** | Three debugged roles, the MCP server, search over the editorial policy |
| **Output** | The script `run_pipeline.py`: a brief goes in, the `id` of an article in the `checked` status comes out. Comments and meta tags are written to the database. A log of the pass with the time of each step |

## Boundaries

- Return for rework: out of scope, that is feature 5.
- Running several articles in parallel: out of scope, one article at a time.
- Restarting from the middle after a failure: out of scope, on failure the run starts over.
- Interface: out of scope, launch from the command line.

## Done when

- [ ] A brief produces an article in the `checked` status with no manual intervention
- [ ] All three roles have run, their outputs are written to the database
- [ ] A run on five different briefs finishes without failures
- [ ] A failure of any role leaves the article in the previous status, not in an intermediate one
- [ ] The log shows how long each role took

## Read before starting

- `../feature-3-agent-roles/README.md`: the role contracts
- `../feature-1-mcp-articles/README.md`: how to change the status
- `../../roadmap.md`, block 4

## Open questions

- What to do if the Fact checker found a serious violation and there is no return for rework yet.
  Hypothesis: leave the article in `draft` and record the comments. Clarify at the start.
