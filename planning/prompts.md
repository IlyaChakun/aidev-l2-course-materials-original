# Prompts

Seven texts for seven steps. Each one is copied into the terminal whole. Whatever is in angle
brackets is replaced with your own content, brackets included.

The prompts are written for a coding agent working in the project repository (Claude Code,
Codex, Cursor and the like). The agent must see the files: all the prompts assume it can read
from and write to the repository.

Common to all seven: the agent is forbidden to make things up. This is not politeness but a
working constraint. A model that lacks data fills the gap with plausible invention by default,
and you will not notice it right away. The second common rule: synthesis and choice stay with
you, and the agent gets the questions, the formatting and the execution.

---

## 1. Vision

The first step, an empty terminal. Half an hour of conversation, five to seven sentences as
the result.

```
Help me formulate the vision of my course project. You ask the questions,
I formulate, you write it down.

The project, briefly: <two or three phrases in your own words>.
Template: docs/vision.md, read it, it describes the structure and the rules.

We work like this:
1. Questions first. One or two at a time, not a list of twenty.
2. You write nothing to the file until I say "write".
3. When no questions are left, you retell my idea in your own words.
   I confirm or correct it.
4. After confirmation you fill in docs/vision.md.

What should come out, four parts, five to seven sentences in total:
- the user and their world: a specific person in a specific situation and their pain;
- what it looks like when it works: not a list of features, but what their work looks like;
- why I am the one to do it: what I have that an outsider does not;
- what it will not be: what the system will refuse to do even when asked.

Constraints:
- Push for specifics. "Developers" is not a user, "a support on-call person
  in a team of four" is a user. Ask again after a vague answer.
- Do not accept the phrasings "an AI platform for X", "ten times faster", "a
  convenient assistant": they do not resolve a single dispute.
- Do not skip the fourth part about the boundary, even if I do not feel like writing it.
  Without it the scope grows silently.
- Do not invent an advantage for me. If I have none, write that down.

At the end: name two or three disputed decisions on my project and show how the
resulting vision resolves them. If it resolves none, say so
directly, and we rewrite it.
```

---

## 2. Product strategy

The second step. The agent will read this file at the start of every session, so it must be short.

```
We are putting together the product strategy. Read docs/vision.md and the template docs/strategy.md.

First ask me about what is missing. Then fill in the file.

Hard requirements for the result:
- Length is one screen, two minutes to read. The file is loaded into context on every task,
  and every extra two pages I pay for with every run.
- The "Current priorities" section: a numbered list, five items at most, the order
  matters. A list without order does not help you choose.
- The "Decisions made" section: the format is "we chose X over Y because Z". A decision
  without a reason we do not record: it will be revisited anyway.
- The "What it is and what it is not" section: in the second part, name the nearest classes
  of systems my project will be mistaken for and is not.
- A hypothesis with no way to check it is not a hypothesis. Either write what checks it, or remove it.

What we do NOT write into this file: architecture and diagrams, the list of features, deadlines,
the history of discussions, current metric values. There are other files for all of that.

When you finish, remind me to connect the planning files to the agent:
the ready-made block for the rules file is in planning/README.md, the section
"How to connect it to the agent".
```

---

## 3. Roadmap

The third step. "What product and why" has already been decided, here it is only "in which stages".

```
We are putting together the roadmap. Read docs/vision.md, docs/strategy.md and the template docs/roadmap.md.

The data I already have: <what it is and where it lives>.
How much time I am ready to spend: <hours per week> for <how many weeks>.

Questions first, then filling in, you touch the file after my "write".

Requirements:
- From five to ten functional blocks. More than fifteen means sliced
  too finely, fewer than four too coarsely. Every block must turn
  into a backlog feature: if it does not, it is written too generally.
- A stage milestone is checked by running it. "Document search is ready" is not a milestone,
  "given a question from the list, the system finds the right document and answers with a
  quotation" is a milestone.
- We fill in the "Data" section honestly. If there is no access to something yet, write that:
  it is the project's first risk, and it must move to the risks section of the strategy.
- Do not rewrite the sections about the user, positioning and stack here.
  They are already above, and three copies of one paragraph drift apart in the second week.
- If I answer "I don't know", that is not a reason for you to pick an option yourself. It is a reason
  to write a line into "Open questions" with the date by which it has to be closed.
```

---

## 4. Slicing the backlog

When the roadmap is filled in and you are satisfied with it.

```
Read docs/roadmap.md in full, and docs/strategy.md as well.

The task: propose a slicing into features. Only propose for now, do not create files.

The format of the proposal: a table with the columns "number", "feature name", "what it does
in one line", "depends on", "why this is a separate feature and not part of a neighboring one".

Slicing rules:
- One feature is something that can be brought to a working state in one to three
  sittings and checked by running it. A feature that takes a week is sliced too coarsely.
- A feature must not require another one to be built in parallel with it. If two things
  cannot be finished separately, they are one feature.
- Mark explicitly which features can be worked in parallel and which only in sequence.
- Mark the critical path: the chain in which a delay shifts the whole project.
- Do not slice the whole roadmap to the end. Take what covers the first <how many>
  weeks. List the remaining blocks separately, without slicing.
- Check against the strategy: if a feature does not serve any of the priorities,
  say so. Maybe it should not be done now.

After I accept the table, you create the structure: docs/backlog/README.md
from the template and the feature folders with empty READMEs from the template
docs/backlog/feature-1/README.md. Name the folders feature-<number>-<short name>,
for example feature-1-mcp-tickets: the number keeps the slicing order, the word makes
the content clear without opening the folder.
```

---

## 5. Filling in a feature README

One feature at a time. Do not ask for all of them at once: you will get ten identical texts.

```
We are filling in the README of feature <number>: docs/backlog/<folder>/README.md.

Read:
- docs/strategy.md (priorities and decisions made)
- docs/roadmap.md, block <block number>
- docs/backlog/README.md (dependencies)
- <project files that relate to this feature>

First ask me about what is missing. Especially about two sections:
"Boundaries" (what the feature does NOT include) and "Done when" (verifiable signs).
They are almost always filled in too generally, and they are exactly what determines the scope of work.

Requirements for the result:
- "Done when" is items each of which is checked by running a command
  or opening a screen. The phrasings "works correctly", "fast", "convenient"
  are not accepted: they cannot be checked, and one can argue about them endlessly.
- "Input and output" describe the contract for neighboring features: from it a neighboring
  feature must understand what it can use without reading the code of this one.
- The "Read before starting" section is no longer than five items.
- If you do not know something, write it into "Open questions", do not invent.

Fill in the file and show me the result.
```

---

## 6. Starting work on a feature

A new terminal, from the project root. The moment everything was described for.

```
We are working on one feature. Everything you need is in its folder.

Read docs/strategy.md, then docs/backlog/<folder>/README.md in full,
then what is listed in the "Read before starting" section.

The order of work:
1. You retell the task to me in your own words and name what you consider unclear.
2. We clarify what is unclear. You write the result into docs/backlog/<folder>/spec.md.
3. You break the spec into steps and write docs/backlog/<folder>/plan.md.
   A step is something after which the project stays in a working state.
4. You follow the plan, marking finished steps right in plan.md.
5. At the end you check the "Done when" items one by one and show what
   confirms each of them.

Constraints:
- You do not go beyond the "Boundaries" section. If you notice something needed outside it,
  write it as a line in docs/backlog/README.md, do not do it.
- If you doubt whether something should be added, look in docs/strategy.md, the section
  "What it is and what it is not". If the answer is not there, you ask me.
- You do not edit the files of other features. If a neighbor needs an edit, tell me.
- If you edit a shared file (database schema, config, dependencies), you immediately write a line
  into docs/backlog/TRACKER.md, the section "Change log for shared files".
  If there is no tracker, a line in docs/backlog/README.md.
- You commit only the paths of this feature. You do not use `git add -A`.
```

---

## 7. Revision after drift

In two or three weeks the plan stops matching the project. This is normal and gets fixed in one pass.

```
<how many> weeks have passed. Check the plan against what has actually been done.

Read:
- docs/vision.md, docs/strategy.md, docs/roadmap.md
- docs/backlog/README.md and TRACKER.md
- the READMEs of all feature folders
- git log for <period>

Tell me:
1. Which features are actually done but the status does not show it.
2. Which features are described but in the meantime have become unnecessary or changed
   beyond recognition.
3. What of what was done was not planned and is not described anywhere.
4. Which decisions made in the strategy contradict what is in the code.
5. Whether the priorities have changed in practice, and if so, to what.
6. What is worth slicing now from the "What is still ahead" section.

For each feature that is already done, ask three uncomfortable questions and answer them
yourself, relying on the code:
- why this part exists and who uses it;
- what breaks if it is removed entirely;
- what it costs to maintain compared with what it gives.

Do not edit files yet, show me the list of discrepancies. We will make the edits after
I decide which side is right: the plan or the code.
```

---

## What most often goes wrong

**The agent writes the vision from the first message.** That means the prompt was given in part or
the ban on writing before confirmation was removed from it. The text will come out smooth, and it
will contain your decisions that you did not make.

**The vision is beautiful but decides nothing.** The check at the end of prompt 1 exists for exactly
this case. If no disputed question is resolved by the vision, it is decoration, and it must be
rewritten, not left as it is.

**The strategy has grown to three pages.** It is read at the start of every session, and the extra
pages are paid for with every run. Everything that does not help make a decision today moves to the
roadmap.

**All the features are described, none has been started.** Planning is endless if it is not stopped.
The rule is simple: you have described two features well enough to give them to an agent, from here on we write code.

**The feature READMEs are filled in by rote.** A sign that they were all filled in at once with a
single request. The "Boundaries" and "Done when" sections are different for each feature, and they
are what gives the effect.

**A feature terminal reached into other people's files.** The constraint from prompt 6 works only if it
is in the prompt. Check before starting that you pasted it whole.
