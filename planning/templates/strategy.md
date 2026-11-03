<!--
PRODUCT STRATEGY TEMPLATE.

This is the file the agent reads at the start of every session. Everything else follows from
that:

- Length is one screen. Two minutes to read. The file is loaded into context on every task,
  and every extra two pages are paid for with every run.
- Write decisions, not the reasoning that led to them.
- Current metric values are not written here: they change every day, and the file does not.

Filled in after the vision, prompt 2 from planning/prompts.md.

It is connected to the agent by a pointer in the rules file, not by copying the content: the
ready-made block and the explanation of why it is done this way are in planning/README.md,
section "How to connect it to the agent".

Delete this comment when the file is filled in.
-->

# <Project name> — product strategy

> Updated: <DD.MM.YYYY> · Vision: [`vision.md`](vision.md) · Roadmap: [`roadmap.md`](roadmap.md)

## Who it is for

<One or two sentences. More specific than in the vision: the role, the situation, the volume
of work, what the person does today instead of your system.>

## What it is and what it is not

**It is:** <one phrase that makes clear which class of systems the project belongs to>

**It is not:** <one or two phrases. The nearest neighboring classes you will be mistaken for
and that you are not. The section exists so that the agent does not drag features of a
neighboring class into the project just because they are usually there.>

## Stage

<One word or phrase: prototype, working version on your own data, preparing for the defense.
The agent behaves differently at different stages: on a prototype it should cut corners, at
the defense it should not. The stage is the only place where this is said.>

## Current priorities

<A numbered list, five items at most, the order matters. A list without order does not help
you choose. If everything is important, nothing is.>

1. <the most important thing right now>
2. <...>
3. <...>

## Decisions made

<Decisions that constrain the project and are not revisited. One format: we chose X over Y
because Z. Without the "because", the decision gets reopened two weeks later, and usually by
the agent, not by you.

Product-level and architecture-level decisions go here, not operational ones. Operational ones
live in the feature specs.>

| Date | Decision | Why |
|---|---|---|
| <DD.MM> | <chose X over Y> | <on what grounds> |

## Risks

<Two to four items. Only what can really stop the work, together with what you intend to do
about it. The section is not for completeness but for naming a risk before it goes off.>

| Risk | What we do |
|---|---|
| <what could go wrong> | <how we reduce it or what we replace it with> |

## Hypotheses to check

<What you assume but do not know. Each hypothesis comes with the means of checking it. A
hypothesis with no way to check it is just an opinion, and is better removed.>

- <assumption>. Checked by: <what and when>

## What this file does not contain

Architecture and diagrams (that is the code and its documentation), the list of features and
deadlines (roadmap and backlog), the history of discussions (only the conclusion goes here),
current metric values (they change, the file does not).
