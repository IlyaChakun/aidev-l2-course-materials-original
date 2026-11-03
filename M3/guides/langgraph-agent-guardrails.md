# LangGraph: rules and pitfalls for a coding agent

> **Compiled on 17.08.2026. Verified by running against LangGraph 1.2.11** - the current release of the
> `langgraph` package for Python on the day of compiling (published 11.08.2026, requires Python 3.10+); alongside
> it, `langgraph-checkpoint-sqlite 3.1.1` and `langchain-core 1.5.5` were verified.
> **Check the major version before using this:** if yours is not `1.x`, treat the specifics
> of this file as suspect and ask the agent to update them from the official documentation (addresses are
> in § 1). Concepts survive a major version change, names and parameters do not.

This file is not written for a human to read, but to be handed to a coding agent. You open Claude Code or
Cursor, attach the whole file and describe the task in your own words: "here are the LangGraph rules, build
me an agent that does such-and-such, with state persisted to disk and one pause for my
confirmation". Models know LangGraph from documentation that is a year old or more: the API has moved
since then, and half of the rules below cannot be derived from the documentation at all - it is incomplete, and answers
to such questions are found in GitHub discussions and by running the code.

The only check of any rule from here is **a run on your own machine**: more than half of the errors
in § 7 give neither an exception nor a warning, the agent answers, and the system behaves differently from the code.

---

## 1. How the agent should work with this file

**The primary source is the official documentation, not this file and not the model's memory.** The documentation
has moved: the old address `langchain-ai.github.io/langgraph/` today serves only a redirect
page. Live addresses as of 17.08.2026:

- Root of the section: `https://docs.langchain.com/oss/python/langgraph/overview`
- **The machine-readable LangGraph index for Python**, about forty pages with links to the `.md` version
  of each: `https://docs.langchain.com/oss/python/langgraph/llms.txt` (4 KB). Start here.
- The index of all sections: `https://docs.langchain.com/llms.txt` (21 KB); the full dump in one file
  `https://docs.langchain.com/llms-full.txt` (6.2 MB, all products at once - do not load it into the context).
- Error pages: `https://docs.langchain.com/oss/python/langgraph/errors/INVALID_CHAT_HISTORY.md`

Any page can be fetched as text by appending `.md` to the address
(`https://docs.langchain.com/oss/python/langgraph/interrupts.md`). The key ones here are `checkpointers`,
`interrupts`, `add-memory`, `graph-api`, `event-streaming`, `persistence`.

**If your environment has documentation search and reading tools - use them
without fail, before writing code.** Built-in web search, Context7, Exa, documentation MCP servers:
any will do. Check class names and import paths, signatures, whether parameters are required.

**If there are no such tools - do not guess.** Tell the user directly: "I have no access
to the documentation, download the needed pages in `.md` form and attach them to the task". Code from the model's memory
breaks here not in theory: over the last year both the import paths and the name of the in-memory checkpointer have moved.

**The material in this file is layered, and the layers have different shelf lives.**

| Layer | What it is | How to treat it |
|---|---|---|
| Invariants | The graph, state and reducers, checkpointer and thread, pause and resume, the split between static and dynamic navigation | They hold for years. This is the frame of the solution, design around it |
| Specifics | Class names, import paths, signatures, parameter names, error texts | Verified on 17.08.2026 on 1.2.11. **Check against the documentation before writing code** |
| Field experience | Rules from the source talk and from the open example project (§ 9) | A supplement, not the norm. Some of them have already diverged from reality, the discrepancies are flagged in the text |

**The order for resolving contradictions:** the documentation beats field experience, and a fact verified
by a run on your version beats the documentation too - the pages lag behind the package, an example is in § 2.

---

## 2. Invariants: state, nodes, the loop

**The graph state is the only place where the agent's data lives.** A flag, a counter, the "already
authorized" marker, an accumulated answer - all of these are fields of the state schema; you must not keep them either in attributes of the node object
(`self.authorized`) or in module variables. Only the state goes to disk,
while `self` stays whatever it was in the process memory. The breakdown of the failure is in § 4.

**A schema on `TypedDict` has no default values.** If you passed only messages at the start, the
node fails at the first access to the counter: `KeyError: 'n'`. Keep a constant with the full initial
state and start from it; `pydantic.BaseModel` has defaults.

**A reducer is needed by a field that two parties write to** - not "by every list in a row". It is the rule by which the
new value is combined with the old one; there is no rule by default, and the consequences depend on how the nodes
are arranged. Verified both ways: sequentially - a silent loss (`{"sql": 1}`, then
`{"tables": 2}`, only the second remains), in parallel - a failure with `InvalidUpdateError: At key 'ctx':
Can receive only one value per step.` A field with a reducer in the same runs collects both values.

- Message history: `Annotated[list, add_messages]` (`from langgraph.graph.message import
  add_messages`) - it appends and matches messages by `id`. A node that returns
  `{"messages": [response]}` does not erase the history **only** thanks to it.
- Accumulating results from parallel executors: `Annotated[list, operator.add]`; without it
  the second executor overwrites the result of the first. Your own merge rule is any function of two
  arguments.

**A node is a function "state → partial update"**: it returns a dictionary with only the changed
fields. Returning a plain dictionary is legitimate, `Command` is needed for choosing the next step (§ 5).

**Only what survives being written to disk goes into the state:** numbers, strings, lists, messages,
simple models. A connection, a handle, an external API client cannot go there - the snapshot will not be written.

**The agent loop is built explicitly and always with a stop condition.** The canonical loop: model node → edge
with a condition → tools node → back to the model. The continuation condition is written positively -
"the model requested a tool", not "the model has not finished": the second variant cuts the work off
on tools executed on the provider's side.

**Your own iteration counter is mandatory, `recursion_limit` does not replace it.** By default it is **10,007**
steps: an emergency stop of the environment, not your budget, you will pay for everything up to it. Keep an
`iterations` field in the state and exit at your own threshold, starting at 5-8. **This is also an example of why you should check
by running:** the graph API page still names the limit as 1000 steps.

---

## 3. Checkpointer: state snapshots and the thread

**The thread (`thread_id`) is the unit of isolation.** One conversation, one run, one user - its own
`thread_id`, and it is passed into every call: `{"configurable": {"thread_id": "..."}}`. Verified:
a second `thread_id` on the same database file sees an empty state.

**The checkpointer and the store (`Store`) are different mechanisms.** The checkpointer writes the state at every step
and lives within the thread; `Store` holds facts between sessions by an address made of a namespace
and a key (usually with a user identifier). They are plugged in in one call as different arguments:
`compile(checkpointer=..., store=...)`. Verified: a write from one thread is read in another, while the
state of the threads stays separate. Both `config` and `store` arrive in the node **as arguments**.

**The snapshot is written between graph steps, not inside a step**, so a node that failed in the middle
runs from the beginning on resume - with all its side effects (§ 4).

**`SqliteSaver` is opened with a `with` block, and the graph is compiled inside the block.**

```python
from langgraph.checkpoint.sqlite import SqliteSaver

with SqliteSaver.from_conn_string("checkpoints.sqlite") as saver:
    graph = workflow.compile(checkpointer=saver)
    result = graph.invoke(input_state, config)
```

The connection string is an ordinary file path. Without `with` the code looks working and fails on the call:
`TypeError: Invalid checkpointer provided … Received _GeneratorContextManager. Pass a proper saver
(e.g., InMemorySaver, AsyncPostgresSaver).` The hint at the end points the wrong way: the checkpointer is chosen
correctly, only the block is missing.

**The second way is the direct constructor**, `SqliteSaver(sqlite3.connect(path, check_same_thread=False))`:
it is needed when the checkpointer outlives the block or when a serializer is passed to it. You cannot
combine them: `from_conn_string()` accepts **only** a connection string, a call with `serde=` gives
`TypeError: unexpected keyword argument 'serde'`. Strict serialization mode is enabled either by the
variable `LANGGRAPH_STRICT_MSGPACK=true`, or by `serde=JsonPlusSerializer(allowed_msgpack_modules=
[("myapp.models", "Ticket")])` in the constructor; a type that is not listed is returned from the database as a plain
dictionary, without an exception.

**For tests - `InMemorySaver`** (`from langgraph.checkpoint.memory import InMemorySaver`). The former
name `MemorySaver` is the very same object (verified: `MemorySaver is InMemorySaver`), but we write the new one.
The state lives inside the process: the scenario "pause → switched off → resumed" cannot be tested on it.

**Asynchronous code requires an asynchronous checkpointer:** `from langgraph.checkpoint.sqlite.aio import
AsyncSqliteSaver`, and the same block rule - `async with`. Open the context for handling one
request and compile the graph inside it. For prod - `AsyncPostgresSaver`
(`langgraph-checkpoint-postgres`), which needs `await saver.setup()` on the first run. The asynchronous
family was not verified by a run - check against the documentation.

**The moment of writing a snapshot is set in the call, not when building the graph:** `graph.invoke(..., durability=
"sync" | "async" | "exit")`. The default is `"async"`: fast, but there is a window in which a crash loses
the last snapshot. For irreversible actions use `"sync"`.

**A pause without a checkpointer deceptively works.** Verified: the graph reaches `interrupt()` and returns
`{"__interrupt__": [...]}` - the first run looks successful, and it is the resume that breaks:
`RuntimeError: Cannot use Command(resume=...) without checkpointer`.

---

## 4. Pausing for a human: `interrupt` and `Command(resume=...)`

One import: `from langgraph.types import interrupt, Command`.

**The main rule, from which almost all the others follow: on resume the node runs
again from the beginning.** Not from the line where the pause was: `interrupt()` in this run will not stop
execution, but will return what the human sent. Verified - a side effect before the pause is executed
twice: `['email sent', 'email sent', 'after the pause: yes']`. **Everything that acts
outwards is placed after the pause point.**

**`interrupt()` must not be wrapped in `try/except`.** The pause is implemented as an exception, and a generic
handler swallows it. Verified: with `except Exception` the node catches `GraphInterrupt`, goes on
with the value `None`, the graph finishes, there is no `__interrupt__` in the result at all, `next` is empty - the pause
does not exist, and there is no way to find out. If you need a handler, `except GraphInterrupt:
raise` goes first (the class is in `langgraph.errors`), and only then the generic `except`.

**You must not skip the `interrupt` call on a condition inside one node**, that is, the node must make
the same number of pauses in any scenario. The failure scheme: the node first asks for an authorization code,
then for the user's answer, and the "already authorized" marker is held in an attribute of the object. Answers
are matched to pauses **strictly by call index**, so on the third step, when the first pause
is skipped, the second takes its value. Verified: the human sent `"my answer"`, and the state received
the code `"1234"` - without an error, and the completion marker lies on top of that.

The cure is the rule from § 2: the marker lives in the graph state, and after processing the answer the node **exits**,
returning a route, instead of going to the second pause in the same execution:

```python
def gate(state) -> Command[Literal["gate", "__end__"]]:
    if not state.get("authorized"):
        code = interrupt("enter the authorization code")
        return Command(goto="gate", update={"authorized": code == "1234"})
    answer = interrupt("your answer")
    return Command(goto=END, update={"answer": answer})
```

**The "approve / reject" decision is passed parsed, not as a string.** The canonical documentation example
branches on truthiness: `Command(resume=True)` - approve, `Command(resume=False)` -
reject. If the decision arrives as a word from the command line or from a chat, parse it before the call:
`Command(resume=(arg == "approve"))` or with a dictionary `{"decision": arg}`. Verified: `bool("reject")`
is truthy, and the rejection branch executes the irreversible action the same way as approval - silently, without an error.

**Resuming is a separate command, not an ordinary call.** Verified: if you pass the answer as an ordinary
input dictionary, the graph starts the node over, reaches the pause again and asks again, which looks like a
hung agent. You do not need to know the continuation point, `Command(resume=...)` finds it from the snapshot:
that is why a messenger, a queue and a process restart legitimately sit between the question and the answer.

**`update_state` during a pause erases the record of the interrupt.** Verified: before the call
`state.interrupts` contains the pause, after it - empty (`next` is the same, the resume works). Code
that determines the presence of a pause by `state.interrupts` will then decide that the graph has finished.

**How to read a pause - three forms, they must not be mixed in one script** (the value passed
to `interrupt()` must be serializable in all three: strings, numbers, lists, dictionaries):

| Form | Where to look for the pause | Note |
|---|---|---|
| `graph.invoke(...)` | the `__interrupt__` key in the result | verified, works; the documentation calls it current |
| `graph.stream(..., stream_mode="updates")` | the event `{"__interrupt__": (Interrupt(...),)}` | verified; convenient when you need per-node progress |
| `graph.stream_events(..., version="v3")` | `stream.interrupts`, `stream.interrupted` | the documentation leads its examples with this form, but the package prints `LangChainBetaWarning: The v3 streaming protocol on Pregel is experimental` |

One more way: `graph.get_state(config).next` - during a pause it holds the node name, after completion
an empty tuple. Resuming a finished thread again does nothing, a separate idempotency
flag is not needed.

---

## 5. Navigation: edges versus `Command(goto=...)`

**There are two ways, and exactly one is chosen for each transition.**

Static - `add_edge` and `add_conditional_edges`: all paths are known at compile time, and the route
function **only reads the state and returns the branch name**, like
`return "tools" if state["messages"][-1].tool_calls else "done"` with
`add_conditional_edges("model", route, {"tools": "tools", "done": END})`. The ban on writing to the state
is not declarative: verified, an assignment in the route function is silently lost, and the next node sees the
field empty.

Dynamic - `Command`: the node itself names the next step and updates the state at the same time,
`return Command(goto="tools", update={"iterations": state["iterations"] + 1})`. Use it where
the routing decision is itself the result of the node's work: routers, a clarification loop at a pause.

**The widespread rule "always return `Command`, not a dictionary" is wrong on today's versions**
and in that form does harm: an ordinary dictionary return from a node works and is the norm for
linear stretches where the route is set by an edge. `Command` is needed for `goto`, not for `update`.
Do not mix the two ways on one transition: if `Command(goto=...)` leaves a node, do not add
an edge to the same node.

Parallel launch of one node on several input sets is done through `Send`
(`from langgraph.types import Send`; the path `langgraph.constants` has been deprecated since version 1.0 and prints a
warning). Details are in the next module; here it is enough to know that the accumulating field
for their results must have a reducer, otherwise the executors will overwrite each other.

**The rendered graph diagram is the compiled structure, not the execution path.** Verified: for a graph
with a fan-out through `Send` the diagram shows one conditional edge `plan → joke`, while the event stream shows three
executions of the node in a row. Look at the actual flow of execution in the stream, not in the picture.

---

## 6. Short-term memory and history trimming

**Short-term memory is the message history in the thread state**, not a separate subsystem. A
`messages` field with the `add_messages` reducer, a checkpointer and one `thread_id` per conversation - that is enough.

**Trimming is needed separately: the checkpointer does not shorten the history, it accumulates it.** The tool is
`trim_messages` from `langchain_core.messages`. It has **two required named arguments**, and
a call without them fails: `TypeError: trim_messages() missing 2 required keyword-only arguments:
'max_tokens' and 'token_counter'`.

```python
from langchain_core.messages import trim_messages

window = trim_messages(
    state["messages"],
    strategy="last",
    token_counter=len,          # count by messages; in prod - a token counter
    max_tokens=12,              # with token_counter=len this means "12 messages"
    start_on="human",
    end_on=("human", "tool"),
    include_system=True,
)                               # the window goes to model.invoke(window)
```

**Boundaries are needed at both ends, and this is not stylistics.** `start_on="human"` stops the window from
starting with a tool result without its call; `end_on=("human", "tool")` stops it from
ending with a tool request without a paired result. Verified: without `end_on` the last
message of the window turns out to be a model answer with an unpaired `tool_call`, and the provider does not
accept such a history - that is a 400 response (the framework describes the same case on the `INVALID_CHAT_HISTORY` page).
It always happens when the pause stands before an irreversible action: the model requested a tool,
and the rejection branch does not execute it. If the rejection must stay in the history, append
a `ToolMessage` with the same `tool_call_id` on it.

**Check that the window does not collapse.** At a small limit both boundaries together cut off almost
everything: verified, `max_tokens=2` with counting by messages leaves `[SystemMessage, HumanMessage]`.
Log the length of the window. For counting by tokens - `token_counter=count_tokens_approximately`.

**The result of trimming is a window for the model call, not a new state.** Do not write it back
into `messages`: `add_messages` appends rather than replaces, and you will get duplicates. Deleting from the history is
a separate mechanism (`RemoveMessage`), it is not needed here.

---

## 7. Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `TypeError: Invalid checkpointer provided … Received _GeneratorContextManager` | `from_conn_string` called without `with` | a `with` block, the graph is compiled inside it |
| `TypeError: … unexpected keyword argument 'serde'` | the serializer was passed to `from_conn_string` | the direct constructor `SqliteSaver(conn, serde=...)` |
| `RuntimeError: Cannot use Command(resume=...) without checkpointer` | the graph was built without a checkpointer, the first run hid this | `compile(checkpointer=...)` |
| `KeyError: 'field'` on the first step | a schema on `TypedDict` without defaults, started with an incomplete dictionary | one constant with the full initial state |
| The graph ran to the end, there was no pause at all | `interrupt()` inside `try/except Exception` | `except GraphInterrupt: raise` first, or remove the handler |
| The agent asks the same question again and again | the answer was passed as an ordinary input instead of `Command(resume=...)` | resume only with the command |
| The human's answer went into the wrong field, no error; after a restart the agent "forgot" the authorization | the `interrupt` call was skipped on a condition on a flag from `self`, and matching goes by index | the marker in the graph state, exit the node with `Command(goto=...)` after the pause |
| An outward action was executed twice | the side effect is before `interrupt`, the node restarts from the beginning | move the action after the pause point |
| A rejection executed the irreversible action | the decision arrived as a string, branching on truthiness; `bool("reject")` is truthy | `Command(resume=(arg == "approve"))` or parsing by a dictionary key |
| The code thinks the graph has finished, although a pause is standing | `update_state` during the pause erased the record of the interrupt | make edits only via `update=` in `Command` |
| 400 from the provider about `tool_call_id` | the history window ends with a tool request without a result | `end_on=("human", "tool")`; on the rejection branch append a `ToolMessage` |
| `TypeError: trim_messages() missing 2 required keyword-only arguments` | `max_tokens` and `token_counter` were not passed | pass both; `token_counter=len` - counting by messages |
| The accumulated field loses the data of the previous node | the field has no reducer, the new value overwrites the old | `add_messages` for the history, `operator.add` or your own merge function |
| `InvalidUpdateError: … Can receive only one value per step` | two parallel nodes write to one field, the field has no reducer | add a reducer to the field that two parties write to |
| An assignment in the route function is not visible further on | `add_conditional_edges` functions do not change the state | return the decision, and change the state in the node via `Command(update=...)` |
| `GraphRecursionError`, or an endless run and a growing bill | no stop condition of your own; `recursion_limit` taken for a budget, but it is 10,007 steps | an iteration counter in the state, your own threshold of 5-8 |

---

## 8. Code acceptance checklist

Each item is verified **by a run**, not by reading the code.

1. The agent answers a question without tools and a question with a tool; the number of iterations is in the log.
2. A scenario with a stably failing tool stops at **your** iteration threshold.
3. The first run created the snapshot database file, and a conversation on a new `thread_id` does not see someone else's history.
4. The pause: the script prints the value that came from `interrupt` and ends the process.
5. **The resume happens in a new process** - on one process this check proves nothing.
6. Approval executes the action; rejection **does not execute it at all**, and the log shows which branch.
7. The side effect is not repeated after the resume: there is one record in the log of external calls.
8. Resuming a finished thread again does nothing and does not fail.
9. On a long conversation the window going into the model stops growing, the answers stay coherent.
10. The rejection branch does not leave a tool request without a result in the history: the next turn has no 400.
11. There are no keys or tokens in the code: everything is read from the environment.

---

## 9. What is not here

The file describes **one** agent on a graph with a checkpointer, short-term memory and one pause
for a human. Not included: several agents over one graph, a coordinator role, a parallel fan-out
through `Send`, long-term memory through `Store`, rolling back to a snapshot for debugging, token streaming
and evaluation by route tests.

A live example of a full-size agent with pauses and state accumulation is the open example project
`https://github.com/Bbar0n234/learnflow-ai`, the patterns are collected in its skill for a coding agent.
This is field experience in the sense of § 1: a source of forms, not the truth about versions.
