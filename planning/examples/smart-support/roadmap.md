# Smart support — roadmap

> Updated: 04.08.2026 · Vision: [`vision.md`](vision.md) · Strategy: [`strategy.md`](strategy.md) · Backlog: [`backlog/`](backlog/)

## What we are building

Processing of the incoming queue by three roles: the Classifier sets the category and urgency,
first-line Support prepares a draft answer from the solutions base, the Escalator assembles
context for the engineer. For whom and why it is done this way: [`vision.md`](vision.md) and
[`strategy.md`](strategy.md).

## Data

| What | Where it lives | Volume | Access |
|---|---|---|---|
| Tickets | PostgreSQL, table `tickets` | 20 fixture records plus an anonymized export | Available |
| Anonymized export of closed requests | CSV | 480 requests over half a year | Available, names and addresses cut out at export |
| Solutions and policies base | Markdown | 61 documents, about 140 pages | Available |
| Escalation rules | One document | 4 pages | Available |

Anonymization is done before loading, only `subject`, `body`, `answer`, the category and the
closing date get into the project.

## Functional map

1. **Access to tickets.** Our own MCP server over the `tickets` table: reading the queue,
   writing an answer, moving through statuses with a check that the transition is allowed.
2. **Solutions base and search.** Policies and solutions are chunked and live in a vector
   database. For the text of a request, suitable documents are returned.
3. **Three roles and their prompts.** Classifier, first-line Support, Escalator. Each has its
   own input and its own output format.
4. **End-to-end run and build architecture.** A ticket on input, an answer or an escalation on
   output. Linear. This is also where it is decided how the parts are connected: what calls
   the roles, where the processing state lives and in which status the ticket stays if a step
   fails in the middle.
5. **Clarification and customer memory.** If data is missing, the system formulates a
   clarifying question and waits for the answer. Earlier requests from the same customer are
   taken into account.
6. **Moving the roles to a framework.** The roles move from ordinary functions to a graph of
   steps: explicit processing state, retry of a failed step, waiting for the customer's reply
   as a state rather than as a pause in the code.
7. **Quality check.** A set of tickets with a known correct outcome, automatic evaluation of
   classification and answers, traces.
8. **Cost and security.** The price of processing one ticket, limits, behavior when an
   instruction is written into the text of a request.
9. **Demo.** Five minutes: the queue, processing an urgent ticket, escalating a complex one.

## What we honestly do not do

- Sending an answer to the customer: we do not do it, the decision is recorded in the strategy.
- Integration with a real task tracker: a stub, the escalation is written to the database and
  to a file.
- Call transcription: we do not do it. Phone requests are processed on a par with the others,
  but from the text that the on-call person typed during the conversation: we do not connect
  to recordings.
- A customer account area: we do not do it.
- Multilingual support: we do not do it, requests are in one language.

## Stages

| Stage | What works at the end of the stage | Deadline |
|---|---|---|
| 1 | An agent from the IDE reads the queue through the MCP server, writes an answer and moves `new` → `answered`. The transition `answered` → `new` is rejected | Week 2 |
| 2 | For the text of a request, search returns a suitable policy with the document named | Week 3 |
| 3 | A ticket on input, the category, urgency and a draft answer on output | Week 4 |
| 4 | A ticket without the needed data triggers a clarifying question, a repeated processing takes the answer into account | Week 5 |
| 5 | On a set of 60 tickets the share of correct categories and the share of answers that the on-call person accepted without edits are known | Week 6 |
| 6 | The price of processing is known, a limit is set, an instruction inside a request is not followed | Week 7 |

## Open questions

- **What counts as the correct category.** In the export the categories were assigned by
  people and in places contradict each other. Close before the quality-check block: we need to
  decide whether to check against the export or relabel.
- **How many clarifying questions are acceptable.** Not decided. More than two is already
  correspondence, not processing.
- **How many earlier requests from the customer to mix into the context.** For now the last
  three, the number was picked at random.

## Later

- Accepting requests directly from email and chat, without entering them into the queue by hand.
- A hint to the on-call person during a manual answer, rather than a separate draft.
- Feedback: whether the on-call person edited the draft, and taking that into account in the
  evaluation.
