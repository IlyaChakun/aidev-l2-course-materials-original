# DevTools assistant — product strategy

> Updated: 04.08.2026 · Vision: [`vision.md`](vision.md) · Roadmap: [`roadmap.md`](roadmap.md)

## Who it is for

A developer on a team of six on one repository. Reviews sit for two days, the conventions are
described in twelve documents that nobody rereads, and documentation is updated on a leftover
basis.

## What it is and what it is not

**It is:** a first pass over a change: comments on conventions, draft tests, updated docstrings,
all with links to the project's rules.

**It is not:** a linter (we analyze the meaning of the change, not the syntax), not a bot in a
pull request (there will be no integration with the hosting), and not a test generator for the
whole repository (we work only with the diff).

## Stage

A prototype on a learning repository. For the defense we need an analysis on real changes with a
known share of defects found and a known share of false comments.

## Current priorities

1. Comments that link to a specific convention. A general-form comment is valid for any project
   and useless for this one.
2. Noise cutoff. A reviewer who gets forty correct but unimportant comments stops reading all of
   them.
3. Working with a real diff, not with the textual description of a change from the fixture.
4. Routing by risk: fixing a typo and changing authorization should not cost the same.

## Decisions made

| Date | Decision | Why |
|---|---|---|
| 30.07 | Take the track as is | The data and statuses are ready, time goes into the system, not into inventing a domain |
| 30.07 | Stay on SQLite | The tool is local and single-user. PostgreSQL would add a container and give nothing |
| 01.08 | Risk is computed before the review, not derived from the number of comments | Risk is needed to decide how closely to look. After the comments it is useless |
| 02.08 | Past discussions are indexed together with the conventions, but marked with a separate type | A discussion is a precedent, not a rule. It can be cited, but differently |
| 04.08 | The Tester writes tests only for new and changed functions | Nobody reads tests for a whole file, and they clutter the diff |
| 04.08 | Running the generated tests is not done | It is a separate infrastructure for a week, and adds nothing to the core of the project |

## Risks

| Risk | What we do |
|---|---|
| Changes over a thousand lines do not fit in the context | Decide before feature 4: split by files or refuse with a clear error. Silent truncation is not allowed |
| False comments clog the output and people stop using it | A severity threshold or a limit on the number of comments. Measure the share of false ones from feature 3 |
| Half of the past discussions are "fix this here" with no context | Filter by length or label by hand. A junk corpus is worse than an empty one |
| Search by file path works badly, because a path is not text | Metadata with paths instead of text similarity |

## Hypotheses to check

- An author accepts a comment with a link to a convention and argues with one without a link.
  Checked on: the first twenty comments on real changes.
- Discussions from past reviews provide what the convention documents lack. Checked on: the share
  of comments that rest on a precedent rather than on a rule.
- Risk computed before the review correlates with the number of defects found. Checked on a set
  of changes with known problems in the quality evaluation block.

## What this file does not contain

Architecture and diagrams, the list of features and deadlines, the history of discussions, current
metric values.
