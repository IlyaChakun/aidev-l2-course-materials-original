# 3 · Three roles

**Status:** `spec` · **Waits for:** 1, 2 · **Blocks:** 4

## What it does

Describes and debugs three agents: the Reviewer, the Tester and the Documenter. Each has its own
system prompt, its own input and its own output format. For now the roles are launched
separately, feature 4 connects them.

## Why

The roles solve different tasks and err in different ways. The Reviewer tends to nitpick style,
the Tester to write tests for everything, the Documenter to retell the code in words. Each of
these tendencies has to be suppressed separately, and doing it in the assembled system is more
expensive.

## Input and output

| | |
|---|---|
| **Input** | The MCP server from feature 1, the search from feature 2, the 20 fixture tasks |
| **Output** | Three system prompts in `prompts/`, each with a JSON schema for its output. A script that runs any role on a given task |

Contracts between the roles:

| Role | Input | Output |
|---|---|---|
| Reviewer | The diff, the conventions and discussions found | A list of comments: file, line, gist, type, severity, link to the rule |
| Tester | The diff, the Reviewer's comments | Draft tests for new and changed functions, a list of what is not covered |
| Documenter | The diff, the comments, the tests | Updated docstrings and a README fragment, only for the affected places |

## Boundaries

- Orchestration of the roles: out of scope, that is feature 4.
- A second round for risky changes: out of scope, that is feature 5.
- Running tests: not done, a decision from the roadmap. Tests are only generated.
- Tests for untouched code: not done, decision of 04.08.
- Automatic fixing of what is found: out of scope.

## Done when

- [ ] Each role runs on any fixture task with one command
- [ ] The output of each role passes JSON schema validation on all 20 tasks
- [ ] Every Reviewer comment has a file and a line, and they exist in the diff
- [ ] A style comment always links to a convention, otherwise it is not issued
- [ ] The Tester does not write tests for functions that are not in the diff
- [ ] The Documenter does not touch README sections unrelated to the change
- [ ] No role goes to the database directly, only through the MCP server

## Read before starting

- `../feature-1-mcp-review-tasks/README.md`: the tool set
- `../feature-2-repo-context/README.md`: what the search returns
- `docs/conventions/README.md`: the project conventions
- `../../roadmap.md`, blocks 3 and 5

## Open questions

- **False comments.** The Reviewer issues a lot that is correct but unimportant. We need a way
  to cut the noise: either a severity threshold or a limit on the number of comments. Not
  decided.
- **Who computes the risk.** So far it was assumed to be a separate step before the Reviewer.
  Possibly it is a fourth role, and then the contract changes.
- **Test format.** A draft in a separate file or a patch to an existing test file. The second is
  more useful and harder.
