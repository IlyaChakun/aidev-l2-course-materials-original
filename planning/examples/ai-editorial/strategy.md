# AI editorial desk — product strategy

> Updated: 04.08.2026 · Vision: [`vision.md`](vision.md) · Roadmap: [`roadmap.md`](roadmap.md)

## Who it is for

The editor of a small editorial office: five to seven pieces a week, three freelance authors, one
editorial policy of 34 documents. Today they proofread by hand, check facts against links
themselves, and add the meta tags the author left out.

## What it is and what it is not

**It is:** an editorial pipeline on top of an article database, where three roles prepare a piece
for a human decision.

**It is not:** a text generator for a topic (we have a brief and an author), not a CMS
(publishing stays outside), and not an SEO service (meta tags are the last step of the process,
not the product).

## Stage

A prototype on our own data. For the defense we need a working version on the live editorial
policy and real articles, not a demonstration on three examples.

## Current priorities

1. A fact checker that cites a specific clause of the editorial policy. Without this the comments
   read as matters of taste, and the whole point is lost.
2. An end-to-end pass from the brief to the `checked` status with no manual intervention.
3. Return for rework: without it the system hits a human at the first disputed fact.
4. The cost of one pass. Unknown for now, and it determines how many rework rounds we can afford
   at all.

## Decisions made

| Date | Decision | Why |
|---|---|---|
| 30.07 | Take the AI editorial desk track as is, do not invent our own domain | The fixture covers the first two weeks, time goes into the system, not the data |
| 30.07 | Python and PostgreSQL. SQLite was used for two days, we are not going back | JSON fields and migrations will be needed later, and SQLite is awkward for that |
| 31.07 | Status transitions are checked on the server, not in the agent's prompt | A prompt can be bypassed by finding the right wording, code cannot |
| 01.08 | The editorial policy is stored as separate documents, not as one file | A comment needs a link to a specific document, otherwise the author does not understand where the requirement comes from |
| 03.08 | The fact checker does not edit the text but returns comments. The Writer edits | Two roles editing one text produce conflicting edits |
| 03.08 | Publishing to the CMS is not built, the final status in the database counts as publication | The integration would eat a week and adds nothing to the core of the project |

## Risks

| Risk | What we do |
|---|---|
| The free-tier limit of the search API runs out midway | Count the number of checks per article before the start of feature 3. Fallback: check only claims with numbers and dates |
| Search over the editorial policy always returns a rule, even when there are none | A cutoff threshold and a test on paragraphs for which there are definitely no rules |
| Rework rounds do not converge, the article bounces between roles forever | A hard limit on rounds, after which the article goes to a human |
| The cost of a pass turns out such that a second round is not worth it | Measure the cost starting from feature 4, not at the end |

## Hypotheses to check

- An author accepts a comment with a link to an editorial policy clause without argument, and
  argues with one without a link. Checked on: the first ten real comments, counting how many came
  back for discussion.
- Two rework rounds are enough for most articles. Checked on: the share of articles that reached
  the limit in the feature 5 runs.
- Chunking the editorial policy by section works better than chunking by size. Checked on: ten
  test paragraphs in feature 2.

## What this file does not contain

Architecture and diagrams, the list of features and deadlines, the history of discussions, current
metric values.
