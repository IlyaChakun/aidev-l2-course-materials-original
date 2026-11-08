# M1: test scenarios

The expected result of each scenario is written in [expected/](expected/) and committed **before** the run (see the git history: the commit with the expectations comes before any run logs). After a run the expectations are not edited; any mismatches are described separately in `report.md`.

Preparation before each scenario: `make db-reset db-seed` (a fresh set of 20 tickets).

## A. The part 1 scenario from an IDE client (task 1, "Check 2")
Client: OpenCode (whether it counts as an "IDE" for the course is to be confirmed with the teacher). Connection: a local MCP server, command `scripts/server-stdio.sh`, environment `SUPPORT_DB_PATH`.
The agent is given **a goal, not a list of calls** (no manual hints during the dialog): "Using the support-tickets MCP server, take tickets 5 and 6 through the lifecycle and show that the server does not let you break the order of statuses. Ticket 5: answer it, then try to move it back to new, then escalate it, then try to answer it again. Ticket 6: try to answer it without the answer text, then correct yourself."
Expectation: [expected/ide-scenario.json](expected/ide-scenario.json) (8 steps: resource, list, read, success, rejection with `allowed_transitions`, fix based on the hint, rejection on the final status, rejection for a required field and a fix). The behavior is checked too: the agent reads the ticket by itself before writing, corrects itself based on the hint, and stops at the final status. If the agent mixes up the order or ignores a tool, the tool descriptions are edited, not the code; the chain of edits goes into `process-log.md`.
