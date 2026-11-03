# Knowledge curator — vision

> Updated: 04.08.2026 · Strategy: [`strategy.md`](strategy.md) · Roadmap: [`roadmap.md`](roadmap.md)

## Where we are headed

**The user and their world.** One person who follows seven topics across twenty-four feeds and
nine open channels. They have forty minutes a day for reading, and about a hundred new items
arrive. They skim the headlines, put half of them off "for later" and never come back, and
they learn about the important things a week late, by accident, and from colleagues.

**What it looks like when it works.** One digest arrives in the morning: seven to ten items,
and for each one you can see what it is about and whether it is worth opening in full.
Repeats of one story from five sources are collapsed into a single item. After a month the
system knows which topics they open and which they skip, and selects more precisely than on
the first day.

**Why I am the one to do it.** I am the only user, and I have what no general-purpose service
has: my own reactions to every item and an archive of what has already been read and
summarized. A system can learn from that, and that is the whole point.

**What it will not be.** The system does not summarize what it has not read, and does not
pass off a summary as the source.

## Boundary

What we do not do and do not intend to do:

- Summarize items for which only the teaser is available: the feed gives three paragraphs,
  and a summary based on them would be invented. We mark such items and do not summarize them.
- Serve several readers with different topics: all the value is in the preference memory of
  one person, and it cannot be shared.
- Publish the digest anywhere except a personal message: this is a personal tool, not a
  media outlet.
- Download full texts around a paywall.

## Check

| Question | What the vision answers |
|---|---|
| An item is behind a paywall, and we have three paragraphs. Do we summarize it? | No, we mark it and do not summarize it |
| Build a web archive of summaries with search? | No. The archive is for the system to find duplicates, not for a person as a product |
| Also send the digest to the team's work channel? | No, that is directly outside the boundary |
| Spend effort on preference memory, even though it only pays off after a month? | Yes. That is the whole idea, without it all that is left is an ordinary feed |

## What this file does not contain

Technical decisions, the list of features, deadlines and metrics. Product framing is in
[`strategy.md`](strategy.md), stages in [`roadmap.md`](roadmap.md), the breakdown of work in
[`backlog/`](backlog/).
