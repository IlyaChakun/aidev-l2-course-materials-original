# Course project planning

The course project runs for seven weeks and usually falls apart not because the task is hard,
but because the whole idea lives in your head and in your chat with the agent. This folder
holds a form that fixes that: five files from "why do this at all" to "what are we doing
today", and work on one feature at a time in its own terminal.

## What is in the folder

| What | Where | Why |
|---|---|---|
| Templates | `templates/` | An empty skeleton with placeholders. Copy it to your project and fill it in |
| Prompts | `prompts.md` | Ready-made texts for the agent for each step: vision, strategy, roadmap, backlog slicing, feature, work, revision |
| Examples | `examples/` | Four filled-in sets, one per course project track |

You can enter from either end. Either you take an empty template and fill it in from scratch,
or you open the example for your track, copy it to your project and rewrite it for your
project. The second is faster, but the example is deliberately not polished to perfection: it
is someone else's draft, not your plan.

## Five levels

From top to bottom, from "why" to "what are we doing today". Each level answers its own
question and does not stray into another's.

| Level | File | Answers | Length | Changes |
|---|---|---|---|---|
| 1. Vision | `vision.md` | Where we are headed and what we will not do | 5-7 sentences | Almost never |
| 2. Strategy | `strategy.md` | Who it is for, what it is and is not, what matters now | One screen | Every couple of weeks |
| 3. Roadmap | `roadmap.md` | In which stages, from which blocks, what we do not do | Two pages | Weekly |
| 4. Backlog | `backlog/README.md` + `TRACKER.md` | What is sliced, in what order, what can be picked up | A table | Daily |
| 5. Feature | `backlog/feature-N/README.md` | What this thing does and when it is done | One page | While the feature is in progress |

The levels are not separated for looks. They have different lifespans and different readers:
you reread the vision when you are arguing with yourself about direction, the agent reads the
strategy at the start of every session, you open the roadmap once a week and the backlog every
day. You can dump all of this into one file, but then either the agent loads your reasoning
about the future into context on every task, or the direction of the project gets lost among
feature statuses.

### What lives where, so as not to duplicate

Three pairs of sections look alike and constantly drift into each other. The boundary runs like this:

| Similar | Vision | Strategy | Roadmap |
|---|---|---|---|
| About the user | Who they are and what their pain is | What situation they are in and what they do today | — |
| About boundaries | What the product will never be | Which class of systems we do not belong to | Which functions we do not build in this scope |
| About the unresolved | — | Hypotheses: what we assume and how we will check it | Open questions: the forks we are standing at right now |

Decisions made live in one place, the strategy, in the format "we chose X over Y because Z".
A decision without a reason gets revisited from scratch two weeks later, and usually by the
agent, not by you.

One repetition here is deliberate. The "Who it is for" section in the strategy retells the
first paragraph of the vision in compressed form, and that is as it should be: the strategy is
loaded into context on every task, and the agent does not see the vision at all. The strategy
must stand on its own. The retelling is short, two or three lines, and adds what the vision
does not have: the volume of work and what the person does today instead of your system.

## Why it is done this way

**The agent needs input of bounded size.** You do not give the agent the whole project. You
give it the `README.md` of one feature plus whatever that README links to, and the strategy is
loaded as a permanent background. Everything else does not get into the context.

**What the agent does not see does not exist for it.** An idea that lives in a chat and in
your head does not exist for the agent: it works only with what lies in the repository. Hence
the rule this whole folder grows from: a decision that is not written into a file will be made
again, and not by you.

**The strategy holds the scope back.** Agents tend to add on: you asked to fix the search and
got filters, query history and analytics. The sections "what it is not" and "what we honestly
do not do" exist precisely so that the agent has an answer to "is this needed" without asking you.

**Features are run in separate terminals.** One terminal, one feature, one owner. While a
feature is in progress, its folder belongs to that terminal. This way two or three independent
features run in parallel without one agent rewriting the result of another.

**Coming back is cheaper.** You were away for a week, opened `backlog/README.md`, looked at the
statuses, took the next free feature. There is no need to remember where you left off.

There is also an opposing view, and it is worth knowing: some practitioners believe you should
not write documentation for the agent, and let it figure things out from context each time. On
a small project with one terminal this is a workable position. Over seven weeks, three agent
roles and parallel features, it breaks down on the very first return to work after a pause.

## How to use it

**Step 0.** Copy the contents of `templates/` into your project repository. The usual place is
`docs/`, but the root will do as well: what matters is that the files lie in the same
repository as the code and are committed together with it.

```
cp -r planning/templates/* <your-project>/docs/
```

**Step 1. Vision.** Prompt 1. Five to seven sentences, half an hour of conversation with the
agent. There is one check: take the nearest disputed question on the project and try to
resolve it with the vision. If it does not resolve, it is decoration, and it must be rewritten.

**Step 2. Strategy.** Prompt 2. One screen. After filling it in, connect the files to the
agent as described below: without that they are read only when you remember them yourself,
and half the point is lost.

**Step 3. Roadmap.** Prompt 3. Two pages: data, functional blocks, what we do not do, stages.

**Step 4. Backlog slicing.** Prompt 4. The agent reads the roadmap and proposes a split into
features with dependencies. You accept the split, not the agent: fix the disputed spots
right away, later it costs more.

**Step 5. Feature READMEs.** Prompt 5, one feature at a time. It is enough to fill in the first
two or three, the rest can wait: after the very first finished feature, half of the rest will
be rewritten.

**Step 6. Work.** A separate terminal per feature, prompt 6.

**Step 7. Revision.** Prompt 7, once every two or three weeks. The plan and the code always
diverge, the only question is whether you notice it.

## How to connect it to the agent

The files are created, but the agent does not know about them. They are connected not by their
content but by a pointer.

**Do not put the content into the agent's rules.** The rules file, be it `CLAUDE.md`,
`AGENTS.md` or `.cursor/rules`, is read in every terminal and on every task. Whatever lands
there you always pay for with context, including when you are fixing indentation in a test. An
unconditional "read the strategy before starting work" is the same mistake in a smaller form:
the agent dutifully loads the file on every task, including those where no product decisions
are being made.

**Put a condition.** The rules hold a dozen lines about where the plan is and when to look into
it, and the files themselves are read at the moment they are needed. Paste this block into your
rules file as is, substituting your own path for `docs/`:

```
## Project planning

The project's idea lives in docs/. Read these files conditionally, not every time.

- Planning a feature, arguing about scope, making a product decision, choosing
  what to do next → docs/strategy.md, then as needed docs/roadmap.md
  and docs/backlog/README.md.
- Working on a specific feature → docs/backlog/<feature folder>/README.md in full
  and what is listed in its "Read before starting" section.
- Implementing an already described feature, debugging, editing code → do not read
  anything from the above, everything needed is already in the task.

Do not read docs/vision.md until I ask directly: it is a file for me, not for you.

If you doubt whether something new is in scope, look at docs/strategy.md, the section
"What it is and what it is not". If the answer is not there, ask me.
```

**Where exactly to paste it.** Every tool has its own rules file, but the rule is the same: the
file the tool reads by itself, without a reminder.

| Tool | File |
|---|---|
| Claude Code | `CLAUDE.md` in the project root |
| Codex, opencode and anything that understands the common format | `AGENTS.md` in the project root |
| Cursor | `.cursor/rules/planning.mdc` |
| Copilot | `.github/copilot-instructions.md` |

The text of the block is carried over unchanged, it is not tied to anything. The wrapper,
however, differs between files: for Cursor the rule requires a short header stating that it
applies always. Their header format has changed over time, so check their documentation, not
someone else's year-old example. If your tool is not in the table: find in its documentation
which file it reads by itself, and put the block there.

Keep one rules file, and make the others a link to it or a symlink. Two copies will drift apart
in the second week, and you will not know which one took effect.

**Which of the five files the agent needs at all.** Not all of them. You write the vision for
yourself, and for the agent it is more of a hindrance: it is the most abstract file, and its
decisions have already been carried over into the strategy.

| File | When the agent needs it |
|---|---|
| `vision.md` | Almost never. Only if you yourself ask it to check against the idea |
| `strategy.md` | When planning, arguing about scope, choosing the next task |
| `roadmap.md` | When slicing the backlog and during revision, prompts 4 and 7 |
| `backlog/README.md` | When choosing what to take next |
| `backlog/<feature>/README.md` | The whole time you work on that feature, in full and from the first message |

## Naming feature folders

In the template the folders are called `feature-1`, `feature-2`. When there are more than five
features, it is worth adding meaning to the number: `feature-1-mcp-tickets`,
`feature-2-kb-search`. The number keeps the order, the word makes the content clear without
opening the folder. The examples use exactly this variant.

The number is the slicing order, not the working order. The working order is set by the
dependencies in `backlog/README.md`.

## When some of this is not needed

**The tracker** (`backlog/TRACKER.md`) is needed when there are more than five features or when
you really keep several terminals going at once. With three features and one terminal, the
status column in `backlog/README.md` is enough. Creating both tables and maintaining one is
worse than not creating the second.

**Vision and strategy as separate files** are justified when the project is your own and you
will argue with it. If you take a course track as is and do not intend to change the idea,
merge both files into one short one and do not breed bureaucracy. But you will have to write
them in any case: at the defense the question "who is this for and why exactly this way" is
asked of everyone.

## What this skeleton does not do

It does not check that the project is feasible, does not watch the deadlines and does not stop
you from slicing a feature the size of a month. The form helps you not to lose the idea and not
to get in your own way in parallel work. The content is up to you.

Another typical mistake: describing everything down to the last feature and then not starting
a single one. The sign that it is time to stop and write code is simple. As soon as the vision,
the strategy, the roadmap and the first two features are described well enough to give them to
an agent, planning for this round is finished.

## How this skeleton covers the course program

The course project is assembled in layers: your own MCP server over data, context management and
RAG, agent roles and their interaction, moving to code, evals and observability, cost and
security. It is convenient to write the roadmap for this whole path at once, and to slice the
backlog as you go.

In the examples the roadmap covers the whole path, while the features are sliced only for the
first weeks. That is as it should be: the distant blocks are named in the roadmap but not yet
laid out into folders.
