# 5 · Clarification and memory

**Status:** `backlog` · **Waiting for:** 4 · **Blocks:** none

## What it does

Adds a clarification branch to the run. If the Classifier flagged missing data, the system
formulates a question for the customer, waits for the answer and processes the ticket again
with it. It also mixes the same customer's earlier requests into the context, so as not to ask
again what is already known.

## Why

Without this, half the requests run into "not enough data" and go to a human. It is also the
first place where state between launches appears: without it a repeated processing is no
different from the first and leads to the same result.

## Input and output

| | |
|---|---|
| **Input** | The working end-to-end run from feature 4 |
| **Output** | A clarification branch with a limit on the number of questions. The processing history in the database: what was asked, what was answered, what changed. Mixing the customer's earlier requests into the context of the Classifier and Support |

## Boundaries

- Sending the question to the customer: not included. The question is written to the database,
  the on-call person sends it.
- Long-term memory about the product and general topics: not included, memory is only by customer.
- A dialogue of more than two turns: not included, a limit from the roadmap.
- A separate dispatcher role: not included, the branching is in the run code.

## Done when

- [ ] A ticket with the missing-data flag leads to a formulated question, not to an escalation
- [ ] The customer's answer is substituted, and the repeated processing gives a different result than the first
- [ ] The same question is not asked twice
- [ ] When the question limit is exhausted the ticket goes to `escalated` with a note of what was missing
- [ ] The customer's earlier requests are visible in the context, and this is noticeable on a customer with a history
- [ ] A ticket with complete data still passes without clarifications and has not slowed down
- [ ] The processing history can be reconstructed by a query to the database

## Read before starting

- `../feature-4-end-to-end/README.md`: how the linear pass is built
- `../feature-3-agent-roles/README.md`: the missing-data flag
- `../../roadmap.md`, block 5

## Open questions

- **How many earlier requests to mix in.** Right now the last three, the number was picked at
  random. Check on customers with a long history.
- **Storing the processing history.** A separate table or JSON in `tickets`. It touches the
  migrations, agree with the feature 2 terminal through the tracker.
- A debt hangs over from feature 1: the escalation context is written as a single text field,
  and here it must be structured.
