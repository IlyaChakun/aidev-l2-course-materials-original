# LangChain Code node: rules and pitfalls for a coding agent

This file is not written for a human to read, but to be handed to a coding agent. You open Claude Code
or Cursor, attach the whole file and describe the task in your own words: "here are the rules of the LangChain
Code node, write me a node that does A, B and C". The agent knows LangChain from the framework's documentation,
but it does not know the dialect this node speaks inside n8n: it has its own sandbox, its own way
to get the connected nodes and its own return format. Without these rules it will write code that looks
right and fails on the very first run.

Everything below was verified by runs on self-hosted n8n 2.23.2. The version matters: some behavior changes
silently between versions, and the main discrepancy is flagged directly in the text. The rules can be checked
in only one way: by running the node on your own test stand. Reading the code with your eyes is not enough: half
of the errors in the table at the end are visible only at runtime. If your stand runs a different version, start by running
the skeleton from section 3, make sure it passes, and only then build up the logic.

The primary sources to check against are the official LangChain Code node page on
[docs.n8n.io](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.code/)
and the LangChain JS documentation ([js.langchain.com](https://js.langchain.com)). The rules are layered:
the sandbox invariants rarely change and make up the core of the file, while you should check specific method and
parameter names against the documentation. If you (the agent) have extra search tools - Context7,
Exa, web search, documentation MCP servers - check signatures against them before writing code;
if not, ask the user to attach the current documentation pages next to this file.

---

## 1. Sandbox invariants

**What the sandbox does NOT have. Do not suggest, import or substitute as a fallback:**

- **`fetch` is `undefined`.** Any network call through `fetch` fails immediately.
- **There are no arbitrary npm packages.** `require('langfuse')`, `require('langsmith')`, `require('axios')`
  and the like give `Cannot find module`. You cannot install a package into the node's sandbox.
- **There is no `this.emit()`.** There is no way to stream progress to the UI; intermediate statuses go only
  to `console.log` and are visible in the browser console.
- **Treat `crypto` as unavailable.** If you need an identifier, write your own three-line generator.
- **There is no file system for arbitrary reads.** `window.fs.readFile` and the like do not work.

**What IS there and what everything rests on:**

- **`require('@langchain/core/messages')` works** - `ToolMessage` comes from there. Other
  subpaths (`prompts`, `runnables`, `output_parsers`) can be tried, but only through `try/catch`
  and with a working fallback: the code must run even when `require` returned `null`.
- **`this.getInputConnectionData(type, index)`** is the only way to get the connected nodes.
  Types: `'ai_languageModel'`, `'ai_memory'`, `'ai_tool'`. The second argument is **`itemIndex`, the number of the
  input item being processed**, not the input number and not the connection number. You cannot use it to address
  a specific connected node: one call returns everything connected to the input of that type.
- **`this.helpers.httpRequest({method, url, headers, body, json: true})`** is the only way
  to reach the network.
- **`$input.all()` and `$input.item`** are the node's input. The payload lives in `item.json`
  (for the chat trigger these are `chatInput` and `sessionId`).

**Ports are declared in the node's parameters, not in the code.** In a workflow export it looks like this, and without
this part the code will never work - `getInputConnectionData` will return nothing:

```json
"parameters": {
  "code": { "execute": { "code": "..." } },
  "inputs":  { "input":  [ {"type": "main"}, {"type": "ai_languageModel"},
                           {"type": "ai_memory"}, {"type": "ai_tool"} ] },
  "outputs": { "output": [ {"type": "main"} ] }
}
```

If you need a second output, add a second `{"type": "main"}` to `outputs`.

**Two models in different roles are connected to ONE `ai_languageModel` input** (verified by a run on
2.23.2 on a workflow with two model nodes). You do not need to create a second input of the same type, and
you cannot reach the second model through the second argument of the call - that is `itemIndex`. One call
returns both, and the code then sorts them out.

**Return.** One output - a flat array `[{ json: {...} }]`. Two outputs - an array of arrays
`[[{json:...}], [{json:...}]]`. Mixing up these two formats is the most common error on the second output.

**`this` is lost inside regular `function`s.** `this.helpers` and `this.getInputConnectionData`
are available at the top level of the code. Anything that uses them is written either at the top level or
inside arrow functions that close over the outer `this`.

**The shape of the response floats, the most expensive pitfall.** Public guides for this node claim
that `getInputConnectionData` **always** returns an array, and take `llmArray[0]`. On 2.23.2 an input
with one connection returns the **object directly**, while an input with two or more connections returns an array.
Code written for one of these two shapes fails on the other. Always normalize:

```js
const pickOne  = (v) => (Array.isArray(v) ? v[0] : v);
const pickMany = (v) => (Array.isArray(v) ? v.filter(Boolean) : (v ? [v] : []));
```

**The order of elements in this array does not match the connection order and can change silently.**
You cannot assume that element zero is the model you connected first: it is enough to reconnect a link
and the roles swap places without a single error in the log. Sort them out only by
the properties of the objects themselves - `temperature`, `modelName` - and fail with a clear message if the needed
model is not among the connected ones.

---

## 2. Node skeleton

A compact working skeleton: memory + tools + model + return. Use it as a starting point.

```js
// 1. PORTS. Connected nodes are not visible in $json - each one has to be fetched separately.
const pickOne  = (v) => (Array.isArray(v) ? v[0] : v);
const model  = pickOne(await this.getInputConnectionData('ai_languageModel', 0));
const memory = pickOne(await this.getInputConnectionData('ai_memory', 0));
const raw    = await this.getInputConnectionData('ai_tool', 0);
const tools  = Array.isArray(raw) ? raw.filter(Boolean) : (raw ? [raw] : []);

// Take ToolMessage from langchain if the module is available; otherwise a plain object with a role.
let ToolMessageCtor = null;
try { ToolMessageCtor = require('@langchain/core/messages').ToolMessage; } catch (e) {}

const SYSTEM = 'Agent instruction. For arithmetic ALWAYS call the calculator tool.';
const MAX_ITERATIONS = 5;             // hard safeguard against an infinite loop
const results = [];

for (const item of $input.all()) {
  const question  = item.json.chatInput ?? item.json.text ?? '';
  const sessionId = item.json.sessionId ?? 'no-session';

  // 2. MEMORY for reading: the history arrives as an array of messages.
  let history = [];
  if (memory) {
    const mem = await memory.loadMemoryVariables({});
    const stored = mem?.chat_history ?? mem?.[memory.memoryKey];
    if (Array.isArray(stored)) history = stored;
  }
  const messages = [{ role: 'system', content: SYSTEM }, ...history,
                    { role: 'user', content: question }];

  // 3. TOOL LOOP: model -> calls -> results -> model again.
  const bound = tools.length ? model.bindTools(tools) : model;
  let response = await bound.invoke(messages);
  let iterations = 0;

  while (Array.isArray(response.tool_calls) && response.tool_calls.length && iterations < MAX_ITERATIONS) {
    iterations += 1;
    messages.push(response);          // the assistant message WITH tool_calls is mandatory BEFORE the results
    for (const call of response.tool_calls) {
      const tool = tools.find((t) => t && t.name === call.name);
      const observation = tool ? await tool.invoke(call.args)
                              : 'Tool ' + call.name + ' is not connected to the node';
      const text = typeof observation === 'string' ? observation : JSON.stringify(observation);
      messages.push(ToolMessageCtor
        ? new ToolMessageCtor({ content: text, tool_call_id: call.id, name: call.name })
        : { role: 'tool', content: text, tool_call_id: call.id, name: call.name });
    }
    response = await bound.invoke(messages);
  }

  const finalText = typeof response === 'string' ? response
                  : (response?.content ?? response?.text ?? String(response));

  // 4. MEMORY for writing: without this the next turn remembers nothing.
  if (memory) await memory.saveContext({ input: question }, { output: finalText });

  results.push({ json: { output: finalText, question, iterations, sessionId } });
}

return results;
```

---

## 3. Memory: rules

- **It is read through `memory.loadMemoryVariables({})`**, the history lives under the key `chat_history`
  (on a node with non-standard settings - under `memory.memoryKey`, check both).
  This object has no `getChatMessages` method.
- **It is written ONLY manually: `memory.saveContext({input}, {output})` at the end of every turn.**
  Unlike the ready-made agent node, LangChain Code itself writes nothing to memory. If you forget the call,
  the agent answers correctly, and on the next turn does not remember a word, and it looks like a broken
  memory rather than a missed line of code.
- **Simple Memory on a multi-process stand and in queue mode does not survive the execution boundary**:
  it is an in-process buffer, the next turn may be served by another worker, and the history will be empty.
  For anything more complex than a single-process demo, use Postgres Chat Memory.
- **The session key in the table is global.** Two different agents with the same `sessionId` read each
  other's history. Separate them with a prefix: `agentName + ':' + sessionId`.
- **Put a summary into memory, not the raw material.** An agent that saves a forty-kilobyte report
  into the history will hit the model's context and the token bill by the third turn. Save a short
  result: "report on topic X assembled, N sections".
- **The message order is fixed**: system message, then history, then the user's new question.
  The history is inserted as an array of messages, not glued into the prompt text.

---

## 4. Tools: the loop and stop conditions

- **Binding:** `model.bindTools(tools)` returns a **new** object, the original model stays without
  tools. You must call the bound one. Keeping both is useful: a planning call without tools is
  cheaper.
- **The loop is exactly this:** `invoke` → `response.tool_calls` → for each call `tool.invoke(call.args)`
  → the result goes back into `messages` as `ToolMessage(content, tool_call_id, name)` → `invoke` again,
  as long as `tool_calls` is non-empty.
- **The assistant message with `tool_calls` is put into `messages` BEFORE the tool results.**
  The provider rejects a history where a result refers to a `tool_call_id` that is not in the previous
  message - that is a 400 response, not a clear n8n error.
- **`tool_call_id` is mandatory and must match** the identifier from `call.id`. You must not invent
  your own.
- **The tool is looked up by `name`**, not by position in the array. If it is not found, return a text
  observation "tool is not connected" into the history instead of throwing an exception: the model can work its way
  out of that, and the run continues.
- **The tool result is normalized**: a string as is, an object with `.content` - take
  `.content`, any other object - `JSON.stringify`. External APIs return all three forms.
- **A hard stop condition is mandatory.** `MAX_ITERATIONS ≤ 5` for the tool loop. Without it the first
  tool that stably returns an error sends the agent into an infinite loop, which you
  notice from the token bill. For a multi-step scenario, set two independent limits:
  on the number of plan steps and on the number of iterations within a step.
- **The model will not call a tool unless you explicitly ask it to.** The system prompt says
  it directly: "for ANY arithmetic always call calculator, do not compute yourself". A vague "you have
  tools" gives a run with no calls at all.
- **Parallel workers are not a tool loop.** Several independent tasks are run
  with a plain `Promise.all` over several `model.invoke` calls. Three calls take the time of one, and this
  works; do not mix them with the tool-calling loop in the same place in the code.
- **Roles among several connected models are separated by a property, not by array
  index.** The order in the array is not guaranteed and need not match the connection order:
  on a verification run the port returned the models in reverse order. It is more reliable to sort
  by `temperature` or to check `modelName`.

---

## 5. Network and external APIs

- **The only way:** `await this.helpers.httpRequest({ method, url, headers, body, json: true })`.
  With `json: true` the body is serialized and the response is parsed automatically.
- **Call it from the top level or from an arrow function.** Inside a regular `function`, `this`
  points into the void, and you will get `Cannot read properties of undefined (reading 'httpRequest')`.
- **SDKs of external services are unavailable.** Observability, a vector database, any third-party service -
  only direct HTTP calls to their API. This usually means: build the request body by hand from the
  documentation and send it as one batch at the end of the run.
- **Any external call is wrapped in `try/catch`.** Telemetry that brought down the agent's answer is
  a defect. Put the error into the node's output as a separate field (`langfuse: 'error: ...'`) and continue the run.
- **There are no keys or addresses in the node's code.** The code keeps a placeholder (`const API_BASIC =
  '__API_BASIC__';`) and a check "if the placeholder is not replaced, skip the integration". The real
  values are substituted on the stand, from credentials or environment variables. The workflow export
  goes into the repository together with the node's code, and everything written into the code goes with it.

---

## 6. Common errors

| Symptom | Cause | Fix |
|---|---|---|
| `fetch is not defined` | there is no `fetch` in the sandbox | `this.helpers.httpRequest` |
| `Cannot find module 'langfuse'` (`langsmith`, `axios`) | arbitrary npm packages are unavailable | a direct HTTP call to the service's API |
| `Cannot read properties of undefined (reading 'httpRequest')` | `this` is lost inside a regular `function` | an arrow function or the top level |
| `Expected a Runnable` | the port returned an array, the code expected an object | `pickOne`, always normalize |
| `model.bindTools is not a function` | took `arr[1]` where there is only one connection | `pickOne`/`pickMany`, do not address by index |
| The code "picks a model" with the second argument `getInputConnectionData(..., 1)` | the second argument is `itemIndex`, not the input number | all models are fetched in one call; the port returns an array with two or more connections |
| The agent answers correctly but does not remember the previous turn | no `memory.saveContext` | add the call at the end of the turn |
| The history is empty while the memory is alive | Simple Memory did not survive the execution boundary | Postgres Chat Memory |
| Someone else's conversation shows up in the dialog | the session key in the table is global | the agent prefix on `sessionId` |
| `memory.getChatMessages is not a function` | wrong method of the memory object | `loadMemoryVariables({})` |
| 400 from the provider, a complaint about `tool_call_id` | the tool result has no preceding message with `tool_calls` | `messages.push(response)` before the results |
| The run never ends, the bill keeps growing | no stop condition in the tool loop | `MAX_ITERATIONS`, a separate limit on plan steps |
| Tools are connected, zero calls | the system prompt does not require calling them | an explicit instruction "always call X for Y" |
| `doesn't return array of arrays` | two outputs, returned a flat array | `return [[out1], [out2]]` |
| `[object Object]` arrives in the chat | returned the message object, not its text | `response.content ?? response.text` |
| `promptValue.toChatMessages is not a function` | a chain of a prompt template and a model with tools was assembled incorrectly | assemble the `messages` array by hand, without a chain |
| `require('@langchain/core/...')` fails | the subpath is unavailable in this version | `try/catch` + a fallback object `{role: 'tool', ...}` |
| The input is empty with several items | the code reads only `$json` | `$input.all()`, the data is in `item.json` |
| A file from the chat is not read | the node keeps the binary in its own structure | `this.getInputData()[0].binary.data0`, `.toString('utf8')` |
| Garbage is extracted from a PDF | `.toString('utf8')` does not parse PDF | text formats, or parsing before the input to the node |

---

## 7. Acceptance checklist

Each item is verified **by a run on the stand**. Reading the code and the agent's confidence that "everything
is covered" do not count as verification: half of these errors are visible only at runtime.

1. The node runs without an error on an empty question and on an ordinary one.
2. A second turn with the same `sessionId` remembers the content of the first.
3. A turn with a new `sessionId` does not see someone else's history.
4. A question that requires a tool gives a non-empty list of calls with arguments in the output.
5. A question that does not require a tool passes without calls.
6. A tool with a broken address does not bring down the run: the error is visible in the response, and the agent continued.
7. A scenario where the tool always returns an error stops at the iteration limit
   instead of spinning on.
8. Both outputs return data, if there are two outputs.
9. The node's output contains run counters: the number of iterations, the number of model calls, the length of the history.
   Without them there is nothing to analyze the agent's behavior with.
10. A search through the node's code finds not a single key, token or stand address.

---

## 8. What is not here

This file describes **only** the LangChain Code node inside n8n. Not included here, and living in a separate
artifact, are: agents on LangGraph and in Python, state graphs, checkpointers and long-term
storage, recovery after a failure, streaming and pauses for human confirmation, testing
and quality evaluation of the agent, as well as the criteria for moving from low-code to code. The rules above are about the dialect
of one node, not about designing an agent.
