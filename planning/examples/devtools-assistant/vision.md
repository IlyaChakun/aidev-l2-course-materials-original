# DevTools assistant — vision

> Updated: 04.08.2026 · Strategy: [`strategy.md`](strategy.md) · Roadmap: [`roadmap.md`](roadmap.md)

## Where we are headed

**The user and their world.** A developer on a team of six where reviews sit for two days. Half
of the review comments are the same thing: a violated convention, a forgotten test for a new
function, an outdated docstring. Because of this the reviewer gets to the substantive things
tired, and never gets to the documentation at all.

**What it will be like when it works.** The author opens a change and sees comments on conventions
with a link to the specific rule, draft tests for the new functions and updated docstrings. The
human reviewer comes to a change where the mechanics are already sorted out, and looks at the
architecture and the meaning. The review queue stops being two days long, because the first pass
does not require a human.

**Why I am the one to build it.** I have this team's conventions and two hundred and ten
discussions from past reviews, that is, a history of what we actually stumble on. A general
linter will not replace this knowledge: half of our rules are formalized nowhere and live in
discussions.

**What it will not be.** The system does not approve or reject changes and does not fix code for
the author.

## Boundary

We do not do these and do not plan to:

- Give a verdict on a change: the decision is made by a human, an automatic approve will not
  appear at any stage.
- Fix what it finds on its own: a comment and a fix are different responsibilities, and mixing
  them means losing trust in both.
- Replace the human in review: the goal is to take off the mechanical half, not everything.
- Work with several repositories and different conventions: the value is in the depth of one set
  of rules.

## Check

| Question | What the vision answers |
|---|---|
| Add an automatic approve if there are no comments? | No, squarely outside the boundary |
| A reviewer suggests generating a patch with the fix. Do we do it? | No. We flag, the author fixes |
| Issue general style comments with no link to our rule? | No. Our conventions are the only advantage, and general comments cancel it |
| Index discussions from past reviews, not only the convention documents? | Yes. That is exactly where what general linters lack lives |

## What this file does not contain

Technical decisions, the list of features, deadlines and metrics. The product frame is in
[`strategy.md`](strategy.md), the stages in [`roadmap.md`](roadmap.md), the scope of work in
[`backlog/`](backlog/).
