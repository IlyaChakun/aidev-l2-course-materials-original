# AI editorial desk — roadmap

> Updated: 04.08.2026 · Vision: [`vision.md`](vision.md) · Strategy: [`strategy.md`](strategy.md) · Backlog: [`backlog/`](backlog/)

## What we are building

An editorial pipeline of three roles over an article database: the Writer writes a draft from a
brief, the Fact checker verifies claims and compliance with the editorial policy, the SEO
specialist prepares the meta tags. For whom and why exactly this way: [`vision.md`](vision.md)
and [`strategy.md`](strategy.md).

## Data

| What | Where it lives | Volume | Access |
|---|---|---|---|
| Articles | PostgreSQL, table `articles` | 20 records from the fixture plus our own | Yes |
| Editorial policy and tone of voice | Markdown files, collected by hand | 34 documents, about 90 pages | Yes |
| Archive of published pieces | The same table, status `published` | Grows over time | Yes |
| External sources for fact checking | Search API | — | Key available, free-tier limit not checked |

The last row is the first risk of the project, it is recorded in [`strategy.md`](strategy.md).

## Functional map

1. **Access to articles.** Our own MCP server over the `articles` table. The agent reads articles,
   creates drafts and moves them through statuses. The server does not perform an invalid
   transition.
2. **Editorial policy corpus and search over it.** The editorial policy documents are chunked and
   stored in a vector database. For a fragment of text, the relevant rules are returned.
3. **Three roles and their prompts.** Writer, Fact checker, SEO specialist. Each has its own
   system prompt, its own input and its own output format.
4. **End-to-end run and the assembly architecture.** A brief goes in, an article in the `checked`
   status with meta tags comes out. Linear, with no returns. This is also where we decide how the
   parts are connected: what calls the roles, where the run state lives, and what happens to an
   article if a step fails midway.
5. **Return for rework and memory.** The Fact checker returns the draft to the Writer with
   comments. What has already been fixed is saved between runs, so as not to go in circles.
6. **Moving the roles to a framework.** The roles move from plain functions to a graph of steps:
   explicit run state, retry of a failed step, rework rounds as part of the graph rather than a
   loop in the code.
7. **Quality evaluation.** A set of articles with a known answer, automatic evaluation of the
   result, run traces.
8. **Cost and security.** The cost of one article, a per-run limit, behavior under injection in a
   source text.
9. **Demo.** Five minutes: a brief, the three roles at work, return for rework, the finished
   article.

## What we honestly do not do

- Image generation for the article: not done, unrelated to the topic of the project.
- Working with several publications and different editorial policies: not done, one editorial
  policy.
- Interface: a stub. Everything goes through the CLI and the database, there will be no screen.
- Multi-user mode and permissions: a stub. One editor, no authorization.
- Publishing to the CMS: not done, the decision is recorded in the strategy.

## Stages

| Stage | What works at the end of the stage | Deadline |
|---|---|---|
| 1 | The agent from the IDE reads articles through the MCP server, creates a draft and moves it `draft` → `checked`. An invalid transition is rejected with a clear error | Week 2 |
| 2 | For a paragraph of a draft, search returns the applicable editorial policy rules with the document indicated | Week 3 |
| 3 | A brief goes in, an article with meta tags comes out, all three roles have run | Week 4 |
| 4 | The Fact checker returned a draft for rework, the second pass went through, the edit history was saved | Week 5 |
| 5 | There is a set of test articles and a report showing which of them the system gets wrong | Week 6 |
| 6 | The cost of one article is known, a limit is set, an injection in a source does not lead the agent astray | Week 7 |

## Open questions

- **How many rework rounds are allowed before an article goes to a human.** Close before
  feature 5 starts. Not decided yet, the hypothesis is two rounds.
- **The free-tier limit of the search API.** Close before feature 3 starts. We need to count the
  number of fact checks per article.
- **What to do with articles that already have a `score`.** In the fixture the score is filled
  in, but who sets it in the system and how has not been decided.

## Later

- A hint to the author right in the editor, instead of a separate report.
- A second editorial policy and switching between publications.
- Scoring an article by reads after publication and feeding it back into the Fact checker's
  evaluation.
