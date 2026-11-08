# M1 · MCP lecture: the three demos, step by step

Everything you need to repeat the MCP demos from the lecture on your own machine: commands, prompts, expected responses and what to do when something goes off track.

**How it was verified (30.10.2026).** All three demos were run end to end on the `smart-support` server from [`../../smart-support/`](../../smart-support/):
- demo 2 — in the Inspector 2.13.0 web UI, following the steps in section 3;
- demos 1 and 3 — in Claude Code 2.1.287 (model Opus 5.5) with the same flags, folders and prompts as below. Demo 1: 2 runs on each version; demo 3: 2 full P1–P4 runs.

The responses and DB rows below were captured from those runs. The model is non-deterministic: for each step the acceptable outcomes are described.

| Demo | What it shows | Where |
|---|---|---|
| 1 | Bad vs good error, A/B | Claude Code, two windows |
| 2 | The protocol "under the hood" | MCP Inspector in the browser |
| 3 | The agent moves a ticket through the statuses on its own | Claude Code + `sqlite3` |

Files alongside:
- `demo-setup.sh` — brings up the whole environment with one command (section 1);
- `demo1-no-hints.patch`, `demo1-bad-error.patch` — two versions of the server for demo 1 (section 1.4).

And in [`../inspector/`](../inspector/) — an Inspector stand in Docker (sections 1.3 and 5):
- `Dockerfile`, `compose.yaml` — Inspector 2.13.0 and the servers from the [overview of 13 MCP servers](../top-mcp-servers.md), preinstalled in the image;
- `catalog.template.json` — the server list that Inspector shows right after start;
- `own-server/faq_server.py` — the smallest own server; `support-tickets` is connected from `~/sts-demo/sts-m1`;
- `check.sh` — a stand check: one real call per server.

**You need:** [uv](https://docs.astral.sh/uv/) (it installs Python 3.13 itself), `sqlite3`, `make`, [Claude Code](https://docs.claude.com/en/docs/claude-code) or another MCP client, Node.js for `npx`. Docker only for the Inspector stand.

---

## 0. What to know in advance

1. **Do not run the agent inside the project folder.** Claude Code with its regular tools reads the source: in a test run it opened `status_graph.py`, the DB schema and even the diff with the demo 1 changes — and answered from the code without calling the server. So:
   - `claude` is started from a separate client folder (`client-a`, `client-b`, `client-m1`) that contains only `.mcp.json`;
   - the built-in tools are disabled with the `--tools` flag, leaving only reading of MCP resources. The agent sees only the server.
2. **Your personal MCP servers will get in the way.** Without the `--strict-mcp-config` flag, the client also loads the servers from your user config. The flag leaves only `support-tickets`. The launch command is in section 1.2.
3. **The full server does not work for demo 1.** Its `INSTRUCTIONS` tell the agent to read the resource `support://status-graph`. The agent reads the graph, understands that `answered → new` is not allowed, and does not call `update_ticket` at all — the good error never appears. So in demo 1 both versions have no hints (in the description, the instructions or the resources) and differ only in the error text (section 1.4).
4. **`.mcp.json` is created by the script** in the client folders, with absolute paths.
5. **`make db-reset db-seed` writes to `data/support.sqlite`**, not to the scenario DB. For the demos use `make ide-db` (or `demo-setup.sh reset`): it recreates `data/ide-scenario.sqlite`, 20 tickets and 10 `agent_trace` rows.
6. **Use Inspector 2.13.0 or newer.** RCE advisories for 2.0.0–2.11.0 were published on 21.10.2026, fixed in 2.12.0. All commands here pin 2.13.0.

### Cheat sheet for the seed data

| id | Status | Subject | What for |
|---|---|---|---|
| 1–10 | `new` | 3 — empty body, 4 — a log of ~15k characters, 10 — prompt injection | edge cases, not used in the demos |
| 5, 6 | `new` | "Cannot export report to CSV" (6 is a duplicate of 5) | demo 3 |
| 11–15 | `answered` | 12 — "Не приходит письмо для сброса пароля" (the password reset email does not arrive) | demo 1 (immediately `allowed=[escalated]`) |
| 16–20 | `escalated` (terminal) | 16 — "Требую возврат средств за год" (a demand for a refund for the year) | demo 2 and step 3 of demo 3 |

Status graph: `new → answered`, `new → escalated`, `answered → escalated`. `escalated` is the final status. A transition "to the same status" is also forbidden.

---

## 1. Preparation (~15 min)

### 1.1 One command

From the `M1-Ilya` folder:

```bash
bash mcp/demo/demo-setup.sh setup
```

What the script does (safe to run again):

| Folder in `~/sts-demo/` | What it is | What for |
|---|---|---|
| `sts-m1` | a copy of `smart-support/`, unchanged | demos 2 and 3 |
| `sts-a` | the copy + both demo 1 patches | demo 1, version A |
| `sts-b` | the copy + only `demo1-no-hints.patch` | demo 1, version B |
| `client-m1`, `client-a`, `client-b` | only `.mcp.json` with absolute paths to the server and the DB of its own copy | `claude` is started from here |

In each copy: `make setup` (uv, Python 3.13, `mcp==2.3.0`) and `make ide-db`. At the end: `make test-server` (48 OK) and `make selfcheck` (19/19) in `sts-m1`.

The `smart-support/` folder itself is not changed. Paths are changed with the `STS_SRC` and `DEMO_DIR` variables (described at the top of the script). When done: `demo-setup.sh remove`.

### 1.2 Starting Claude Code

For each window, from its own client folder:

```bash
cd ~/sts-demo/client-a     # or client-b, client-m1
claude --strict-mcp-config --mcp-config .mcp.json \
  --tools "ListMcpResourcesTool,ReadMcpResourceTool" --allowedTools "mcp__support-tickets"
```

- `--strict-mcp-config` — only the demo server, none of your personal servers (point 0.2).
- `--tools …` — no file reading and no shell; the agent can only call the server's tools and read its resources (point 0.1).
- `--allowedTools "mcp__support-tickets"` — the server's tools do not ask for permission.

Check: `/mcp` → the list shows a single `support-tickets`, connected. The tools are visible as `mcp__support-tickets__update_ticket` and so on.

### 1.3 Inspector

**The simple way, without Docker** (shows only the demo server):

```bash
cd ~/sts-demo/sts-m1
CLIENT_PORT=6390 MCP_SANDBOX_PORT=6391 npx -y @modelcontextprotocol/inspector@2.13.0 \
  "$PWD/scripts/server-stdio.sh" -e SUPPORT_DB_PATH=./data/ide-scenario.sqlite --protocol-era auto
```

- Put `-e` **after** the server path, otherwise you get `No servers found in config file`.
- The DB here is shared with demo 3 (`data/ide-scenario.sqlite`); the server's stderr has the line `starting transport=stdio db=ide-scenario.sqlite`.
- `make inspector` in the project uses `--catalog` and does not accept the server command in web mode (`--catalog cannot be combined with an ad-hoc server URL/command`). Use the command above.

**The stand in Docker** (all servers from the overview plus ours). It takes `support-tickets` from `~/sts-demo/sts-m1`, so do 1.1 first.

```bash
cd mcp/inspector
cp .env.example .env                 # once; the GitHub and Figma tokens are optional (section 5.3)
docker compose up --build -d         # first build ~3 min and 2.6 GB, afterwards seconds
docker compose logs inspector | grep -A1 'up and running'
bash check.sh                        # ends with "Errors: 0"
```

- Open the link from the log: `http://localhost:6380?MCP_INSPECTOR_API_TOKEN=…`. The token is new on every start; a permanent one is `INSPECTOR_TOKEN` in `.env`.
- The **Servers** list immediately has 18 servers (16 without tokens in `.env`). For demo 2, turn on the toggle in the **support-tickets** card: "Connected", "MCP 2026-07-28". The other cards fade out meanwhile: Inspector holds **one** connection. To switch to another server, turn the current one off first.
- `support-tickets` on the stand is the same server from `~/sts-demo/sts-m1` (mounted read-only), but with **its own** DB `/home/node/data/sts.sqlite` inside the container. It is recreated from the seed on every start: `docker compose restart inspector` = a fresh DB. Calls from the stand do not end up in the `agent_trace` of demo 3.
- `protocolEra: auto` is already set in the catalog: the connection uses revision **2026-07-28**, and the first entry in the log on the right is `server/discover`, not `initialize`.

### 1.4 Demo 1: what is in versions A and B

Both versions have no hints: everything the agent could use to learn the graph in advance is removed from the server. They differ only in the response to a rejection.

| | `demo1-no-hints.patch` | `demo1-bad-error.patch` |
|---|---|---|
| What it changes | `tools.py`: the "Allowed status transitions" block, the requirement "new_status, allowed from it", the reference to the resource and the rejection-handling block are removed from the `update_ticket` description. `server.py`: a short `INSTRUCTIONS` without the graph, `register_resources` commented out | `results.py`, `fail()`: any domain error → `{"error": "Invalid transition"}` |
| A (`sts-a`) | yes | yes |
| B (`sts-b`) | yes | — |

Why it is done this way. Without the first patch the agent takes the graph from the description or the resource and never reaches the error (point 0.3). Without the second patch there is no difference between A and B: the same server, a different error.

What remains in the description as a weak hint, which is acceptable:
- the `new_status` field: "'answered' or 'escalated' (must be allowed from the current status)";
- the list of statuses in the `list_tickets` description.

The graph cannot be reconstructed from this.

Verified:
- A: any domain error, including `MISSING_REQUIRED_FIELD`, returns `isError=true` and `{"error": "Invalid transition"}`; the resources are empty;
- `agent_trace` in A records the **real** codes;
- the tests fail as expected: A — 5 `test_mcp` tests, B — 2 tests; `selfcheck` is 3/5 in both (the status-graph resource is disabled). The copies exist for the demo only.

---

## 2. Demo 1 · Bad vs good error, A/B

**Idea:** the error text is a prompt. The server is the same; the only difference is what the agent gets in response to a rejection.

**Ticket:** **12** (`answered` on a fresh seed, only `escalated` is allowed). Demo 1 does not touch tickets 5, 6 and 16, and A and B work with different DBs, so demo 3 is not affected.

Open two windows: `client-a` and `client-b`, both started with the command from 1.2. Paste the same prompt into both.

**Prompt:**
```
Ticket 12 was answered by mistake. Use the support-tickets server to move it back to new.
```

**A, in the runs (2 of 2):** `get_ticket(12)` → `update_ticket(12, new_status="new", agent="operator")` → `{"error": "Invalid transition"}` → the agent gives up. It says the ticket cannot be moved back and that there is "no way to reopen it", and sends the user to an administrator. That the ticket can be escalated, it does not know and does not suggest.

**B, in the runs (2 of 2):** the same call → a rejection:
```json
{
  "ok": false,
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "cannot move ticket 12 from 'answered' to 'new'",
    "hint": "Ticket 12 is 'answered'. Retry update_ticket with new_status in ['escalated'], or stop if none fits.",
    "current_status": "answered",
    "allowed_transitions": ["escalated"]
  }
}
```
Next the agent explains that from `answered` you can only go to `escalated`, and proposes escalation. It may also escalate on its own, with an `escalation_reason`; that is a good outcome too.

**`agent_trace` in A:**
```bash
sqlite3 -header -column ~/sts-demo/sts-a/data/ide-scenario.sqlite \
  "SELECT id, status_from, status_to, outcome, error_code FROM agent_trace WHERE ticket_id=12 AND id>10;"
```
One `rejected` row with the **real** code `INVALID_STATUS_TRANSITION`. The server knew the reason; in version A it just did not say it.

### What can go wrong

| Situation | What it means |
|---|---|
| A repeats the call or tries statuses at random | It is guessing. This did not happen in the Opus 5.5 runs, but other models do it |
| A guessed `escalated` and gave a reason | The model knows typical ticket systems. For your own domain with 7 statuses, guessing will not work |
| B did not call `update_ticket` and said right away that it is not allowed | It saw the graph somewhere: check that the window was started from `client-b`, not from `client-m1` |
| The agent reads files or runs commands | The window was started without the flags from 1.2. Restart with the flags |
| The agent asks for permission to call a tool | `--allowedTools` was not passed. Press "allow for session" |
| `/mcp` shows failed | Check that `demo-setup.sh setup` finished without errors and that `.mcp.json` points to an existing copy |

---

## 3. Demo 2 · Inspector

**Idea:** under the agent there is an ordinary protocol. Here is what the server really returns.

Open Inspector (1.3) and connect `support-tickets`. The 2.13.0 interface: tabs **Servers · Tools · Prompts · Resources** at the top, a **Protocol** log on the right with all the messages.

| Step | Action | What is visible |
|---|---|---|
| 1 | The **Tools** tab | "Tools (3)": `get_ticket`, `list_tickets`, `update_ticket` — three tools for the whole ticket lifecycle, not one for every field |
| 2 | Click `update_ticket` | The whole description: "Allowed status transitions…", "When NOT to call", an example with `agent='operator'`; below it the arguments form. The description is a prompt: this is where the agent takes the transitions and even the value of `agent` |
| 3 | The **Resources** tab → **Ticket status graph** | The graph JSON opens at once (below), `resources/read` in the log on the right. A resource is reference material that the client supplies without a model turn |
| 4 | **Tools** → `update_ticket`: Ticket Id `16`, New Status `answered`, Agent `inspector`, Answer `test` → **Execute Tool** | A red "Tool Error" block and "Structured Output" with the rejection JSON (below), `tools/call` in the log. Not an exception but a tool result with `isError` (SEP-1303): the code, the current status, what is allowed, what to do |

In the log on the right, the first message is `server/discover`, not `initialize` — that is the 2026-07-28 protocol revision.

The content of `support://status-graph`:
```json
{
  "statuses": ["new", "answered", "escalated"],
  "initial_status": "new",
  "terminal_statuses": ["escalated"],
  "allowed_transitions": {"new": ["answered", "escalated"], "answered": ["escalated"], "escalated": []},
  "field_rules": {"answered": "requires non-empty `answer`", "escalated": "requires non-empty `escalation_reason`"}
}
```

The response to `update_ticket(16, answered)`:
```json
{
  "ok": false,
  "error": {
    "code": "INVALID_STATUS_TRANSITION",
    "message": "cannot move ticket 16 from 'escalated' to 'answered'",
    "hint": "Ticket 16 is in terminal status 'escalated' and can no longer change. Do not retry. Report that the ticket is already handled.",
    "current_status": "escalated",
    "allowed_transitions": []
  }
}
```

Why ticket 16: it is terminal on a fresh seed, the response is stable, and demo 2 does not touch tickets 5, 6 and 12. The rejection is written to `agent_trace` with `agent=inspector` — in the DB of the server that Inspector is connected to. On the Docker stand this is the container's own DB; the `npx` path writes to the shared `ide-scenario.sqlite`.

**The second line of defense, right in the DB.** Even if you bypass the server, the DB trigger will not let the transition through:
```bash
sqlite3 ~/sts-demo/sts-m1/data/ide-scenario.sqlite "UPDATE tickets SET status='answered', answer='x' WHERE id=16;"
# Error: stepping, invalid status transition (19)

# on the Docker stand, from mcp/inspector:
docker compose exec inspector sqlite3 /home/node/data/sts.sqlite "UPDATE tickets SET status='answered', answer='x' WHERE id=16;"
```
The guarantee comes from code, not from a prompt.

### What can go wrong

| Situation | What to do |
|---|---|
| The server is "Disconnected" | The Servers tab → the toggle in the `support-tickets` card |
| The `support-tickets` toggle cannot be pressed, the card is faded | Another server is connected (for example `faq`). Turn it off, then turn `support-tickets` on |
| There is no `support-tickets` card on the stand | The stand started without `~/sts-demo/sts-m1`: `docker compose logs inspector` has the line "support-tickets: skipped". Run `demo-setup.sh setup`, then `docker compose restart inspector` |
| The page does not open or asks for a token | Open the fresh link from `docker compose logs inspector` (after a restart the token is new) |
| The port is taken | Another `INSPECTOR_PORT` in `.env`, `docker compose up -d`. For `npx`, another `CLIENT_PORT` |
| Resources are empty or reading fails | The server started without `SUPPORT_DB_PATH` and looks at `data/support.sqlite`. Check stderr (`db=…`) and the order of `-e`. Or Inspector was started from `sts-a`/`sts-b`, where resources are disabled |
| The card says "MCP 2025-11-25" | Started without `--protocol-era auto`. Not a problem, the demo works |
| "Error executing tool …" instead of JSON | A required field (`agent`) is not filled in. This is the SDK's own response (pydantic): this is what an error looks like when nobody designed it |

**Inspector CLI mode**, a text alternative to the UI (verified on 2.13.0):
```bash
cd ~/sts-demo/sts-m1
MCP_CATALOG_PATH=$(mktemp -d)/catalog.json npx -y @modelcontextprotocol/inspector@2.13.0 --cli "$PWD/scripts/server-stdio.sh" \
  -e SUPPORT_DB_PATH=./data/ide-scenario.sqlite --method tools/call --tool-name update_ticket \
  --tool-arg ticket_id=16 --tool-arg new_status=answered --tool-arg agent=inspector --tool-arg answer=x
```
Exit code 5 is normal: the tool returned `isError`. On the stand: `docker compose exec inspector mcp-inspector --cli --catalog /home/node/.mcp-inspector/mcp.json --server support-tickets --method tools/call …` with the same `--tool-arg`.

---

## 4. Demo 3 · The agent in Claude Code

**Idea:** an agent with no hints moves a ticket through the statuses and cannot break the order. We verify against the DB, not against the agent's retelling. This is "Check 2 from the IDE" from the [homework](../../../M1/homework.md): a successful pass and a rejection on an invalid transition.

**Window:** a new `claude` session in `~/sts-demo/client-m1` (the command from 1.2). The expected result is recorded before the run: [`smart-support/m1/expected/ide-scenario.json`](../../smart-support/m1/expected/ide-scenario.json).

### 4.1 Scenario

| Step | Prompt | Calls and responses in the runs (2 of 2) |
|---|---|---|
| 0. Check | `/mcp` | `support-tickets` connected, 3 tools, stdio |
| 1. Success | **P1** | `list_tickets(status="new")` → 10 tickets, ids 1–10 → `get_ticket(5)` → (`status-graph`) → `update_ticket(5, new_status="answered", agent="operator", answer=…, category="technical", …)` → `{"ok": true, …}`. Sometimes the agent also reads ticket 6 and notices it is a duplicate |
| 2. Rejection | **P2** | `get_ticket(5)` → `update_ticket(5, new_status="new")` → `INVALID_STATUS_TRANSITION`, `allowed_transitions: ["escalated"]` → `update_ticket(5, new_status="escalated", escalation_reason=…)` → `ok` |
| 3. Terminal | **P3** | `get_ticket(16)` → `escalated` → the agent explains that the ticket is final and does not call `update_ticket` |
| 4. Cross-check against the DB | `sqlite3` (4.3) | The `agent_trace` rows with id > 10 match the expected ones |
| 5. Bonus | **P4** | `update_ticket(6, answered)` without `answer` → `MISSING_REQUIRED_FIELD`, `details.field = "answer"` → retry with `answer` → `ok` |

What to notice along the way:
- **Step 1.** Nobody said which tools to call. The agent reads the ticket before writing, because the description requires `get_ticket` first. It takes `agent="operator"` from the example in the description: examples are part of the contract.
- **Step 2.** The server refused and said what is allowed. The agent did not repeat the same arguments but chose an allowed transition. The guarantee is not in the prompt: the domain code and the trigger in the DB will not let it do otherwise.
- **Step 3.** The agent read that `escalated` is final and did not even try. If it does call: `allowed_transitions` is empty, the hint says not to retry, the agent stops.
- Inspector is a separate client, it does not show the IDE traffic. For the homework, the evidence for check 2 is the IDE dialog log and the DB.

### 4.2 Prompts (paste as is)

**P1:**
```
Use the support-tickets server. Find the tickets that are still waiting for a reply, then answer the customer in ticket 5.
```
Why not "process all new tickets": there are 10 of them, including ticket 4 with a log of ~15k characters and ticket 10 with a prompt injection, and ticket 5 is needed in the `answered` status for step 2.

**P2:**
```
Ticket 5 was answered by mistake. Call update_ticket to move it back to new. If the server refuses, do what it allows and tell me why.
```
Why `update_ticket` is named in the prompt. The agent has already read the graph in step 1, and without the explicit name it simply refuses without calling the tool (that is what happened with the wording "Move it back to new"). Then there is no rejection in the log, and the homework requires exactly that. **Advice for the homework:** if the description is good, a smart agent will not make a forbidden call on its own. To test the rejection, ask explicitly in the test scenario to call the tool.

**P3:**
```
The customer in ticket 16 wrote again. Answer them: "We are processing your refund request."
```

**P4 (bonus):**
```
Call update_ticket to mark ticket 6 as answered, without any answer text. Then fix the call the way the server tells you, with this answer: "This is the same issue as ticket 5. Please see our reply there."
```
The answer text is given in the prompt up front. With the wording "do not write any answer text yet. Then fix whatever the server says" the agent got a rejection and stopped: fixing the error would mean breaking the user's request.

### 4.3 Cross-check against the DB

```bash
cd ~/sts-demo/sts-m1
sqlite3 -header -column data/ide-scenario.sqlite \
  "SELECT id, ticket_id, agent, status_from, status_to, outcome, error_code FROM agent_trace WHERE id > 10 AND ticket_id IN (5,6,16) ORDER BY id;"
sqlite3 -header -column data/ide-scenario.sqlite "SELECT id, status FROM tickets WHERE id IN (5,6,16);"
```

Rows 1–10 are the seed. The row from demo 2 (`agent=inspector`, ticket 16) appears only if demo 2 went through the `npx` path on the shared DB; with the Docker stand it is absent, and the row numbers below shift by one.

On both P1–P4 runs, after demo 2:
```
id  ticket_id  agent      status_from  status_to  outcome   error_code
11  16         inspector  escalated               rejected  INVALID_STATUS_TRANSITION   (demo 2, only with the npx path)
12  5          operator   new          answered   ok
13  5          operator   answered                rejected  INVALID_STATUS_TRANSITION
14  5          operator   answered     escalated  ok
15  6          operator   new                     rejected  MISSING_REQUIRED_FIELD      (P4)
16  6          operator   new          answered   ok                                  (P4)
```
Result: ticket 5 is `escalated`, ticket 6 is `answered` (`new` without P4), ticket 16 is `escalated`.

Not recorded in `agent_trace`:
- an invalid `agent`;
- `TICKET_NOT_FOUND`;
- SDK argument validation errors (pydantic).

### 4.4 What can go wrong

| Situation | What to do |
|---|---|
| In step 1 the agent set about answering all 10 tickets | Esc, then repeat P1 with "only ticket 5" |
| In step 1 the agent did not call `list_tickets` | Not a problem, what matters is `get_ticket` → `update_ticket` |
| In step 2 the agent still did not call `update_ticket` | Add: "Call it anyway, I want to see the server's answer" |
| In step 2 the agent asked "escalate?" | Answer "yes". A human in the loop is a good outcome |
| The agent repeated the same invalid call | This is where you fix the tool description, not the code, and record the change in `process-log.md` (the working order is in the [homework](../../../M1/homework.md)) |
| The agent uses another DB (the tickets are wrong) | The window was not started from `client-m1` |
| Ticket 5 is already `escalated` from a previous run | `demo-setup.sh reset`, or `/exit`, `make ide-db` in `sts-m1`, `claude` again. Or take the pair "ticket 7 + ticket 17" through the same scenario (7 is `new`, 17 is terminal) |

---

## 5. The Inspector stand: 13 servers from the overview and our own servers

The stand lets you open any server from the [overview](../top-mcp-servers.md) in a minute and see how it works live. It also shows how to connect **your own** server to Inspector.

**How it was verified (30.10.2026).**
- The image was built from scratch without cache: 2.6 minutes, 2.64 GB.
- `check.sh` — 14 servers answered a real call, 4 OAuth servers answered "sign-in needed".
- In the web UI the following were verified: the list of 18 servers; `faq` (connecting, a `search_faq` call, the resource, the prompt); switching `faq` → `support-tickets`; the 4 steps of demo 2; the start of the Notion sign-in (a redirect to `app.notion.com/login`).
- The sign-ins to the OAuth servers themselves, as well as GitHub and Figma with tokens, were not verified.

### 5.1 How the stand is built

- **One image.** Inspector 2.13.0 and all the local servers are installed at build time with exact versions.
  - Node servers are installed via `npm -g`.
  - Python servers as `uv tool`.
  - GitHub MCP is a binary from the official image.
  - For Playwright and Chrome DevTools the image has Chromium.
- **The catalog is built on every start.** The `render-catalog.mjs` script turns `catalog.template.json` into the container's `~/.mcp-inspector/mcp.json`:
  - substitutes the tokens from `.env`;
  - drops the servers that have no token or no mounted folder, and writes the reason to the log.
  - This is needed because Inspector does not substitute `${VAR}` itself, and a stdio server does not see the container's environment.
- **The catalog can be edited from the UI.** This is `--catalog`, not `--config`: Add Servers / Edit / Remove work in the UI. Edits live until the container restarts, then the catalog is built again from the template.
- **Postgres** is a separate container with a sample DB: 20,000 tickets, with deliberately no index on `customer`.
- **Mounted from the host:**
  - `catalog.template.json` — edit it and run `docker compose restart inspector`, no rebuild needed;
  - `own-server/`;
  - `~/sts-demo/sts-m1` (read-only; another path via `STS_DIR` in `.env`).
- **Secrets in memory only.** OAuth tokens are not written to disk; sign in again after a restart.
- **Port only `127.0.0.1:6380`.** The Inspector backend starts processes on request, do not expose it to the network.

### 5.2 What is in the catalog and what to try

The number is the card in the overview. "Verified" means a call from `check.sh` or from this table, made on 30.10.2026.

| Server | No. | How it is connected | Needs | What to try in 30 seconds |
|---|---|---|---|---|
| `everything` | 1 | stdio | — | The reference for all protocol features: Tools (17), Prompts, Resources in one server |
| `filesystem` | 1 | stdio, only `/home/node/workspace` | — | `list_directory` on the workspace works, `read_text_file /etc/passwd` → "Access denied - path outside allowed directories" |
| `fetch` | 1 | stdio | — | `fetch https://example.com` → the page as Markdown, not HTML |
| `git` | 1 | stdio, `--repository` workspace | — | `git_log` → two commits of the sample project |
| `github` | 2 | stdio, `--read-only` | `GITHUB_TOKEN` (not verified) | Only read tools in Tools: read-only mode cuts the set, rather than asking the model "not to write" |
| `context7` | 3 | remote HTTP | — (without a key there is a limit) | Only 2 tools: `resolve-library-id` → `query-docs` |
| `serena` | 4 | stdio, `--agent-interface tools` | — | 22 tools; `find_symbol` with `name_path_pattern=check_transition`, `include_body=true` → the function body via LSP (first call ~10 s) |
| `serena-repl` | 4 | stdio, `--agent-interface repl` | — | The same capabilities but 2 tools: `initial_instructions` and `serena_repl`. This is the default mode in Serena 2.x — the same shift toward Code Mode as at Cloudflare |
| `playwright` | 5 | stdio, headless Chromium | — | 25 tools; `browser_navigate https://example.com` → a page snapshot via the accessibility tree, not a screenshot |
| `chrome-devtools` | 6 | stdio, headless Chromium | — | 32 tools; `new_page https://example.com` → a list of pages |
| `figma` | 7 | stdio | `FIGMA_API_KEY` (not verified) | `get_figma_data` by file key: the response is already compressed to what the model needs |
| `notion` | 8 | remote HTTP, OAuth | a Notion account | Connect → the Notion sign-in page → back to Inspector. Only the redirect to sign-in is verified |
| `sentry` | 9 | remote HTTP, OAuth | a Sentry account | The same; sign-in not verified |
| `supabase` | 10 | remote HTTP, OAuth, `?read_only=true` | a Supabase account | The same; read-only is set in the URL; sign-in not verified |
| `postgres` | 11 | stdio, `--access-mode=restricted`, the DB from compose | — | `explain_query` for `SELECT * FROM tickets WHERE customer='customer42@example.com'` → Seq Scan; `execute_sql` with `DELETE` → "Error validating query" |
| `cloudflare` | 12 | remote HTTP, OAuth | a Cloudflare account | The entire Cloudflare API through Code Mode; sign-in not verified |
| `cloudflare-docs` | 12 | remote HTTP | — | `search_cloudflare_documentation` works without sign-in |
| `azure` | 13 | stdio | `az login` for calls | 73 tools: `namespace` mode by default, one tool per Azure service. The list is visible without an account, calls are not |
| `faq` | own | stdio | — | Section 5.4 |
| `support-tickets` | own | stdio, from `~/sts-demo/sts-m1` | 1.1 | Demo 2, section 3 |

Two findings worth noticing:
- **Postgres MCP Pro rejects `DELETE` with `isError: false`.** The error text is there, but the client does not learn that it is an error. In `support-tickets` the rejection comes with `isError: true` and with the allowed transitions — that is how it should be in the homework.
- **Serena 2.x returns a single `serena_repl` by default instead of separate tools.** The overview describes the classic set; the stand has both variants, convenient to compare side by side.

### 5.3 Tokens and sign-in

- **GitHub and Figma.** Put the tokens in `.env`, then `docker compose up -d`: the container is recreated with the new environment. In the log, instead of "skipped (no GITHUB_TOKEN in .env)" you will see `+ github`. Never commit `.env`.
  - GitHub: a fine-grained read-only PAT.
  - Figma: Settings → Security → Personal access tokens.
- **Notion, Sentry, Supabase, Cloudflare.** Turn on the toggle in the card → the service's sign-in page opens → after signing in the browser returns to `http://localhost:6380/oauth/callback`, and the server becomes Connected. The token lives until the container restarts.
- The stand works without tokens and sign-ins: 16 cards, 4 of which are OAuth servers that show a sign-in.

### 5.4 Your own small server: `faq`

[`../inspector/own-server/faq_server.py`](../inspector/own-server/faq_server.py) — about 50 lines. One tool, one resource, one prompt, only `mcp==2.3.0`. The point: **an MCP server is functions with good descriptions, the SDK does everything else.**

| Step | Action | What is visible |
|---|---|---|
| 1 | Servers → turn off the current server, turn on `faq` | "Connected", "MCP 2026-07-28", `server/discover` in the log |
| 2 | Tools → `search_faq` | The description from `description=`, the **READ-ONLY** badge from `ToolAnnotations(readOnlyHint=True)` |
| 3 | Query `refund` → Execute Tool | `{"topic": "refund", "answer": "Refunds go back to the original card within 5 business days after approval."}` |
| 4 | Resources → **FAQ topics** | `["export", "password", "refund"]` |
| 5 | Prompts → `answer_ticket`, field `ticket_text`: `I did not get my refund` → **Get Prompt** | A ready message for the model: "Call search_faq for the main topic of this ticket…" |
| 6 | In an editor on the host add the line `"invoice": "Invoices are in Billing > History; the PDF has the VAT number.",` to `FAQ` → in Inspector turn `faq` off and on → Tools → `search_faq` with `invoice` | The new answer right away, with no rebuild or restart: the folder is mounted, and Inspector starts the server anew on every connection |

After step 6, remove the added line again.

### 5.5 Your own real server: `support-tickets`

This is the server from the homework example and from all three demos. Differences from running it on its own:
- the **code** comes from `~/sts-demo/sts-m1` (read-only), Python and `mcp==2.3.0` come from the image (`/opt/mcp/venv`), not from the copy's `.venv`: that venv was built for your host OS;
- the **DB** is its own, inside the container, from `db/schema.sqlite.sql` and `db/seed.sql` of the copy; recreated on every start;
- **edits** in `~/sts-demo/sts-m1/mcp_server/` are visible after turning the card off and on, as in 5.4.

How to add your own server to the stand:
1. Put it in `own-server/<name>/`.
2. Add an entry to `catalog.template.json` modeled on `faq`: `command`, `args`, and if needed `cwd`, `env`, `"protocolEra": "auto"`.
3. Run `docker compose restart inspector`.

The dependencies are only `mcp==2.3.0` from the image; if you need others, add them to the `Dockerfile` (the line with `/opt/mcp/venv`) and rebuild.

It can also be done without editing files: **Add Servers** in the UI. But the entry lives only until a restart, and the command must exist inside the container.

### 5.6 What can go wrong

| Situation | What to do |
|---|---|
| `check.sh`: `FAIL serena` or a long first call | Serena starts a language server, the first call takes up to ~10 s. Repeat; if FAIL again — `docker compose logs inspector` |
| `FAIL playwright` / `chrome-devtools` | No network to example.com, or Chromium crashed. `docker compose exec inspector chromium --version` |
| `FAIL postgres` | The `postgres` container did not come up: `docker compose ps`, `docker compose up -d` |
| An OAuth server asks for sign-in again after signing in | The container was restarted, the tokens were in memory. Sign in once more |
| There are no `github` / `figma` cards | No token in `.env`, which is normal. The log has a "skipped" line |
| After `STS_DIR` with a nonexistent path an empty folder appeared | Docker creates the mount folder itself. Delete it; `support-tickets` is simply skipped in that case |
| A different port is needed | `INSPECTOR_PORT` in `.env`, `docker compose up -d`. The port inside and outside match deliberately: Inspector hands the browser addresses with its own port |

To stop the stand: `docker compose down`. The image stays, the next `up` takes seconds. To remove the image too: `docker compose down --rmi local`.
