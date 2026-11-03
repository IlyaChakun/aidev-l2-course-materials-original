# Smart support — product strategy

> Updated: 04.08.2026 · Vision: [`vision.md`](vision.md) · Roadmap: [`roadmap.md`](roadmap.md)

## Who it is for

A support on-call person in a team of four, about forty requests a day, three channels: email,
chat and phone. Today they read the queue in order, judge urgency by eye, and look for similar
cases from memory and by searching the work chat.

## What it is and what it is not

**It is:** processing of the incoming queue by three roles up to the state in which the
on-call person only has to check and send.

**It is not:** a chatbot for the customer (the customer does not talk to the system), not a
ticketing system (the queue already exists, we work on top of it) and not a knowledge base with
an interface (search here is an internal tool of the roles, not a product for a person).

## Stage

Prototype on anonymized data. By the defense we need processing on a real queue with a
measured share of answers that the on-call person accepted without edits.

## Current priorities

1. Urgency classification. Without it the queue stays unsorted, and the main pain does not go
   away however many good answers the system writes.
2. A draft answer with a link to the policy. Without a link the on-call person re-checks by
   hand, and the time gain disappears.
3. An honest refusal by the first line. A system that always answers something is worse than a
   system that can say "I don't know".
4. A clarifying question when data is missing, otherwise half the requests run into a human.

## Decisions made

| Date | Decision | Why |
|---|---|---|
| 30.07 | Take the track as is, do not invent our own domain | The data and statuses are ready, time goes into the system |
| 30.07 | TypeScript and PostgreSQL, data loading through migrations | The schema will change with every feature, manual loads will drift apart |
| 31.07 | Urgency is computed by a separate role, not by Support along with the answer | Urgency is needed before the answer: the queue is sorted before anyone starts answering |
| 01.08 | Escalation is a separate role, not a branch inside Support | Escalation has its own task: to assemble context for the engineer. It is not "could not answer" |
| 02.08 | Anonymize the export of closed requests before loading it into the project | The requests contain addresses and phone numbers, which have no business in the project |
| 04.08 | The urgency threshold is a number in the config, not text in the prompt | The threshold will have to be moved based on results, and doing that by editing the prompt is inconvenient |

## Risks

| Risk | What we do |
|---|---|
| Categories in the export were assigned by people and contradict each other | Decide before the quality-check block: either check against the export as is, or reduce to ten categories and relabel |
| Search always returns something, and Support answers from an irrelevant policy | A cutoff threshold plus a requirement to refuse on an empty result |
| The model refuses to answer too often, and the system is useless | Require the refusal to list what was checked. A refusal without a list is not accepted |
| Anonymization misses personal data | A sample check on 50 records before loading, a search for address and phone patterns |

## Hypotheses to check

- The on-call person sends a draft with a link to the policy without edits more often than a
  draft without a link. Checked by: the share of accepted answers in the first two weeks of
  operation.
- Two clarifying questions are enough, beyond that it is already correspondence. Checked by:
  the share of requests that reached the limit, on the runs of feature 5.
- The customer's last three requests are enough for context. The number was picked at random,
  checked on customers with a long history.

## What this file does not contain

Architecture and diagrams, the list of features and deadlines, the history of discussions,
current metric values.
