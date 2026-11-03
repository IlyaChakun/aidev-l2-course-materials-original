# 3 · Three roles

**Status:** `spec` · **Waiting for:** 1, 2 · **Blocks:** 4

## What it does

Describes and debugs three agents: the Classifier, first-line Support and the Escalator. Each
has its own system prompt, its own input and its own output format. For now the roles are
launched separately by hand, feature 4 connects them.

## Why

The split into roles is not a formality here. The Classifier is needed before the answer,
because the queue is sorted before anyone starts answering. The Escalator solves its own task,
assembling context for the engineer, rather than just signing off on the first line's
helplessness.

## Input and output

| | |
|---|---|
| **Input** | The MCP server from feature 1, search from feature 2, 20 fixture tickets plus a sample from the export |
| **Output** | Three system prompts in `prompts/`, each with a JSON schema for its output. A script that runs any role on a given ticket |

Contracts between the roles:

| Role | Input | Output |
|---|---|---|
| Classifier | The text of the request, the channel | Category, urgency as a number 0-100, a "data is missing" flag |
| First-line Support | The request, the category, the documents found | A draft answer with links to sources, or a refusal with a reason |
| Escalator | The request, the first line's refusal, what has already been checked | Structured context for the engineer: the gist, what was checked, hypotheses, what is missing |

## Boundaries

- Orchestration of the roles: not included, that is feature 4.
- Clarifying questions to the customer: not included, that is feature 5. Here the Classifier
  only sets the missing-data flag.
- Automatic escalation on timeout: not included.
- Choice of a framework: not included, the roles are ordinary functions for now. Moving to a
  framework is block 6 of the roadmap.

## Done when

- [ ] Each role runs on any ticket with one command
- [ ] The output of each role passes validation against the JSON schema on all 20 fixture tickets
- [ ] Tickets of all three channels are processed the same way: the channel affects the form
      of the answer, but not whether the ticket is taken into work
- [ ] On a ticket without the needed data the Classifier sets the missing-data flag and does
      not invent a category
- [ ] On an empty search result Support refuses to answer and does not make up an answer
- [ ] In the draft answer every link leads to an existing document
- [ ] The Escalator assembles context from which the engineer does not re-ask the basics
- [ ] No role goes to the database directly, only through the MCP server

## Read before starting

- `../feature-1-mcp-tickets/README.md`: the set of tools
- `../feature-2-solutions-corpus/README.md`: what search returns and how a precedent differs
  from a policy
- `corpus/kb/escalation-rules.md`: the escalation rules
- `../../roadmap.md`, blocks 3 and 5

## Open questions

- **Urgency scale.** The number 0-100 is taken from the fixture, but people in the export used
  three levels. How to map them is not decided. The quality check depends on this.
- **First-line refusal.** Support must be able to say "I don't know". How to tell an honest
  refusal from model laziness is unclear. Hypothesis: require it to list what was checked.
- **Categories.** The list is taken from the export, where it is contradictory. We may have to
  reduce it to ten and relabel.
