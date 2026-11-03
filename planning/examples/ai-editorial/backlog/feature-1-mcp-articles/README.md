# 1 · MCP over articles

**Status:** `done` (03.08) · **Waits for:** none · **Blocks:** 3, 4

## What it does

Our own MCP server over the `articles` table. The agent from the IDE sees articles, creates a
draft, appends text and moves the article through statuses. The lifecycle rules live in the
server: `draft` cannot be moved straight to `published`, and the agent gets a rejection with an
explanation, not a silent success.

## Why

This is the only way all the other parts of the system touch articles. Without it each role would
reach into the database with its own code, and the transition rule would have to be repeated in
three places.

## Input and output

| | |
|---|---|
| **Input** | PostgreSQL with the track fixture loaded: table `articles`, 20 records |
| **Output** | An MCP server in Python: 5 tools, 1 resource with the database schema, 1 resource template `db://article/{id}`. A rejection on an invalid transition with a code and a reason text |

Tools: `list_articles`, `get_article`, `create_draft`, `update_body`, `advance_status`.
The other features work with articles only through them.

## Boundaries

- Authentication and roles: out of scope, will come separately in the security block.
- Full-text search over articles: out of scope, filtering only by status and section.
- Deleting articles: out of scope, there is no scenario for it.
- Working with the editorial policy: out of scope, that is feature 2.

## Done when

- [x] The server starts with one command and is visible in MCP Inspector
- [x] `list_articles` with a status filter returns the same number of records as a `SELECT` on the database
- [x] `advance_status` takes `draft` → `checked` → `published`
- [x] An attempt at `draft` → `published` is rejected, the response names the current status and the allowed ones
- [x] A transition attempt on a nonexistent `id` is rejected, with an error different from the transition error
- [x] The server is connected in the IDE and the agent takes an article through the cycle without hints in the prompt

## Read before starting

- `M1/starter-server/python/README.md` in the course repository: the skeleton we started from
- `M1/fixtures/ai-editorial/` in the course repository: schema and data
- `M1/guides/tool-design.md` in the course repository: the tool set and the error contract
- `../../roadmap.md`, block 1

## Open questions

- Closed 02.08: whether to return `published` back to `draft`. We decided not to; withdrawing a
  publication is done with a new version of the article. Recorded in the roadmap.
- Remaining: `update_body` currently overwrites the whole text. With the rework rounds in
  feature 5 a version history will be needed, and the tool will have to change. Noted so as not
  to forget.
