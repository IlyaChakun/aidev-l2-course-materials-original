# AI editorial desk — vision

> Updated: 04.08.2026 · Strategy: [`strategy.md`](strategy.md) · Roadmap: [`roadmap.md`](roadmap.md)

## Where we are headed

**The user and their world.** The editor of a small editorial office that publishes five to seven
pieces a week with three freelance authors. Half of their working day goes not on editing for
meaning but on mechanics: checking facts against links, remembering what the editorial policy
forbids in this section, and adding meta tags because the author again did not send them.

**What it will be like when it works.** The editor submits a brief and gets a draft in which the
disputed claims are already marked with links to sources, the places where the text departs from
the editorial policy are marked with the specific clause, and the meta tags are ready. They read
the text as an editor, not as a proofreader, and spend their time on the decision whether to
publish or not. The author gets comments the same day, not two days later.

**Why I am the one to build it.** I have the editorial policy itself, accumulated over four years
and published nowhere, and an understanding of which mistakes repeat from article to article in
this section. An outsider can build such a system, but it will check general rules, not ours.

**What it will not be.** The system does not write or publish anything without a human decision
and does not aim to replace the author.

## Boundary

We do not do these and do not plan to:

- Publish to the CMS automatically: the decision to publish stays with the editor, and this is
  not an implementation limit but the core of the idea.
- Write a whole article on a topic without a brief: that would be a text generator, whereas ours
  is an editorial process with an author inside it.
- Rate the quality of a text with a number and rank the authors: the editorial office has its own
  conversation about this, and it should not go through the system.
- Work with several publications and different editorial policies: the point is depth in one,
  not breadth.

## Check

| Question | What the vision answers |
|---|---|
| The fact checker found a violation and can fix the text itself. Do we allow it? | No. The author makes the fix, the system only flags. Otherwise the editor stops understanding whose text is whose |
| Add a "publish" button after the check? | No. Publishing is a human decision, not a pipeline step |
| An author asks to generate three headline options to choose from. Do we do it? | Yes, this is inside the process and does not replace the author. Unlike "write an article on a topic" |
| Someone asks to add a second publication with its own editorial policy. Do we take it? | No, this is squarely outside the boundary. In `roadmap.md` the idea sits under "Later" |

## What this file does not contain

Technical decisions, the list of features, deadlines and metrics. All of that lives below: the
product frame in [`strategy.md`](strategy.md), the stages in [`roadmap.md`](roadmap.md), the
scope of work in [`backlog/`](backlog/). The vision answers only the question of where we are
headed and what we will not be.
