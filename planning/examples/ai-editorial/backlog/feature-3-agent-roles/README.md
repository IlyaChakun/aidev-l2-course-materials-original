# 3 · Three roles

**Status:** `spec` · **Waits for:** 1, 2 · **Blocks:** 4

## What it does

Describes and debugs three agents: the Writer, the Fact checker and the SEO specialist. Each has
its own system prompt, its own input and output format and its own area of responsibility. For
now the roles are launched separately, by hand: feature 4 connects them.

## Why

The three roles are the core of the project, and a mistake in dividing the roles later shows up as
puzzling behavior of the whole system. It is cheaper to debug each one separately on live
articles from the fixture than to catch the mistake in the assembled system.

## Input and output

| | |
|---|---|
| **Input** | The MCP server from feature 1, search over the editorial policy from feature 2, the 20 fixture articles |
| **Output** | Three system prompts in `prompts/`, each with a JSON schema for its output. A script that runs any role on a given article |

Contracts between the roles:

| Role | Input | Output |
|---|---|---|
| Writer | A brief: topic, section, key points | A draft article, status `draft` |
| Fact checker | A draft | A list of comments: claim, type (fact or tone), link to a source or rule, severity |
| SEO specialist | The article text | Title, description, key phrases, markup |

## Boundaries

- Orchestration of the roles: out of scope, that is feature 4.
- Return for rework: out of scope, that is feature 5. Here the Fact checker only issues comments.
- Text editing by the Fact checker: deliberately not done, decision of 03.08. The Writer edits the text.
- Choice of framework: out of scope. For now the roles are plain functions, moving to graph
  execution is block 6 of the roadmap.

## Done when

- [ ] Each role runs on any fixture article with one command
- [ ] The output of each role passes validation against its JSON schema on all 20 articles
- [ ] On an article with a deliberately corrupted fact, the Fact checker finds it and cites a source
- [ ] On an article with a tone violation, the Fact checker cites a specific section of the editorial policy
- [ ] The SEO specialist stays within the limits on title and description length
- [ ] No role reaches into the database directly, only through the MCP server

## Read before starting

- `../feature-1-mcp-articles/README.md`: the tool set
- `../feature-2-style-corpus/README.md`: what the search returns
- `../../roadmap.md`, blocks 3 and 5
- `corpus/style/README.md`: the structure of the editorial policy

## Open questions

- **Comment severity.** Three grades or two. It affects feature 5: the grade determines what
  sends an article to a second round and what is simply written into the report. Not decided.
- **Key phrases.** Set by the editor in the brief or proposed by the SEO specialist. For now it
  proposes them itself, but on a couple of topics the result missed.
- **Order of the Fact checker and SEO.** Currently SEO is assumed to work after the fact check.
  If the Writer rewrites half the text after the comments, SEO will have to be run twice.
