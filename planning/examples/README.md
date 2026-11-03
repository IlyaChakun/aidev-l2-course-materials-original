# Examples

Four filled-in sets, one for each course project track. Each has all five levels: vision,
product strategy, roadmap, the backlog registry with a tracker, and five described features.

| Folder | Track | Entity from the fixtures |
|---|---|---|
| [`ai-editorial/`](ai-editorial/) | AI editorial desk | `articles`: `draft` → `checked` → `published` |
| [`smart-support/`](smart-support/) | Smart support | `tickets`: `new` → `answered` → `escalated` |
| [`devtools-assistant/`](devtools-assistant/) | DevTools assistant | `review_tasks`: `queued` → `reviewed` → `tested` |
| [`knowledge-curator/`](knowledge-curator/) | Knowledge curator | `sources`: `collected` → `rated` → `summarized` |

The examples continue the starter fixtures from [`../../M1/fixtures/`](../../M1/fixtures/): the
same tables, the same fields, the same statuses. If you took the fixture for your track, the
example fits onto it without rework.

## Layout inside each one

```
<track>/
├── vision.md              where we are headed and what we will not do
├── strategy.md            who it is for, what it is and is not, priorities, decisions, risks
├── roadmap.md             data, functional blocks, what we do not do, stages
└── backlog/
    ├── README.md          feature registry and order of work
    ├── TRACKER.md         statuses, waves, rules for parallel terminals
    └── feature-N-<name>/
        └── README.md      what it does, boundaries, done when
```

## How to read

All four sets are shown in the same state: about the end of the second week of work. The first
feature is done, the second is being written, the third is being worked out, the fourth and
fifth are only described, and the distant roadmap blocks are not sliced at all. This is
deliberate: in real work a backlog is almost never filled in completely, and it is more useful
to see it in motion than in an ideal form.

Open questions marked "not decided" are left as they are. Having them is the normal state of a
plan, not an unfinished example.

Pay attention to two sections that are usually written as a formality, and here they carry
weight. In the vision it is "Check": a table of disputed decisions and how the vision resolves
them. If the vision resolved none, it would have to be rewritten. In the strategy it is
"Decisions made": each one is written as "we chose X over Y because Z", and it is exactly these
that the "Boundaries" sections in the features later refer to.

## How to use

The first way: copy your track's folder into the project repository and rewrite it for
yourself.

```
cp -r planning/examples/ai-editorial/* <your-project>/docs/
```

Then go through the files from top to bottom and replace someone else's decisions with your
own. Look first at the "Boundary" in the vision, "Decisions made" in the strategy and
"Boundaries" in the features: that is where the assumptions sit that you almost certainly have
different.

The second way: take a clean template from [`../templates/`](../templates/) and keep the
example open beside it as a model of scope and level of detail.

## What is not in the examples

There is no code here, no architectural decisions, no choice of libraries. The files describe
what is being done and why. How exactly is decided in `spec.md` inside the feature folder, and
that is the agent's work together with you, not something copied from an example.

The time estimates in the "Stages" section are also conditional. They show the form of the
entry, not a norm: at your own speed and on your own stack the numbers will be different.
