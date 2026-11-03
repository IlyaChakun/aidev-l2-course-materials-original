# Connecting LangSmith and Langfuse to self-hosted n8n

> Compiled on 17.08.2026. Both setups were connected and verified by runs on the course's demo stand:
> self-hosted n8n in queue mode (main container, workers, runners), LangSmith in the cloud,
> Langfuse deployed next to the stand.
>
> The instructions are tied to the versions and interfaces of mid-2026. Before using them,
> check the details against the official documentation: [docs.smith.langchain.com](https://docs.smith.langchain.com)
> and [langfuse.com/docs](https://langfuse.com/docs). If you hand the file to a coding agent, ask
> it to re-check the commands at these addresses or with extra search tools (Context7, Exa,
> web search, documentation MCP servers), and if it has none, attach the current
> documentation pages to the task.

## Why this and when to use it

The n8n agent node shows the input and the output. Everything in between - the system instruction the
node assembled, each model iteration, each tool call with its arguments and result, the time
of each step, tokens and money - is not visible in the n8n interface at all. As long as the agent answers correctly,
this is tolerable. As soon as it starts answering wrongly, you are debugging a black box from a single
final text.

Tracing lifts the lid. The run unfolds into a tree: calls, nesting, durations,
tokens, cost. It costs zero (the LangSmith free tier or your own Langfuse) and does not require
moving to code: since the n8n AI nodes are built on LangChain, the traces flow on their own.

Both setups work **only on self-hosted n8n**. In cloud n8n there is no access to the container's
environment variables, and there is no way to connect LangSmith with variables there.

**The boundary of this file.** Here is only connecting the tool: how to enable it, how to check that
it is enabled, and what it breaks on. What to measure, which metrics to consider useful, how to build evals
and assess the quality of the agent's answers - that is module six. We do not go there.

---

## 1. LangSmith: the vendor's cloud

### Step by step

1. Create an account at `smith.langchain.com`. Registration is free, and so are traces on the starter
   tier: you pay for volume, not for access.
2. **Remember the account's region.** During registration you choose US or EU, and it cannot be changed
   later. The endpoint address depends on it - see the pitfalls below.
3. Settings → API Keys → create a key. It is shown once, looks like `lsv2_...`.
4. Write the four variables into the `environment` of the n8n service in `docker-compose.yml` (or into `.env`,
   if the stand is built that way).
5. **Recreate the container**, do not restart it.
6. Run any chat through the agent node and open the project in the LangSmith interface.

### The docker-compose block

```yaml
services:
  n8n:
    image: n8nio/n8n
    environment:
      # ... your existing variables ...

      # LangSmith
      - LANGCHAIN_TRACING_V2=true
      - LANGCHAIN_ENDPOINT=https://eu.api.smith.langchain.com   # EU account
      # - LANGCHAIN_ENDPOINT=https://api.smith.langchain.com    # US account
      - LANGCHAIN_API_KEY=<your-lsv2-key>
      - LANGCHAIN_PROJECT=n8n-agents
```

`LANGCHAIN_PROJECT` is the name of the project under which the traces land in the interface. If you did not set the variable,
everything goes to the `default` project, all mixed together. Create a separate name at least for the demo stand.

```bash
docker compose up -d          # recreate, not restart
```

### What goes into the trace

Everything built on LangChain is traced, that is, all n8n AI nodes:

| What was run | What is visible in LangSmith |
|---|---|
| AI Agent node | The full `AgentExecutor` tree: request assembly, model call, response parsing, tool calls, nesting, tokens and cost for every step |
| LangChain Code node | A flat list of calls: each model call separately, each tool separately, with no common parent |

The flat list for the code node is not a defect. You call the model and tools manually, and there is simply
no common executor there that would glue them into a tree. If you want a hierarchy, either build it
yourself, or look at the agent node's tree.

### Pitfalls that cost a day

**1. `docker compose restart` does not pick up new variables.** The instructions for connecting
LangSmith that circulate online almost all end with the words "restart the container:
`docker compose restart n8n`". This does not work. `restart` restarts the process in the **already
existing** container, while the environment is fixed at the moment it is created. You added the variables,
the container did not see them, there are no traces, and no errors either. You need `up -d`: compose compares the configuration
with the running container and recreates it.

**In queue mode the workers must be recreated too.** The agent runs in a worker, not in the main
container. If you recreated only n8n, the traces will not flow, and it will look exactly like "nothing
worked".

**If the stand is built from several compose files**, bring it up with the same set of flags
(`-p <project-name> -f <file> -f <file>`) it was originally brought up with. A bare
`docker compose up -d` in the same folder will pick up the default files and start a **second stack**
under a different project name, fighting with the first for ports and volumes.

**2. The endpoint must match the account's region.** An EU account sends to
`https://eu.api.smith.langchain.com`, a US account to `https://api.smith.langchain.com`.
On a mismatch the server answers `403`, **but n8n does not report it**: tracing in LangChain
runs in the background and its errors do not fail the execution. The workflow is green, the LangSmith interface is empty.
The symptom "everything is configured, no traces" is, in nine cases out of ten, either `restart` instead of
`up -d`, or the region.

**3. You cannot install LangSmith yourself.** A common confusion: since there is self-hosted n8n, there must be
self-hosted LangSmith in docker compose too. There is not. Self-hosting LangSmith exists only
in the Enterprise plan, is deployed in Kubernetes and requires a commercial license. Everything available
without negotiating with the vendor is the cloud. The run data goes to the vendor; for a perimeter where this is
unacceptable, Langfuse is installed.

---

## 2. Langfuse: observability inside your own perimeter

### Why there is no native path

Langfuse is an open observability platform: the same traces, token and cost counting, deployed
on your side in docker compose, and the data does not leave your perimeter.

There is **no** built-in n8n → Langfuse integration. The "add environment variables" scheme that
works with LangSmith does not work here at all: `LANGCHAIN_*` are the variables of the LangChain
tracer, and LangSmith listens to them. The Langfuse tracer is not built into the n8n runtime, there is nothing to enable.
The official summary of possible paths is [langfuse.com/integrations/no-code/n8n](https://langfuse.com/integrations/no-code/n8n).

Two options remain: send the events yourself from code (if the agent lives in a LangChain Code node) or
install community wrappers (if the agent is built from ordinary AI nodes).

### The path through the LangChain Code node

In code you call the model and tools by hand, which means you can send the trace events by hand too. Sending goes to the
ingestion API as a batch to `POST /api/public/ingestion`, authorization is Basic:
the login is the project's public key `pk-lf-...`, the password is the secret `sk-lf-...`, and the header gets
the base64 of the string `pk:sk`.

Three event types cover the whole run:

| Event type | What it is created for | What it carries |
|---|---|---|
| `trace-create` | One per run | Name, session identifier, the whole input and output, metadata |
| `generation-create` | For each model call | Model name, input, output, start and end time, tokens |
| `span-create` | For each tool call | Tool name, arguments, result, time |

The identifiers are generated by the client, and the events are linked through `traceId`. You do not need to send them
one by one - one batch request at the end of the run.

**Two limitations of the node's sandbox** that you run into right away: it has **no `fetch`** and **no
`langfuse` package** (`require('langfuse')` does not resolve). The HTTP request is made through
`this.helpers.httpRequest`. `crypto` may also be unavailable, so it is easier to build
the event identifiers yourself.

```js
// Basic = base64("pk-lf-...:sk-lf-...")
const LANGFUSE_HOST = 'https://langfuse.example.com';
const LANGFUSE_BASIC = '<your-basic-token>';
const uid = () => 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
  const r = (Math.random() * 16) | 0;
  return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
});

const traceId = uid();
const now = () => new Date().toISOString();
const batch = [
  { id: uid(), type: 'trace-create', timestamp: now(), body: {
      id: traceId, timestamp: traceStartedAt, name: 'my-code-agent',
      sessionId, input: question, output: finalText, metadata: { iterations } } },
  ...llmCalls.map((c, i) => ({ id: uid(), type: 'generation-create', timestamp: now(), body: {
      id: uid(), traceId, name: 'llm-call-' + (i + 1), model: 'gpt-4.1-mini',
      startTime: c.startTime, endTime: c.endTime, input: c.input, output: c.output,
      usage: { input: c.usage?.input_tokens, output: c.usage?.output_tokens } } })),
  ...toolCalls.map((t) => ({ id: uid(), type: 'span-create', timestamp: now(), body: {
      id: uid(), traceId, name: 'tool:' + t.tool,
      startTime: t.startTime, endTime: t.endTime, input: t.args, output: t.result } })),
];

await this.helpers.httpRequest({
  method: 'POST', url: LANGFUSE_HOST + '/api/public/ingestion',
  headers: { Authorization: 'Basic ' + LANGFUSE_BASIC, 'Content-Type': 'application/json' },
  body: { batch }, json: true,
});
```

Wrap the sending in `try/catch` and put its result into the node's output as a separate field. Tracing
must not bring the agent down, but it must not stay silent about its own errors either: without such a field you cannot tell
"was not sent" from "was sent but not displayed". The absence of an exception does not by itself count as success -
the outcome is verified by the trace being visible in the interface.

A side effect of this fiddling is more useful than the traces themselves: it becomes visible that observability is
just events that you send yourself. In the agent node the framework sends them for you, which is why it seems
to come out of thin air.

### Workarounds for ordinary AI nodes

If the agent is built from standard nodes, there is nowhere to write to Langfuse from code. Third-party solutions remain:

| Path | What it does | Link |
|---|---|---|
| `n8n-nodes-openai-langfuse` | A wrapper node over the OpenAI model, duplicates the calls into Langfuse | [github.com/rorubyy/n8n-nodes-openai-langfuse](https://github.com/rorubyy/n8n-nodes-openai-langfuse) |
| `n8n-nodes-ai-agent-langfuse` | The same for the agent node | [github.com/rorubyy/n8n-nodes-ai-agent-langfuse](https://github.com/rorubyy/n8n-nodes-ai-agent-langfuse) |
| OpenRouter Broadcast | Routes calls through OpenRouter, broadcasting events to Langfuse | summary at [langfuse.com/integrations/no-code/n8n](https://langfuse.com/integrations/no-code/n8n) |
| An OpenTelemetry shipper | A separate service reads n8n executions and sends them as OTel traces | same place |

The first two are community packages from an independent author: they are installed into n8n as community nodes,
maintained outside the vendor and require trusting someone else's code in the perimeter where your model keys
live. On a demo stand - go ahead. On a working one - make it a conscious decision, not one made by inertia.

---

## 3. Key hygiene

The LangSmith key in `docker-compose.yml` and the Langfuse Basic token in the header of the node's code are **secrets**,
despite lying in convenient places.

- **Do not commit them to git.** Neither the compose file with a substituted `LANGCHAIN_API_KEY`, nor a workflow export
  with the token in the body of the code node. A workflow export is ordinary JSON, and the node's code lies in it as a string.
  Git history is immutable: a committed key will have to be revoked, not deleted.
- In the node's code - a placeholder (`<your-basic-token>`), the real value is substituted on the stand.
- **Do not show the keys in demos and screen recordings.** Neither in the terminal, nor in an open node,
  nor in the list of environment variables.
- **For sessions and experiments - a separate project** in Langfuse and a separate name in
  `LANGCHAIN_PROJECT`. Demo runs must not land in the same project your working
  perimeter writes to: there are hundreds of them, and they mix with the real telemetry.
- The LangSmith key is shown once. If you lose it, issue a new one and revoke the old one, do not
  leave it hanging.

---

## 4. The "it works" checklist

1. The variables are added to the n8n service (and to the workers, if queue mode).
2. The containers are **recreated** (`up -d`), not restarted.
3. A chat was run through the agent node.
4. The trace is visible in the platform's interface, in the right project.

If it is empty at the fourth step - check strictly in this order, from top to bottom:

| Check | How to make sure |
|---|---|
| Endpoint region | `LANGCHAIN_ENDPOINT` matches the account's region (EU or US). The most common cause |
| Container recreated | `docker inspect` or simply `docker ps` - the container's creation time must be later than the file edit |
| Workers recreated | In queue mode the execution happens in a worker; its environment is separate |
| Key | Not expired, not from another account, copied in full |
| Project | Look in the project named in `LANGCHAIN_PROJECT`; without the variable - `default` |
| n8n is really self-hosted | Cloud n8n has no container environment variables |

For Langfuse the order is the same, but the first item is different: look at what `httpRequest` returned from the node's
code. An authorization error means a wrong Basic (the project keys are mixed up or the base64 is corrupted),
an empty interface with a successful response - you are looking at the wrong project.

---

## 5. What is not in this file

Here is only the connection and the check that it is enabled. Deliberately not covered and dealt with
in module six:

- What exactly to measure and which metrics to consider useful.
- Answer quality assessments, datasets and evals on top of the collected traces.
- Labeling traces with user feedback and analyzing failed runs.
- Alerts, dashboards, budgets for tokens and cost.
- Choosing a platform for a working perimeter: pricing, storage, data requirements.

One thing is enough for today: you have something to look with, it is enabled in ten minutes and costs zero.

---

## Links

- [LangChain Code node documentation](https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.code/) - inputs, outputs, sandbox limitations
- [LangChain methods in n8n code](https://docs.n8n.io/code/builtin/langchain-methods/) - what is available inside the node
- [Langfuse integrations with n8n](https://langfuse.com/integrations/no-code/n8n) - the current summary of paths
- [Langfuse ingestion API documentation](https://langfuse.com/docs/api) - event types and the batch format
