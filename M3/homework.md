# Module 3 homework: the course project's agent moves from n8n to code

You built the prototype in the first module as a deliberately linear one: no branching, no loop and no
memory, strictly a chain of nodes. What that prototype was missing, you wrote down yourselves in that module's
report. In this assignment one agent from that chain is rebuilt in code on LangGraph: its
own stop condition, its own state, a loop that can be stopped and resumed.

You work with exactly one agent. Multi-agent graphs, routing between roles and a shared state
schema are the next module's topic; do not pull them in here.

The base program is the same for everyone. The advanced level is blocks of your choice on top of it: a real
tool instead of a stub, a measurement of how memory behaves, strict serialization of state snapshots,
a third human decision at the pause. You can take one block, or all four.

## What to submit: the short version first

The work consists of two base parts; advanced adds blocks of your choice to them. Everything is submitted
together, in one repository.

| Part | What you do | What artifacts remain |
|---|---|---|
| 1. The agent loop | The agent contract before the code, a state schema, two nodes with a conditional edge and a cycle, an iteration limit, a short-term memory window | the agent code, `requirements.txt`, the contract and schema sections in `report.md`, the output of 2–3 convergence runs |
| 2. Checkpointer and pause | State snapshots in a file, three script modes, two process launches on one `thread_id`, a pause before an irreversible action, the approve and reject branches | a `README` with the start and resume commands, `.gitignore`, logs of the pause runs and of the second-thread isolation run |
| Blocks A–D (advanced, of your choice) | A real tool, a memory measurement, strict serialization, a third decision and the irreversibility boundary | additions to the code and sections in `report.md` |

Plus `process-log.md`: how you worked with the coding agent while building. Start it before the first
prompt, not at the end: verbatim wordings, especially the unsuccessful ones, cannot be
reconstructed after the fact. The full list is below, in the section "What to submit and acceptance criteria";
it is the source of truth for the contents.

## Deadlines and submission format

**Deadlines:** the module theory: August 17. The submission deadline and the practice date are announced separately, in the course
chat and in the LMS, before the fourth module starts. If you see that you will not make it: write in advance,
not on the day of submission.

**Submission format:** the work continues in the private repository of your course project; read access
for the teacher's account [`Serg1Kk`](https://github.com/Serg1Kk) has already been granted. Paste the link
to the whole repository, not to a single file, into the field at the bottom of this assignment in the LMS
and send it with the button: feedback is written there and attached to your submission. This module's report
does not overwrite the reports of the first two: put it in a separate file, for example `report-m3.md`
or `m3/report.md` (below it is simply called `report.md`). **State the level you are submitting
on the first line of the report** and, if you are submitting advanced, which blocks you did. If you work
in a separate branch, name it there too: by default the repository opens on the main branch,
and work in another branch is invisible to the reviewer.

**What you need before starting:** the materials of sessions 3.1 and 3.2 and the working n8n prototype from the first
module. The assignment carries one agent from it over into code.

**Time:** the base program takes 9–12 hours. Each advanced block adds an hour and a half to two hours, except
block B: it adds two to three hours and 25 real exchanges with the model. All four blocks together
add six to nine hours to the base, and it makes sense to take them on only when the base program
is already built and working. The estimate is honest: about three hours go on what
nothing speeds up. That is reading two pages of documentation, extracting the agent contract
from n8n, `report.md` and `process-log.md`, the run logs, and the "start, kill the process,
resume" iterations through a real model.

## Order of work

The dependencies here are strict, and several steps cannot be redone after the fact, so the order
is this:

| Step | What | Why now |
|---|---|---|
| 0 | Create `process-log.md` and add wordings to it as you go | Verbatim prompts, including the unsuccessful ones, cannot be reconstructed at the end of the evening, and without them the log counts as missing |
| 1 | Check that the n8n prototype runs and the chosen agent is visible in it separately | The assignment stands on it. If the prototype did not come together, sort it out before starting, not along the way |
| 2 | Check the provider key with a direct API call and estimate the budget | A direct call may fail where an n8n node works. Loop runs cost real tokens, and block B adds 25 consecutive exchanges to them |
| 3 | Write the agent contract in `report.md` | From here the code is checked against this record, not the other way around |
| 4 | Part 1: the state schema, two nodes, the conditional edge, the iteration limit | The skeleton everything else stands on |
| 5 | Run 2–3 scenarios, save the output | Convergence is checked before the checkpointer goes on top: otherwise it is unclear what broke |
| 6 | The short-term memory window | Put on the already working loop |
| 7 | Part 2: state snapshots in a file and the three script modes | Without the modes there is nothing to check that the state survives the process exiting |
| 8 | The pause before an irreversible action, the approve and reject runs, second-thread isolation, a repeated resume | Save the log right away: restoring it after the fact costs more than recording it once |
| 9 | Finish `report.md`, assemble the `README` with two commands and `.gitignore` | While the runs are fresh |
| 10 | Advanced blocks, if you do them | Put on top of the working base |

## How normal and advanced differ

The base program is the same for everyone: parts 1 and 2 in full. Advanced is not a different assignment but blocks
on top of the base. Do at least one of the four in full, more if you like; note which ones you did
on the first line of `report.md`.

| | normal | advanced |
|---|---|---|
| Parts 1 and 2 | in full | in full, unchanged |
| Block A: a real tool | a stub with an honest input and output contract | a real search over the knowledge base from the second module instead of the stub |
| Block B: memory measurement | not required | a dialogue of 25+ exchanges with two numbers per model call |
| Block C: strict serialization | not required | an explicit list of allowed types instead of the default mode |
| Block D: a third decision and the boundary | approve and reject | plus the edit option and a justification of the irreversibility boundary |

**The table rows explained.**

- **Block A, a real tool.** In the base program the agent calls a stub: a function that
  returns a predefined answer in the same format a real tool would return. Block A
  plugs in, instead of it, a search over the Qdrant collection built in the second module. Qdrant is needed
  only by this block: the other three have nothing to do with search and are done without it.
- **Block B, memory measurement.** Two numbers for each model call: how many messages went into the request
  and how many input tokens the provider counted. The point of the measurement is to see that both
  stop growing from exchange to exchange. The block is expensive: it requires a separate, interactive
  script mode on top of the base three, and 25 real exchanges with the model.
- **Block C, strict serialization.** The checkpointer puts the graph state into a file and by default
  agrees to pack almost any object. This is not done in production: unpacking a swapped
  file becomes a hole. The block sets an explicit list of allowed types and, along with it, changes the form
  of opening the database: the `with` block from part 2 will have to be rewritten as a direct constructor. It is not
  required to complete the assignment.
- **Block D, a third decision and the boundary.** Besides "execute" and "cancel", the human can return
  a corrected text of the action: the pause hands a draft out, the human edits it, the graph continues
  with the edit. In addition, the report gets a paragraph on where your agent's boundary of
  irreversibility lies and why the pause stands exactly there.

Two words the assignment uses from the first line on are worth defining right away.

- **Checkpointer:** a component that, after each graph step, saves the state to storage
  so that the work can be continued in a new process launch. The saved state is
  called a snapshot from here on.
- **`thread_id`:** a conversation identifier. The checkpointer uses it to find which exact state
  to continue; two different identifiers on one database file do not see each other.

## Preparation

### Environment: check before you start

The assignment stands on the prototype from the first module, and the first step is blocked if there is no prototype.
Before you begin, make sure that:

- the n8n prototype runs and passes through the whole chain, and the chosen agent is visible in it
  separately: with its own prompt, input and output;
- you have a model provider key, the same one you set up at the first level, and it works
  with a direct API call, not only through an n8n node;
- the key has a balance and headroom on the request rate. The base program is several dozen
  real model calls, and block B adds 25 consecutive exchanges to them. If the key is a free one,
  check the limits before starting, not in the middle of part 2;
- Python 3.10 or newer is installed on the machine;
- for block A: the Qdrant from the second module comes up and the collection is in place.

One-line install: `pip install "langgraph>=1.2" langgraph-checkpoint-sqlite
"langchain[anthropic]"` (or `langchain[openai]`, to match your key). The framework and model access
are installed separately, and the first error of this homework, for almost everyone, is here: `pip install langgraph`
does not pull in the provider. The `init_chat_model` model factory lives in the `langchain` package, so
the import will not pass without it; without the provider package the import will pass and the call
will fail instead, but with an explicit pointer to what to install. Pin the versions in `requirements.txt` and attach it
to the submission.

### Module theory

- **Session 3.1**, the agent cycle, tool calls and stop conditions:
  [3.1](https://kb.hardsoftskills.dev/AI_Product_Development_L2_v1/ru/3.1-agent-anatomy).
  The loop built there on the bare API moves here onto `StateGraph`.
- **Session 3.2**, state, snapshots, `thread_id`, pause and resume:
  [3.2](https://kb.hardsoftskills.dev/AI_Product_Development_L2_v1/ru/3.2-state-and-memory).
  These are direct instructions for the assignment, not general context.
- **LangGraph documentation**, keep two pages open:
  [checkpointers and state snapshots](https://docs.langchain.com/oss/python/langgraph/checkpointers)
  and [pauses and resume](https://docs.langchain.com/oss/python/langgraph/interrupts).
  The `persistence` overview page gives only the frame: the only graph-assembly example on it
  keeps snapshots in memory, which is exactly what the assignment does not accept.

### Module materials

The `M3` folder of your materials repository holds the companions to the assignment. You do not need to read them in order;
they are picked per step.

**For this homework:**

- [Rules and pitfalls for a coding agent on LangGraph](https://github.com/Serg1kk/aidev-l2-course-materials/blob/main/M3/guides/langgraph-agent-guardrails.md):
  the assignment's main guide. Python, `StateGraph`, the checkpointer, the pause. Give it to your coding agent
  as context before asking for code: it removes most of what is listed below
  in the section "Where it usually breaks".
- [Module slides](https://github.com/Serg1kk/aidev-l2-course-materials/blob/main/M3/slides/m3-slides.html):
  download and open with a double click; a click on an item expands the details.
- [Run tracing](https://github.com/Serg1kk/aidev-l2-course-materials/blob/main/M3/guides/observability-langsmith-langfuse-n8n.md):
  how to hook observability up to your runs. Not required for submission, but if you want to see
  what exactly goes into the model on each iteration, it takes half an hour to set up and greatly simplifies
  debugging the loop.

**Session demos, not for this homework:**

- [`M3/examples/`](https://github.com/Serg1kk/aidev-l2-course-materials/tree/main/M3/examples):
  n8n workflow exports and three JavaScript code examples for the LangChain Code node. This is material
  for the intermediate step, where the agent's logic still lives inside n8n. The Python and LangGraph code of your homework
  is not assembled from them: look at them for the mechanics of the loop, not for the syntax.
  They are imported into your own n8n, credentials scrubbed.
- [Rules for the LangChain Code node](https://github.com/Serg1kk/aidev-l2-course-materials/blob/main/M3/guides/langchain-code-node-guardrails.md):
  the same dialect, if you decide to go through the intermediate step and first try out the agent logic
  as code inside n8n. This does not apply to the assignment.

The folders shared across the course live in the root of the materials repository:
[`planning/`](https://github.com/Serg1kk/aidev-l2-course-materials/tree/main/planning),
[`agents/`](https://github.com/Serg1kk/aidev-l2-course-materials/tree/main/agents),
[`skills/`](https://github.com/Serg1kk/aidev-l2-course-materials/tree/main/skills). The templates
for working with a coding agent live there too.

### Where to start if you lack experience

**If you have never built a graph by hand.** Do not start with your own agent. Build a graph
of two nodes where the second one just appends a string, run it once and look at
the state. Once the chain "input, node, state, output" works on a dummy, your agent
becomes a matter of replacing the node bodies.

**If you have never worked with a checkpointer.** Attach it to the same two-node graph,
run it twice with the same identifier and see that in the second run the state is already
not empty. That is thirty minutes, and after it part 2 reads as an instruction, not as theory.

**If the agent in your n8n prototype is not singled out.** The contract can still be extracted:
take the node's system prompt, look at what comes in and what goes on
down the chain, and write that down as the contract. You do not need to rework the prototype for this.

## Part 1: the agent loop on LangGraph

The graph is built by hand on the low-level `StateGraph`, not with the ready-made `create_agent` factory:
the assignment is about what happens between steps, and the factory hides exactly that.

Three words from this part, so you can use them freely from here on. A **node** is a graph step, a piece
of your code that receives the state and returns changes to it. An **edge** is a rule for
where to go after a step; a conditional edge picks the next step by the state. An **iteration** is one
pass of the agent around the cycle: model, tool, model again.

### Which agent to take

Choose one agent of your course project. Not just any will do: the agent needs three properties,
otherwise half the assignment will have nothing to apply to.

1. It calls at least one tool, otherwise you cannot build a loop or check convergence.
2. It can call a tool more than once per task, otherwise there is nothing to hit the iteration limit with.
3. It ends with an irreversible action: sending a reply to a client, publishing a text,
   a comment on a diff, a write into someone else's system. This is the place the pause will stand before.

A classifier that labels a ticket in one call does not meet these conditions: take the agent
that does something outward after it decides. If you have your own project and no such agent
exists, take the closest one and add one outward action to it.

**Write the agent contract in `report.md` before the code:** what the agent accepts, which tools it
calls, what counts as a successful result. From there the code is checked against this record, not
the other way around, and the report has an explicit reference to it. If something in the code departed from the contract, that is
fine: write what exactly and why.

**Tools.** In the base program a tool is a stub with an honest input and output contract:
the function returns a predefined answer of the same shape a real
tool would return. A real search over the collection from the second module is block A of the advanced level. If
the tool you need already lives in your MCP server from the first module, plug it in as is:
tools are portable between orchestrators, only the graph is rewritten.

### State schema and graph

- **State schema:** a `messages` field with the `add_messages` reducer plus 2–3 domain fields
  of your agent. For example, the ticket category, a reply draft, an iteration counter, a counter
  of repeated tool errors: the loop counters from session 3.1 move here as schema fields.
- A **reducer** is a rule by which a field's new value is combined with the old one. By default there is no
  rule: the field's value is determined entirely by the node that wrote last. It is worth giving the error counter
  its own merge reducer: without it, what was accumulated for the previous tool is easy to lose in a refactor or with parallel branches, and the difference is measurable.
  In the measurement discussed in the session, without a merge rule the run reached the fifteenth
  iteration, with the rule it stopped at the sixth. Nine paid iterations of difference, with
  no error and not a line in the log.
- **Full input at the start.** The state schema is easiest to declare through `TypedDict`; it has no
  default values, so the first graph call must contain all the fields, not `messages` alone:
  otherwise the very first node looks for the counter field, does not find it and fails. It is cured by one
  constant holding the full initial state, into which the user's question is mixed.
  Warning: mix it in only on the **first** call on a thread: on the second it will overwrite the counters
  with the values from the constant, and the loop will start counting anew.
- **Two nodes:** `agent` calls the model with tools, `tools` executes the requested calls.
  The conditional edge after `agent` decides whether to continue the loop or finish; the edge from `tools`
  returns to `agent` and closes the cycle.
- **Iteration limit:** a counter in the state and a conditional edge to the exit, with a guideline of 10 iterations.
  In the session's practice it is 15, because there the database has several tables and the questions
  involve joins; for your own agent take less, the loop is shorter, and an excess limit is paid for
  in tokens. The built-in `recursion_limit` does not fill this role: in the framework it is an emergency
  stop at thousands of steps, protection against an infinite loop, not your budget for a task. Set your own
  counter in the state.
- **Check:** run 2–3 scenarios of your agent and make sure the loop converges
  to a final answer within the limit. Save the output of the runs, it goes into the submission.

### Short-term memory

- **Window:** keep the last 10–15 messages whole, trim older ones before the model
  call. Counting by messages is a simplification for the homework: in production the boundary is counted
  in tokens.
- **Trim at turn boundaries, not with a naive list slice.** If you cut the old messages
  just by count, you cut off the model's request to a tool and leave the tool's response without
  its request. The provider does not accept such a dialogue at all and answers 400. Bound the window
  at both ends: `start_on="human"` keeps the window from starting with a tool result without its own
  call, `end_on=("human", "tool")` keeps it from ending with a tool request without
  a result.
- **The second bound matters especially in this assignment.** On the `reject` branch the tool
  is not executed, and without `end_on` a dangling call is left in the history: the next request to the model
  goes out with it and gets a 400. The vendor's requirement here is verbatim: a tool result must
  come immediately after its call, with no other messages between them. If by your agent's logic
  the refusal must stay in the history, add to the `reject` branch a message with a tool result,
  with the same `tool_call_id` and the refusal text. The vendor's wording and a walkthrough:
  [how to handle tool calls](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls).
- **The whole call**, because two arguments of the trimming are required and without them it fails
  immediately:

```python
from langchain_core.messages import trim_messages

window = trim_messages(
    state["messages"],
    strategy="last",
    token_counter=len,        # count messages, not tokens: a simplification for the homework
    max_tokens=12,            # that is, 10–15 messages
    start_on="human",
    end_on=("human", "tool"),
    include_system=True,
)
```

  `token_counter=len` is exactly the count by messages; in production a token counter goes here,
  and `max_tokens` starts to mean tokens. The canonical trimming example with both bounds
  is on the page
  [short-term memory](https://docs.langchain.com/oss/python/langgraph/add-memory).
- **Check that the window does not collapse to a single system message.** On a small window
  with both bounds this is easy to reproduce, and it looks like "the agent forgot everything".
- **In `report.md`:** which strategy you chose, a window or folding the old tail into a summary,
  and what you pay for it.

## Part 2: checkpointer and a pause before an irreversible action

Both checks of this part run in two process launches: the loop's state moves to disk to
survive the first launch ending, and the pause breaks the agent's work exactly along that boundary.

### Persistence between launches

- **A file on disk, not memory:** attach `SqliteSaver` with a path to a database file, not `:memory:`.
  The `from_conn_string` method is a context manager, not an ordinary factory: the whole run lives
  inside a `with` block.

```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph

builder = StateGraph(State)   # nodes and edges from part 1

with SqliteSaver.from_conn_string("checkpoints.sqlite") as saver:
    graph = builder.compile(checkpointer=saver)
    # all graph calls here, inside the block
```

  The package name and the import path do not match here: `langgraph-checkpoint-sqlite` is installed,
  `langgraph.checkpoint.sqlite` is imported.

  A call without `with` gives `TypeError: Invalid checkpointer provided … Received
  _GeneratorContextManager`, and the hint at the end of the message leads astray: it suggests
  taking a different checkpointer, although the checkpointer is chosen correctly and only the block is missing.
  An alternative, if the block gets in the way: the direct constructor
  `SqliteSaver(sqlite3.connect("checkpoints.sqlite", check_same_thread=False))`.
- **Only what turns into text goes into a snapshot:** numbers, strings, messages.
  An open connection, a file descriptor or an API client cannot be put there; the snapshot simply
  will not be written.
- **`thread_id` is a parameter of the script launch**, it is passed in the configuration on every graph
  call.
- **The script needs modes, and they are branches of one `main()`.** Between the start and the resume the process
  exits completely, so the human's decision also arrives as a command-line argument:

```
python agent.py start  <thread_id> "<question>"   # a turn into the thread: prints the pause's question and exits
python agent.py resume <thread_id> approve        # a separate process: execute the action
python agent.py resume <thread_id> reject         # a separate process: do not execute
python agent.py state  <thread_id>                # snapshot: what is next and what is in the fields
```

  **`start` accepts both an identifier and the turn's text.** A repeated `start` call with the same
  `thread_id` and a new question continues the same conversation: the state is pulled from the snapshot,
  and the new message is appended to the history. A separate command for continuing the dialogue is therefore
  not needed, and all three modes stay one-shot: started, printed, exited.

  **The decision arrives as a string, but the graph must receive it already parsed.** Compare
  against the word, not the truthiness of the value: `Command(resume=(sys.argv[3] == "approve"))` or
  `Command(resume={"decision": sys.argv[3]})` with parsing by key in the node. A check like
  `if decision:` on the string `"reject"` is true, and the reject branch will execute the irreversible action.
  There will be no error at all: in the log you will see "it worked", and a scenario that the
  assignment counts as passed will turn out not passed.
- **Survival test:** 3–4 exchanges in a row with `start` calls on one `thread_id`, the process
  exits, a repeated launch with the same identifier. The agent remembers the context and continues.
  You do not need a separate run for this: it is also the first half of the `approve` scenario
  from the next section, and they share a log.
- **Thread isolation:** a second `thread_id` on the same database file starts with an empty state.
  Verify this with a separate run and save its output: it is the proof that
  conversations do not leak into each other.

### One human-in-the-loop pause

- **One pause point:** `interrupt()` before the agent's key irreversible action. The boundary of
  irreversibility lies where the result of the action cannot be undone by your own means: the email
  went out, the comment is published, a record is created in someone else's system. A walkthrough of the criterion:
  [session 3.1](https://kb.hardsoftskills.dev/AI_Product_Development_L2_v1/ru/3.1-agent-anatomy).
- **The pause:** the script prints the value from the pause (with an ordinary call it arrives under the key
  `__interrupt__`) and exits. Today the documentation runs its examples through an event stream
  (`stream_events(..., version="v3")`), and the ordinary call remains workable alongside it: that is stated outright
  on the same page. Take either form, but one, and do not mix them in one script.
- **Resuming is a separate command**, not an ordinary call with the answer inside: a separate
  launch with `Command(resume=...)` and the same `thread_id`. If you pass the answer the ordinary way, the graph
  starts over, reaches the pause again and asks again. It looks like a hung agent, although you
  start it from scratch every time.
- **Decisions:** `approve` and `reject` in the base program; the third option `edit`, with an edit of the action's
  text, is block D.
- **Side effects strictly after the pause.** When the human has answered, the node is executed not
  from the middle but from the beginning: the answer simply sits now where the question was. So everything the node
  managed to do outward before the pause, it will do once more, and the email will go out twice. The rule:
  any outward action is placed after the pause point. Details:
  [side effects before the pause](https://docs.langchain.com/oss/python/langgraph/interrupts#side-effects-called-before-interrupt-must-be-idempotent).
- **The whole scenario:** start, pause, the process exits, resume with `approve`, the action
  executed exactly once. Separately run `reject`: the action is not executed at all.
  Repeat the resume on the same thread: there must be no second execution. You do not need to write a separate flag
  for this: on a finished thread a repeated resume does nothing.
  This holds on two conditions: the side effect stands after the pause, and the graph reached the end.
  It is checked with the `state` mode: in the snapshot of a finished thread there is no next step.

## Advanced blocks

All the blocks rest on the finished base program. Do at least one in full, more if you like.

### Block A: a real tool instead of a stub

Plug into the agent a search over the Qdrant collection built in the second module, instead of the stub.
The tool's input and output contract does not change: the body changes. In `report.md`
write down what changed in the loop's behavior when a real search came in place of the predictable stub: how many iterations
started going to a task and whether empty result sets appeared, after which the agent goes around a second time.

### Block B: measuring short-term memory on a long dialogue

Run a dialogue of 25+ exchanges and on each model call take two numbers: how many messages
went into the request and how many input tokens the provider counted. They read differently. The number of
messages hits the window's ceiling exactly. The number of tokens reaches a plateau and then fluctuates
around it along with the message length: one long tool response gives a jump up, and that is
normal. A linear growth of both numbers from exchange to exchange means the trimming is not applied.

Look separately at the size of the state snapshot: it will keep growing, and that is not an error. Trimming
before the model call does not touch the state; messages are removed from there by a separate
delete operation. The difference between "what is in the state" and "what went to the model" is the block's main result.

The block needs a separate, interactive script mode on top of the base three: running 25 exchanges
one command-line call at a time would wear you out. The measurement table goes into `report.md`: the model
call, messages in the request, input tokens.

### Block C: strict serialization of snapshots

The block is done with an explicit list of allowed types, as "module, class name" pairs. The serializer
is passed in the `serde` argument of the checkpointer constructor, and `from_conn_string` does not accept it:
it has no arguments other than the connection string. So here the database is opened with the direct
constructor, and the `with` block from part 2 is not used in this variant:

```python
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer

serde = JsonPlusSerializer(allowed_msgpack_modules=[("myapp.models", "Ticket")])
saver = SqliteSaver(
    sqlite3.connect("checkpoints.sqlite", check_same_thread=False),
    serde=serde,
)
```

The library itself prints the needed pair in a warning on the first read.

There is a second way to enable the strict mode, the environment variable `LANGGRAPH_STRICT_MSGPACK=true`.
It enables the mode as a whole but does not add your domain types to it, so you cannot use it to check
that objects came back from the database as the same types. It is good for looking at the behavior
for a minute; the block is not submitted with it.

The block's trap: an unlisted type is returned from the database by the strict mode as a plain dict, without
an exception. So it is the second launch that breaks, not the first, and it will look like data corruption,
not like a configuration problem. In `report.md`: what you listed and how you checked that after
a restart the objects came back as the same types.

Both forms are described in the README of the `langgraph-checkpoint` package on PyPI, the Serde section:
[pypi.org/project/langgraph-checkpoint](https://pypi.org/project/langgraph-checkpoint/).
The documentation pages that you keep open for part 2 do not mention the strict mode
at all.

### Block D: a third decision and the irreversibility boundary

Add to `approve` and `reject` an `edit` option: the pause hands out a draft of the action, the human
returns the corrected text, the graph continues with the edit. The log must show that
it was the corrected action that was executed, not the original one.

Plus a paragraph in `report.md`: where your agent's irreversibility boundary lies and why the pause
stands exactly there. Rely on the criterion of session 3.1, not on a general sense of the step's importance.
If the agent has several such boundaries, name them all and explain why the pause stands on this one.

## Where it usually breaks

A short summary of the pitfalls most people hit. Half of them are silent: everything "works",
there is no error anywhere, and the result is wrong.

- **An incomplete initial state.** A schema without default values, only `messages` passed at the start,
  and the very first node fails looking for the counter field. Cured by a constant holding the full
  initial state.
- **The checkpointer opened wrongly.** Without the `with` block you get `TypeError: Invalid checkpointer
  provided`, and the hint at the end of the message advises changing the checkpointer. The checkpointer is right,
  the block is missing.
- **A 400 from the provider on a trimmed history.** An orphaned tool result at the start of the window
  or a dangling tool call at the end. The first is closed by `start_on`, the second by `end_on`, and without the
  second you will certainly run into it on the `reject` branch.
- **A plain dict instead of the resume command.** The graph starts over, reaches
  the pause again and asks again. Looks like a hang, but in fact every launch starts
  from scratch.
- **A side effect before the pause.** The node is re-executed from the beginning, the action goes outward a second
  time. You will see the duplicate email or duplicate comment not in the log but at the recipient.
- **The `reject` branch checked by truthiness.** The decision arrives as a string, and `if decision:`
  on the string `"reject"` is true. The refusal executes the action and raises no error: a silent
  breakage of exactly the scenario you are submitting.
- **An error counter without its own reducer.** The field's value is determined entirely by the node that wrote
  last, and what was accumulated for the previous tool is lost. The loop spins longer and costs
  more, and nothing is visible in the log.
- **The full initial state mixed into every call.** On the second exchange in the same thread
  it overwrites the counters with the values from the constant, and the iteration limit stops firing.
- **The provider package not installed.** The import passes, the call fails. Read the exception text:
  it says outright what to install.
- **Block C: an unlisted type.** It comes back from the database as a plain dict, without an exception.
  The second launch breaks, not the first.

The first question for strange loop behavior is always the same: what exactly went to the model at this step.
Printing the window before the call or the tracing from the observability guide answers it in a minute.

## What to submit and acceptance criteria

### What to attach

Everything in the private repository of the course project, with the link in the field at the bottom of the assignment in the LMS:

- **the agent code:** the `agent_v2` folder in the main branch, plus `requirements.txt` with pinned
  versions and a `README` with two exact launch commands, start and resume. If you work
  in a separate branch, name it on the first line of `report.md` next to the submission level: the repository
  opens on the main branch, and the reviewer will not look into another branch;
- **`.gitignore`:** the provider key and the snapshot database file are not committed to the repository. The key goes
  through environment variables, the database file is a local artifact of the run;
- **`report.md`** following the skeleton below;
- **text logs of the runs.** Put the output in a `runs/` folder next to the agent code, one file
  per run, the file name is arbitrary. The log must show the launch commands, the value from the pause
  and that the action was executed once. There are five kinds of runs, six to eight
  launches in all:

  1. **Convergence:** 2–3 scenarios of your agent, each reaches a final answer within the
     iteration limit.
  2. **Isolation:** a second `thread_id` on the same database file starts with an empty state.
  3. **`approve`:** 3–4 exchanges on one thread, the process exits, resume with `approve`,
     the action executed exactly once. It is also the survival test: the continuation after the process
     exits is visible in this same log.
  4. **`reject`:** resume with a refusal, the action is not executed at all.
  5. **Repeated resume** on a finished thread: nothing happens;

- **`process-log.md`** following the skeleton below: 3–5 key prompts verbatim, including the unsuccessful ones,
  how you split the task, what you verified with, one case of the agent's error. A page in length.
  A decorative log of the kind "I asked it to write a graph, it wrote it" counts as missing;
- **advanced blocks, if you did them:** additions to the code and report sections named in the block
  description.

### What to write in report.md

The first line is the submission level, then the sections are copied as headings:

```markdown
Submission level: normal or advanced. For advanced: which blocks you did. If the work
is in a separate branch, name it here too.

# Module 3 homework report

## Agent contract
Written before the code: what the agent accepts, which tools it calls, what counts as a
successful result.

## Deviations from the contract
What in the code diverged from the contract record and why. If nothing diverged, say so.

## State schema
The schema fields and their purpose, which fields have their own reducer and why, where the
iteration limit stands and why this number was chosen.

## Short-term memory strategy
A window or folding into a summary, what you pay for it.

## Where the pause is and why exactly there
Which action of the agent is irreversible. What happens on the reject branch and whether
a trace of the refusal remains in the history.

## Runs
What is visible in the attached logs: convergence on 2–3 scenarios, isolation of the second thread,
`approve` with one execution and continuation after the process exits, `reject` without
execution, a repeated resume without a second execution.

## Block A: a real tool (if you did it)
What changed in the loop's behavior compared with the stub.

## Block B: memory measurement (if you did it)
A table: model call, messages in the request, input tokens. What happened to the size of the
state snapshot.

## Block C: strict serialization (if you did it)
What you listed in the allowed-types list and how you checked the second launch.

## Block D: a third decision and the boundary (if you did it)
Where your agent's irreversibility boundary lies and why the pause stands exactly there.
```

### The process-log.md skeleton

```markdown
# Working with the agent: module 3

## How I set the task
3–5 key prompts verbatim, including the unsuccessful ones. For the unsuccessful ones: how the wording
changed after the first failure.

## How I split the work
What I did myself, what I handed to the agent, why the boundary went exactly there.

## What I verified with
The step, what I ran by hand, which numbers I looked at, what I read with my own eyes before accepting.

## Where the agent made a mistake
One case: what the error was, how I found it, how I closed it.
```

### Acceptance criteria

- [ ] `report.md` states the submission level on the first line; for advanced the blocks done
      are listed.
- [ ] **The loop works and converges:** the agent calls tools and finishes the task within the
      iteration limit, confirmed by the output of the 2–3 runs in the submission.
- [ ] **The state survives the process exiting:** the continuation with the same `thread_id`
      is confirmed by the log of the `approve` scenario; isolation is confirmed by a separate run
      with a second identifier.
- [ ] **The pause stops the graph before the irreversible action:** resume with `approve`
      executes the action exactly once, with `reject` does not execute it at all, a repeated resume
      does nothing. All three are confirmed by the logs from `runs/`.
- [ ] **Short-term memory is bounded:** the code shows where and with what the history is trimmed, the window
      is closed at both ends, `report.md` names the strategy and its cost.
- [ ] **The code matches the contract:** `report.md` has the contract record made before the code,
      and an explicit statement of what in the code diverged from it and why.
- [ ] **`process-log.md` shows the path to the result:** setting the task for the agent, splitting
      into steps, checking the result, a walkthrough of one error. The check runs along two axes: the completeness
      of the result and how you worked with the agent.
- [ ] **The advanced level (if you submit it):** at least one block done in full. Block A: the search
      over the second module's collection works instead of the stub, an analysis of the changes in the report.
      Block B: a dialogue of 25+ exchanges, a table with two numbers per call, the number of messages hits
      the window's ceiling, the number of tokens reaches a plateau. Block C: the list of allowed types is set
      explicitly in the serializer, the second launch is checked. Block D: the log shows the execution of the
      corrected action, the report justifies the irreversibility boundary.

## The course project map: how the results are reused later

This is stage 5 of the course project. Stages 1–3 (the MCP server, agent roles, the n8n prototype) were submitted
in the first module, stage 4 (RAG on Qdrant) in the second.

| Module | What happens to this assignment's artifacts |
|---|---|
| Module 4 | The agent skeleton is extended into a multi-agent graph: routing between roles, a supervisor and a shared state schema. The domain fields of your agent become part of the shared state |
| Module 5 | Offline quality evaluations are built on this same agent; the loop runs become tests on the route, not on the answer text |
| Module 6 | The agent's runs get into tracing in full, including pauses and resumes |
| Module 7 | The economics of exactly this agent are computed, tokens per task before and after the memory limit, and an audit of the security of its tools and pause boundaries is carried out |

The cleaner the state schema now, the cheaper the fourth module: the shared fields are assembled
from yours, not rewritten from scratch.

## How to submit your work

At the bottom of this assignment in the LMS there is one input field. Paste into it the link to your private
repository and press the submit button. Nothing else needs to be added to this field:
the work itself lives in the repository.

Submit your work exactly this way, even if you already sent the link to the course chat. Feedback
is written in the LMS and attached to your submission: anything sent outside this field is left without feedback
and without a mark.
