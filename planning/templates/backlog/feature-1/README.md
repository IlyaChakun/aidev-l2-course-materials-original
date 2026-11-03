<!--
FEATURE TEMPLATE.

One file per feature, one page. This is the file you give the agent at the start of the work,
so it must be self-sufficient: the agent should not have to guess what was meant.

Filled in with prompt 5 from planning/prompts.md. The quality check is simple. Give the filled
in README to an agent in an empty terminal and ask what it is going to do. If the answer
matches your idea, the file is done. If the agent starts asking about basic things, write
them here, not in the chat: in the chat they disappear along with the session.

The "How it is run" section is a reminder of the order of work, the same for all features.
Once the order has become habit, delete it: that is exactly why the examples do not have it.

Delete this comment when the file is filled in.
-->

# <Number> · <Feature name>

**Status:** `backlog` · **Waiting for:** <feature numbers or "none"> · **Blocks:** <feature numbers or "none">

## What it does

<Two to four sentences. What appears in the project after this feature, through the eyes of
whoever uses it. Not a list of tasks and not a description of the architecture.>

## Why

<Which problem it closes and what breaks without it. One or two phrases. If there is nothing
to write, the feature is either unnecessary or sliced wrongly.>

## Input and output

| | |
|---|---|
| **Input** | <what must exist before the start: data, finished features, access> |
| **Output** | <what appears: files, endpoints, tables, behavior> |

<The output is what the following features use. Word it so that a neighboring feature can
rely on it without reading your code.>

## Boundaries

<What is not part of this feature. The most useful section of the file: without it the agent
fills in the scope itself and does twice as much as needed.>

- <not included>
- <not included>

## Done when

<Verifiable items. Not "RAG is built" but "for question X the system returns document Y".
Every item must be checkable by running it, not by opinion.>

- [ ] <verifiable sign>
- [ ] <verifiable sign>
- [ ] <verifiable sign>

## Read before starting

<Files and links the agent must read before starting. Paths from the repository root. The
list is short: five links is already a lot, and the agent will skim them.>

- <path to file>: <why it is needed>
- <link>: <why>

## How it is run

A separate terminal, from the project root. The order:

1. Read this file and what is listed above.
2. Work out the solution together with the agent, record the result in `spec.md` next to this
   file.
3. Break the spec into steps, record them in `plan.md`.
4. Write code following the plan, marking finished steps in `plan.md`.
5. Check the items from "Done when", set the status to `done` in `../README.md`.

## Open questions

<What will become clear along the way. A question with no answer is better than an answer
invented by the agent.>

- <question>
