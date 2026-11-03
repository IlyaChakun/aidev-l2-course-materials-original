<!--
ROADMAP TEMPLATE.

The third of the five files. Filled in after the vision and the strategy, prompt 3 from
planning/prompts.md: the roadmap answers "in which stages", while "what product and why" has
already been decided above.

Rules for filling it in:
- Placeholders in angle brackets <like this> are replaced entirely, brackets included.
- Do not delete a section you have nothing to put in. Write "not decided yet" and the date.
  An empty section is an open question, and a deleted section is a forgotten question.
- Length: two pages. If it comes out longer, part of the content is already a feature
  description and belongs in backlog/feature-N/README.md.
- Every functional block must turn into a backlog feature. If a block does not, it is
  written too generally.
- There are no sections here about the user, positioning or stack. They are in vision.md and
  strategy.md, and there is no need to rewrite them here: three files with the same paragraph
  drift apart in the second week.

Delete this comment when the file is filled in.
-->

# <Project name> — roadmap

> Updated: <DD.MM.YYYY> · Vision: [`vision.md`](vision.md) · Strategy: [`strategy.md`](strategy.md) · Backlog: [`backlog/`](backlog/)

## What we are building

<One or two phrases, so that the file reads on its own. The full picture is in the vision,
the product framing in the strategy, here only a reminder.>

## Data

| What | Where it lives | Volume | Access |
|---|---|---|---|
| <an entity with statuses> | <DB / API / files> | <how many records> | <available now / needs to be obtained> |
| <a corpus of documents> | <where> | <how many documents> | <available now / needs to be obtained> |

<Data comes as the first section because it is most often the thing that turns out to be
missing. If the "Access" column says "needs to be obtained", that is the project's first risk,
and it must go into the risks section of the strategy.>

## Functional map

<A numbered list of the system's blocks. Each block is a future backlog feature. Word each
block as what it does, not how it is built. Technical decisions are made at the feature
level.>

1. **<Block 1>.** <What it does. One or two sentences.>
2. **<Block 2>.** <...>
3. **<Block 3>.** <...>

## What we honestly do not do

<Specific functions that stay a stub or are not done within this scope of work, and why. This
is not the same as the boundary in the vision: that is the product boundary for the whole
idea, this is the list for the current scope. The section saves more time than any other:
without it the scope grows silently.>

- <function>: <stub / not doing>, <reason>
- <function>: <stub / not doing>, <reason>

## Stages

| Stage | What works at the end of the stage | Deadline |
|---|---|---|
| 1 | <a verifiable result: what you can run and see> | <week N> |
| 2 | <...> | <...> |
| 3 | <...> | <...> |

<A milestone is worded so that it can be checked by running it. "Document search is ready"
is not a milestone. "Given a question from the list, the system finds the right document and
answers with a quotation" is a milestone.>

## Open questions

<What is not decided and gets in the way of the work. Different from the hypotheses in the
strategy: a hypothesis is an assumption about the product that is checked by experience, an
open question is a fork you are standing at right now. Each question is marked with when it
must be closed.>

- **<Question>**. Close by <when>. <What is needed to answer it.>

## Later

<Ideas that are definitely not in the scope of the project. The section exists so that an
idea has somewhere to go and is not dragged into the current work.>

- <idea>
