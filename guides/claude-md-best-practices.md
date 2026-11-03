# CLAUDE.md: best practices and review with an agent

> **A cross-cutting guide, outside the modules.** Self-contained: you can read it as a checklist, or you can put the whole thing
> into an agent's context, and it will review your rules file against the criteria in this guide.
> **Facts as of: 20.08.2026.** Update of 20.08: added sections on the mechanics of delivering the file
> to the model, the three levels of guarantees, phrasing techniques, anti-patterns, security,
> token economy and the global file. Unverified figures are marked [not verified].
>
> The guide is written using `CLAUDE.md` as the example, but the criteria are not tied to a tool: they are the same
> for `AGENTS.md`, `GEMINI.md`, `.cursor/rules/*.mdc`, `.github/copilot-instructions.md`
> and any other rules file. Wherever "rules file" is written below, substitute your own.

---

## How to use this file

**Way 1: a checklist for yourself.** Open the "Twelve criteria" section and go through your
rules file from top to bottom. About twenty minutes; it closes almost all the known ways of getting
"the rule doesn't work" without a single error message.

**Way 2: review with an agent.** Open the agent in the root of your project, give it this file
(in Claude Code, `@path/to/claude-md-best-practices.md`; in other tools, attach the file
or ask it to read it) and write:

```
Read this guide and review my project's rules file
following the "Instructions for the agent" section.
```

After that the agent works by the protocol in the next section: first it shows its review,
then it discusses the disputed lines with you one at a time, and only after that edits the file.

---

## Instructions for the agent

This section is addressed to the agent that the project owner has given the guide to and asked for a review.
Work strictly step by step, do not skip ahead.

**Scope of the review.** The review covers the **project** rules file: the file in the repository root
and, if present, nested files in subfolders and rules with path filters. The user
level, meaning files in the owner's home folder (`~/.claude/CLAUDE.md` and equivalents), is not part of this review:
do not read it and do not offer to edit it.

**Step 1. Find what to review.** Find the agent rules files in the repository: `CLAUDE.md`,
`AGENTS.md`, `GEMINI.md`, `.cursor/rules/`, `.github/copilot-instructions.md`, `.junie/`,
`.devin/rules/`, `.windsurf/rules/`. List everything you found to the owner, with size in lines.
If there is no rules file at all, say so and offer to build one from scratch: first a map
of the repository, then a draft against this guide's criteria, then questions to the owner about
what cannot be seen from the code. After that, the same steps 3–4.

**Step 2. Preliminary review.** Run the main file through the "Twelve criteria"
and the "Anti-patterns: what not to do" section below and show the result as two tables, without edits:

1. A summary by criterion: `criterion → verdict (met / partly met / not met) → one phrase on why`.
2. Line-by-line findings: `line or group of lines → what is wrong with it → by which criterion`.
   This is where duplicates, contradictions, code retellings, general practices and dead links go.

Review rules: verify every claim about the project by reading the code, not by assumption;
give verdicts with a justification, without praise and without softening; if the file is good, say so
and name what exactly works in it.

**Step 3. Brainstorm with the owner.** Do not dump all the questions at once. Go from the most expensive
finding to the cheapest and for each ask **one question at a time**: is this line needed,
and if it is, where does it belong. Offer the answer options yourself: keep as is · rewrite more
specifically · move to a rule with a path filter · move into a separate reference
and leave a link · delete. Listen to the answers: the owner knows things about the project that are not in the code,
and their "this rule is needed, the agent makes mistakes without it" outweighs any criterion.
Ask separately: which mistakes has the agent already repeated in this project? Each such mistake is
a candidate for a new line in the file.

**Step 4. Edits.** Assemble the new version of the file. Show the owner a "before → after" diff
**before writing to disk** and apply it only after confirmation. At the end show: the resulting file,
a list of what was moved where, and how many times shorter or longer the file became. If new rules
were written by hand as a result of the brainstorm, check each against the test in criterion 2.

---

## Twelve criteria

### 1. Size and weight are known

The vendor's guideline is **up to 200 lines**: "Longer files consume more context and reduce
adherence". It is a recommendation, not a limit, but it has a mechanism: a bloated file drowns out
the needed rules too. The weight is worth knowing in tokens, not lines: the context inspection command
(`/context` in Claude Code and equivalents) prints your number; a reasonable guideline is up to 2% of the window.

### 2. Every line passes the test "if I remove it, will the agent start making mistakes?"

The vendor's test for every line of the file. If the answer is "no", the line is redundant, and it is not free:
"If your CLAUDE.md is too long, Claude ignores half of it because important rules get lost
in the noise. Fix: ruthlessly prune". A semi-automatic aid in Claude Code is the `/doctor` command.

Two more tests that a rule works at all. The test task: a fresh session, a small
task that should trigger the rule; a rule that has never changed behavior is
decoration, and decoration costs tokens. The weekly log: if you manually repeat to the agent what
is already written in the file, the rule is not getting through, usually because of the file's length.

### 3. No retelling of the code or of common knowledge

Anything the agent derives by reading the code in a single pass does not live in the file: directory structure,
the list of dependencies, standard language conventions, "write tests", "don't commit secrets".
The file is useful exactly where it carries what exists nowhere else: non-obvious gotchas, the reasons
behind prohibitions, team agreements, the domain vocabulary.

### 4. The structure reads like onboarding for a new engineer

A working scheme is **WHY / WHAT / HOW**. WHY: why the project exists and why each
part of it exists. WHAT: the stack, the structure, what lives where. HOW: how to work: commands, conventions,
the order of delivery. `/init` gives a skeleton; the official wording is "Treat it as a starting
point": autogeneration is a draft, the value is added by rules written by hand.

### 5. Rules are specific and verifiable

The verb first, then the constraint. Three pairs from the vendor's documentation:

Bad: "Format code properly" → good: "Use 2-space indentation"

Bad: "Test your changes" → good: "Run `npm test` before committing"

Bad: "Keep files organized" → good: "API handlers live in `src/api/handlers/`"

The check: a rule can be followed or violated. "Write clean code" can be neither.

### 6. A rule has a reason, a prohibition has an alternative

A failure mode next to the rule makes the rule sticky: "don't call `db.query` from handlers:
the pool is per-request, connections leak; go through `repositories/`". And every "never"
should have an "instead": a prohibition without an alternative makes the agent stop
and ask, or silently invent a workaround.

### 7. No contradictions

A conflict costs more than length: the model spends attention on resolving the contradiction before
it gets to the task. This is exactly what the vendor named the main harm when, in July 2026, it removed more than
80% of its own product's system prompt "with no measurable loss": a single request
contained both "leave documentation as appropriate" and "DO NOT add comments". The check is mechanical:
search for `never`, `always`, `do not`, and go through the pairs by eye to see whether they argue with each other.

### 8. The important things are at the top

Truncation and context compaction preserve the beginning of the file. Critical prohibitions and the most expensive
rules go in the first lines, reference material below.

### 9. "Sometimes" content is moved out, the file keeps pointers

Only what is needed on every request lives in the permanent context. The rest is moved out,
and each move-out has its own address: a rule about part of the tree goes into a rule with a path filter
(`paths:` / `globs:`); a procedure goes into a skill ("Procedures belong in skills. CLAUDE.md is for
facts Claude should hold all the time"); a long reference goes into a separate file, and the rules file gets
a pointer line with a link and a note on when to look there. This is the **progressive
disclosure** technique: the agent reads the details at the moment they are needed, not on every launch.
The architecture diagram and ADRs of your course project are connected exactly this way.

### 10. Levels are not mixed up

Project things go in the project file, which is in git and shared by the team. Personal things go in local memory
(`CLAUDE.local.md` and equivalents), which is in gitignore. Habits "for all projects" go on the
user level in the home folder, and do not belong in the project repository. A symptom
of mixed-up levels: "answer me in Russian" or paths with your username
in the project file.

### 11. The file is alive, not written once

The threshold for adding: the agent **made a mistake in the same convention a second time**, so that is a line for the file.
The threshold for pruning is criterion 2. A working self-maintenance technique: the instruction "update the module's
rules file after working on it" in a rule with a broad path filter: it gets pulled in
exactly when the agent has touched the code, and is not lost by the end of a long session.

### 12. The file survives a model change

Verbatim from the documentation: "instructions that worked around an older model's limitation may
become overhead once a newer model handles the case on its own". After a model change or a
major version of the tool, the file is re-read: some workaround rules have become redundant,
some links dead. The link check: every path and file mentioned still exists.

---

## Why rules get ignored: the delivery mechanics

So that the criteria above do not look like magic, it is useful to know how the file reaches the model.

**The rules file is not a system prompt and not configuration.** It arrives in the model as an ordinary
user message after the system prompt, wrapped in a reminder "this context may or may
not be relevant to your tasks". On every turn the model decides for itself whether this piece of text is relevant
to the current task. All the behavior follows from this: specific, action-bound rules are followed,
vague wishes are filtered out, there are no guarantees. This is the foundation of criteria 2, 5 and 9.

**Ignoring rules is a documented systemic pattern**, not just "you wrote it badly":
open issues anthropics/claude-code #37818 and #36492, practitioners' confirmations "even 5 lines
guarantee nothing". The right reaction to non-compliance is not to add a third rule about the same
thing, but to work out why the existing one does not work.

**An extra rule does not get "lost at the end": it dilutes all the others evenly.** And sections
relevant only to one subsystem, while you work on another, teach the model to consider the whole file
irrelevant, including the rules that do apply.

**After `/compact` only the root file is re-read.** Nested files and rules
with path filters are lost until the next touch of their files. A long session is the main
killer of compliance: after several compacts the file noticeably loses influence. One more argument
for "one task, one chat".

**`@` imports do not save context.** What is imported is loaded in full at startup, with depth
up to 4 hops; this is an organization technique, not a saving. What saves are rules with `paths:` (loaded when
a matching file is touched), skills (only name+description is always loaded) and moving content out
into a separate file with a pointer line.

**Levels are concatenated, not overwritten.** All rules files are concatenated; on a direct
conflict the documentation honestly says "Claude may pick one arbitrarily": the behavior is
nondeterministic. So contradictions between levels cost more than contradictions within a file:
they are harder to notice. A check that the file was loaded at all: `/context` → the Memory files section.

**Cross-tool gotchas.** Claude Code does not read `AGENTS.md`: you need a symlink
(`ln -s AGENTS.md CLAUDE.md`) or an import line `@AGENTS.md`. In Cursor a plain `.md`
in `.cursor/rules/` is silently ignored: only `.mdc` works. If the team uses
different tools, one file is made the source of truth and the others are symlinks.

---

## Three levels of guarantees: rule, skill, hook

A working formula: **a rule in the file is a request, a skill is a procedure, a hook is a guarantee.**

The rule "always run the linter after an edit" lives exactly until a long session or a compact:
after that the agent forgets it, and this is normal behavior, not a failure. Everything that has to
run every time without exception moves out of text into mechanisms:

- **code style** goes into the linter and formatter, not into prose (see anti-pattern 2 below);
- **prohibitions on actions** go into a `PreToolUse` hook or permissions deny: they are enforced
  by the system, not the model, and do not depend on whether the model "remembered" the rule;
- **post-processing** goes into a `PostToolUse` hook (auto-formatting after a file write);
- **the definition of "done"** goes into a `Stop` hook, which does not let the agent finish
  with red tests.

The working architecture of experienced teams: a short rules file + rules with path filters +
skills for procedures + hooks for guarantees. In this scheme the rules file is responsible only for
what must always be in the agent's head: facts, boundaries, the domain vocabulary.

---

## Phrasing techniques: what to do

A supplement to criterion 5: six techniques with "weak → strong" pairs.

**Commands with exact flags, not names of actions.** The agent will not guess your non-standard
port, test runner and flags.
- Bad: "We use pytest for tests"
- Good: "Tests: `pytest --tb=short -q`. One file: `pytest path/to/test.py -q`. Green means
  0 failed, warnings are acceptable"

**Three permission levels stated explicitly: Always / Ask first / Never.** What matters to the agent is not only
the "forbidden" boundary but also the "ask" boundary.
- Bad: "Be careful with migrations"
- Good: "Allowed without asking: editing code and tests. Ask first: new dependencies, schema migrations.
  Never: `git push --force`, edits in `vendor/`; instead describe the problem in the PR"

**Gotchas with the mechanism of breakage, not a statement of fact.** A rule with a reason survives more
sessions and compacts (this is criterion 6 in action).
- Bad: "The Header component is fragile, be careful"
- Good: "Do not change `display`/`position` on Header: last time it broke the mobile layout.
  After any nav edit, run `npm run test:mobile`"

**A pointer instead of pasting, `file:line` instead of a snippet.** Pasted code goes stale
on the first refactor; a navigation line does not have this problem.
- Bad: `@docs/architecture.md` (loaded in full at the start of every session)
- Good: "For architecture questions, read `docs/architecture.md`. The authorization scheme is at
  `src/auth/middleware.ts:40`"

**Behavior under uncertainty.** One of the most underrated classes of rules: what to do
when the agent does not know.
- Good: "If you don't know, say "I don't know", don't guess. If a requirement is ambiguous, ask one question
  rather than make a silent assumption"

**The definition of "done".** Without it the agent declares victory after the first compile.
- Good: "A task is finished when: tests are green, `npm run lint` is clean, the diff does not touch files
  outside the task"

---

## Anti-patterns: what not to do

A supplement to the "what to include / what not to include" table, with the mechanism for why it does not work.

1. **Role incantations** ("You are a senior software engineer with 20 years…"). Tokens with no
   influence on behavior: the system instructions already set the role, and behavior is changed only by
   verifiable rules.
2. **Duplicating the linter in prose** ("don't use var", "semicolons are mandatory").
   Deterministic work is done by a deterministic tool; a rule in prose is slow,
   expensive and without a guarantee. The file keeps only what the linter cannot express.
3. **"Just in case" rules**: for tasks that have not yet occurred in the project. When real
   rules are mixed with speculative ones, the model weighs them equally and follows
   none. The file grows from actual mistakes, not from fantasies about them.
4. **Sections about one subsystem in the root file.** The mechanism is in the delivery section:
   it teaches the model to skim the whole file. The address for such sections is a nested file
   or a rule with a path filter.
5. **Current state and changelog** ("Current Sprint", "added rule on 12.03", migration
   statuses). It goes stale by next week; history is git's job.
6. **Secrets and private URLs.** The file goes to the model every session and is visible to the whole team
   through git; local things go in `CLAUDE.local.md` in gitignore, real secrets go nowhere.
7. **Emphasis on everything.** "IMPORTANT" works as long as it is alone. When every second rule is
   IMPORTANT/NEVER/ALWAYS, the weight of the marker drops to zero.

---

## Security: the rules file is an attack surface

A pull request that edits `AGENTS.md`/`CLAUDE.md` changes the instructions of the agents of everyone who
works with the repository. A nested rules file in a subfolder intercepts agents when they
touch that folder: "the nearest wins". So rules file diffs are reviewed harder than
code: these are executable instructions, not documentation. There are no secrets in the file for the same
reason: it goes in full to the model every session.

---

## Token economy: where it exists and where it does not

The main conclusion: **there is almost nothing to save in the rules file itself**: the right file is small.
The real levers are next to it.

**Command output is where tokens really burn.** Compact command pairs in the rules:

```
git status → git status --porcelain
git log    → git log --oneline -20
git diff   → git diff --stat first
pytest     → pytest --tb=short -q
long output → ... 2>&1 | tail -30
```

**Scoping instead of compression.** Rules with `paths:` filters instead of one big file
([not verified] in one vendor case, -41% of always-loaded context, methodology not published);
unused MCP servers turned off: their descriptions go into every request whether
or not you use them.

**Offloading through skills.** An illustrative case (a public breakdown of a .NET monorepo): 564 lines
of a monolithic file → 7 skills + a 23-line rules file, -82% of always-loaded
context, while the total volume of procedural knowledge grew. The dividing line: principles
in the file, procedures in skills.

**A session handoff instead of a diary in the file.** At the end of a long session the agent writes a note
"what was done, what decisions, what is next", and the next session starts from it. Context
is restored for a fraction of the tokens, and the rules file does not turn into a journal.

**What not to do:** compress rules into a telegraphic style without connectives and explanations: it trades
the readability of the whole team for pennies; a rule without a reason is also followed worse (criterion 6).
Among the curiosities: [not verified] "prompts in Chinese for token density" is folklore, unmaintainable;
[not verified] "HTML comments in the file are free" has no confirmation, consider it false.

---

## The global file: `~/.claude/CLAUDE.md`

The selection principle: **information about you goes in the global file, information about the project in the project file.**
Anything that contains the stack, paths or conventions of a specific repository is noise in the global file,
and will travel into all your projects. The level test: a rule that may be wrong in at least
one of your projects is not global ("prefer Tailwind" will fire even where Tailwind is
forbidden). Keep the file short: it is a tax on every session of every project.

Candidate rules from practitioners' public examples, with a note on why:

| # | Rule | Why |
|---|---|---|
| 1 | "Never create a git commit unless I explicitly ask for one" | The agent does not commit what you have not seen |
| 2 | "Prefer non-interactive commands: `git --no-pager diff`, flags instead of prompts" | Interactive commands hang the agent session |
| 3 | "Make the smallest useful diff. No unrelated improvements unless asked" | Cures the "refactored while I was at it" habit |
| 4 | "Always raise errors explicitly; no fallbacks or silent recovery unless I ask" | A stub instead of an error hides bugs |
| 5 | "If you don't know, say "I don't know". If ambiguous, ask one question, don't guess" | Turns off silent defaults |
| 6 | "Before destructive commands (rm, reset --hard, drop) — ask and show what will be lost" | A user-level safety net, across all projects |
| 7 | "Answer in Russian; code, commits and identifiers in English" | The language pair is set once |
| 8 | "No praise, no apologies, answer the question asked" | Communication style is personal, not project |
| 9 | "Use strict typing; no `Any`/`unknown` unless unavoidable" | A personal quality standard on top of projects |
| 10 | "Error messages must say what failed, why, and include params/status" | Debuggability by default everywhere |
| 11 | "My projects: active ones in `~/projects/active/`, experiments in `~/projects/playgrounds/`" | The agent stops asking for paths |
| 12 | "Before tests, use short flags (`--tb=short -q`); pipe long command output through tail" | User-level token hygiene |

Check your `~/.claude/CLAUDE.md`: most people do not have one, or it holds junk
from autogeneration. Put together 5 rules from the table for yourself: that is cheaper and more useful
than copying all twelve.

---

## Where opinions differ

An honest map of the disputes, so that someone else's confident blog post does not look like the truth.

1. **Critical rules at the top or at the bottom of the file.** "The important at the top" (criterion 8: truncation
   and compaction preserve the beginning) versus "recency bias: the model weighs the end of the
   context more heavily". There is no official recommendation. A practical synthesis: the file is so short
   that the question does not arise.
2. **`/init`: generate or not.** The documentation: "treat it as a starting point".
   Some practitioners: "don't use it at all". The ETH study is on the skeptics' side
   (LLM-generated files -3% to solve rate, +20% to cost). A working synthesis: a draft →
   cut half by hand. More radical: start from an empty file and grow it by one line per mistake.
3. **Length thresholds.** 200 lines (official) vs [not verified] 80 lines vs [not verified] 60 lines vs [not verified] "500 tokens":
   the only official figure is 200, the rest are extrapolations with no published methodology.
   [not verified] An analysis of 2500+ repositories with AGENTS.md: the median of working files is 300–350 words, after
   1000 words the correlation with performance is negative (methodology not checked).
4. **Skills vs rules.** A practitioners' observation: "skills fire by description better than
   rules are followed": skills have a different loading mechanism. The counter-argument: a skill fires
   only on a description match, while a rule with `paths:` fires deterministically on a file touch.
   The choice depends on which is worse: a miss or an unnecessary load.
5. **Compressing output through rules** ("no praise, answer only what's asked": [not verified] up to -63% of output
   words on a tiny benchmark). The skepticism: forced brevity may cut the quality of
   reasoning. For pipeline tasks, yes; for research tasks, with caution.

---

## What to include and what not to include

A condensed official table, handy as a quick filter when going through line-by-line findings:

| Include | Do not include |
|---|---|
| bash commands that cannot be guessed | anything derived by reading the code |
| style rules that differ from defaults | standard language conventions |
| how to run tests and what counts as "green" | detailed API documentation (a link instead) |
| branch, commit and pull request conventions | anything that changes often (versions, dates, statuses) |
| architectural decisions and their reasons | per-file descriptions of the repository |
| env variables and non-obvious gotchas | "write clean code" and other wishes |

---

## What backs this up

- **The only peer-reviewed study** [ETH Zurich, arXiv:2602.11988, ICLR 2026
  Workshop; 138+300 tasks, 4 agents]: LLM-generated context files **reduce** the success
  rate by 3% on average and raise inference cost by 20–23%; human-written ones raise it
  by 4%. The mechanism: agents follow instructions rather than ignore them, so extra requirements
  make the task harder. Limits of the measurement: Python only, 23 repositories. The takeaway for
  practice is not "the file is not needed" but "autogeneration without manual refinement is harmful".
- **The vendor's admission** [Anthropic blog, 24.07.2026, internal evals]: more than 80% of
  the Claude Code system prompt was removed without a measurable loss of quality; "we were overconstraining
  Claude Code, both through our system prompt and in our CLAUDE.md files and skills".
  The named mechanism of harm is contradictions, not tokens.
- **The 200-line recommendation** is from the [Claude Code documentation, the
  Memory section](https://code.claude.com/docs/en/memory), where you will also find the test "Would removing this cause
  Claude to make mistakes?" and the "what to include" table.

Additional sources for the new sections (viewed 20.08.2026):

- https://code.claude.com/docs/en/best-practices — the line test, "bloated files cause Claude to ignore"
- https://claude.com/blog/steering-claude-code-skills-hooks-rules-subagents-and-more — "Procedures belong in skills", the owner for the rules file
- https://www.humanlayer.dev/blog/writing-a-good-claude-md — the system-reminder wrapper, the instruction budget
- https://tianpan.co/blog/2026-02-14-writing-effective-agent-instruction-files — Always/Ask/Never, recency bias, median 300–350 words
- https://getunblocked.com/blog/audit-fix-bloated-claude-md/ — auditing the file, test tasks for a rule
- https://www.openhands.dev/blog/claude-code-best-practices-agentic-coding — "start the file late"
- https://www.firecrawl.dev/blog/claude-code-token-efficiency — paths scoping, .claudeignore
- https://agents.md — the AGENTS.md standard
- https://github.com/anthropics/claude-code/issues/37818 and /issues/36492 — ignored rules as open issues
- https://arxiv.org/abs/2602.11988 — ETH Zurich, "Evaluating AGENTS.md", ICLR 2026 Workshop

A "before → after" pair from the same story: the shift is visible in five seconds:

> **Before:** "In code: default to writing no comments. Never write multi-paragraph docstrings
> or multi-line comment blocks: one short line max."
>
> **After:** "Write code that reads like the surrounding code: match its comment density,
> naming, and idiom."

One principled sentence instead of a list of prohibitions, and it does not break in a repository
where the docstring is part of the house style.
