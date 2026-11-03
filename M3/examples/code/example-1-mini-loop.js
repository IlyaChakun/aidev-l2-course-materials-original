/**
 * M3 · A mini agent loop by hand: memory + tools + model + observability.
 * The ports are declared below in Inputs/Outputs: main + ai_languageModel + ai_memory + ai_tool -> main
 */

const SYSTEM_PROMPT = 'Ты демо-агент занятия. Отвечай кратко, по-русски. Для ЛЮБОЙ арифметики всегда вызывай инструмент calculator - не считай сам.';
const MAX_ITERATIONS = 5;

// Observability: the Langfuse address and the project keys (Basic = base64 of "pk:sk").
// The node sandbox has no SDK of its own - we send the events to the ingestion API directly.
const LANGFUSE_HOST = 'https://your-langfuse.example.com';
const LANGFUSE_BASIC = '__LANGFUSE_BASIC__'; // replace with your own keys when publishing the code externally

// Connected nodes are obtained through the ports, not from $json.
const model = await this.getInputConnectionData('ai_languageModel', 0);
const memory = await this.getInputConnectionData('ai_memory', 0);
const rawTools = await this.getInputConnectionData('ai_tool', 0);
const tools = Array.isArray(rawTools) ? rawTools : (rawTools ? [rawTools] : []);

// Take ToolMessage from langchain if modules are allowed; otherwise a plain object with a role.
let ToolMessageCtor = null;
try {
  ToolMessageCtor = require('@langchain/core/messages').ToolMessage;
} catch (e) {
  ToolMessageCtor = null;
}

// A simple uuid for trace events - crypto may be unavailable in the sandbox.
const uid = () => 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
  const r = (Math.random() * 16) | 0;
  return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
});

// A message snapshot for the trace: role + content, without the internals of LangChain classes.
const asPlain = (m) => ({
  role: m.role ?? (m._getType ? m._getType() : 'unknown'),
  content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
  ...(Array.isArray(m.tool_calls) && m.tool_calls.length > 0
    ? { tool_calls: m.tool_calls.map((c) => ({ name: c.name, args: c.args })) }
    : {}),
});

const items = typeof $input.all === 'function' ? $input.all() : [$input.item];
const results = [];

for (const item of items) {
  const question = item.json.chatInput ?? item.json.text ?? '';
  const chatSessionId = item.json.sessionId ?? 'no-session';
  const traceStartedAt = new Date().toISOString();

  // 1. MEMORY: read the history and mix it into the prompt as an array of messages.
  let history = [];
  if (memory) {
    const mem = await memory.loadMemoryVariables({});
    const stored = mem?.chat_history ?? mem?.[memory.memoryKey];
    if (Array.isArray(stored)) history = stored;
  }

  const messages = [
    { role: 'system', content: SYSTEM_PROMPT },
    ...history,
    { role: 'user', content: question },
  ];

  // 2. TOOLS: bind them to the model and run the call loop.
  const modelWithTools = tools.length > 0 ? model.bindTools(tools) : model;
  const trace = [];
  const llmCalls = []; // for the trace: each model call with timings
  let iterations = 0;

  const callModel = async () => {
    const startTime = new Date().toISOString();
    const inputSnapshot = messages.map(asPlain);
    const resp = await modelWithTools.invoke(messages);
    llmCalls.push({
      startTime,
      endTime: new Date().toISOString(),
      input: inputSnapshot,
      output: asPlain(resp),
      usage: resp?.usage_metadata ?? resp?.response_metadata?.tokenUsage ?? null,
    });
    return resp;
  };

  let response = await callModel();

  while (
    Array.isArray(response.tool_calls) &&
    response.tool_calls.length > 0 &&
    iterations < MAX_ITERATIONS
  ) {
    iterations += 1;
    messages.push(response);

    for (const call of response.tool_calls) {
      const tool = tools.find((t) => t && t.name === call.name);
      const toolStartedAt = new Date().toISOString();
      let observation;
      if (!tool) {
        observation = 'Tool ' + call.name + ' is not connected to the node';
      } else {
        observation = await tool.invoke(call.args);
      }
      const text = typeof observation === 'string' ? observation : JSON.stringify(observation);
      trace.push({ tool: call.name, args: call.args, result: text, startTime: toolStartedAt, endTime: new Date().toISOString() });

      messages.push(
        ToolMessageCtor
          ? new ToolMessageCtor({ content: text, tool_call_id: call.id, name: call.name })
          : { role: 'tool', content: text, tool_call_id: call.id, name: call.name },
      );
    }

    response = await callModel();
  }

  const finalText = typeof response === 'string'
    ? response
    : (response?.content ?? response?.text ?? String(response));

  // 3. MEMORY: append the dialogue turn, otherwise the next turn remembers nothing.
  if (memory) {
    await memory.saveContext({ input: question }, { output: finalText });
  }

  // 4. OBSERVABILITY: assemble the run's trace and send it to Langfuse in one batch.
  // Trace - the whole run; generation - each model call; span - each tool call.
  // In code you assemble the trace yourself - this is the difference from the AI Agent node, where everything is hidden.
  let langfuseStatus = 'off';
  if (LANGFUSE_BASIC && !LANGFUSE_BASIC.startsWith('__')) {
    const traceId = uid();
    const now = () => new Date().toISOString();
    const batch = [
      {
        id: uid(), type: 'trace-create', timestamp: now(),
        body: {
          id: traceId, timestamp: traceStartedAt,
          name: 'm3-langchain-code-agent',
          sessionId: chatSessionId,
          input: question, output: finalText,
          metadata: { iterations, history_len: history.length, node: 'LangChain Code' },
        },
      },
      ...llmCalls.map((c, i) => ({
        id: uid(), type: 'generation-create', timestamp: now(),
        body: {
          id: uid(), traceId, name: 'llm-call-' + (i + 1),
          model: 'gpt-4.1-mini',
          startTime: c.startTime, endTime: c.endTime,
          input: c.input, output: c.output,
          ...(c.usage ? { usage: { input: c.usage.input_tokens ?? c.usage.promptTokens, output: c.usage.output_tokens ?? c.usage.completionTokens } } : {}),
        },
      })),
      ...trace.map((t) => ({
        id: uid(), type: 'span-create', timestamp: now(),
        body: {
          id: uid(), traceId, name: 'tool:' + t.tool,
          startTime: t.startTime, endTime: t.endTime,
          input: t.args, output: t.result,
        },
      })),
    ];
    try {
      await this.helpers.httpRequest({
        method: 'POST',
        url: LANGFUSE_HOST + '/api/public/ingestion',
        headers: { Authorization: 'Basic ' + LANGFUSE_BASIC, 'Content-Type': 'application/json' },
        body: { batch },
        json: true,
      });
      langfuseStatus = 'sent';
    } catch (e) {
      langfuseStatus = 'error: ' + String(e.message).slice(0, 120);
    }
  }

  results.push({
    json: {
      output: finalText,
      question,
      history_len: history.length,
      iterations,
      tool_calls: trace,
      tools_available: tools.map((t) => t && t.name).filter(Boolean),
      langfuse: langfuseStatus,
    },
  });
}

return results;
