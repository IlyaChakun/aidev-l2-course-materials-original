/**
 * M3 · Demo 2: a multi-step research agent on the LangChain Code node.
 *
 * How it differs from demo 1. There was a single "model -> tool -> model" loop,
 * and the model decided on the next step every time. Here the agent first
 * builds a research plan, then goes through that plan step by step, and only at the end
 * synthesizes an answer. The plan, the steps and the synthesis are written by hand, so each of them
 * is visible in the node's output and each can be stopped by its own condition.
 *
 * The ports are declared in the node's Inputs/Outputs:
 * main + ai_languageModel + ai_memory + ai_tool -> main.
 */

// ─── BLOCK 0. Loop settings and stop conditions ────────────────────────────────
// This part handles the stop conditions: without them an agent with tools
// goes into an infinite loop on the very first failed call.
const MAX_STEPS = 5;            // the maximum number of research plan steps we execute
const MAX_TOOL_ITERATIONS = 3;  // how many "model -> tools" iterations are allowed within one step
const MAX_PLAN_QUERIES = 4;     // this many sub-queries we ask the planner for
const MODEL_NAME = 'gpt-4.1-mini';

// Observability: the Langfuse address and the project keys (Basic = base64 of "pk:sk").
// The node sandbox has no SDK of its own - we send the events to the ingestion API directly.
const LANGFUSE_HOST = 'https://your-langfuse.example.com';
const LANGFUSE_BASIC = '__LANGFUSE_BASIC__'; // replace with your own keys when publishing the code externally

// ─── BLOCK 1. Ports: model, memory, tools ───────────────────────────────────
// This part handles the connected nodes. They are not visible in $json: each
// port has to be visited separately. The materials' author took the first element of the array
// (llmArray[0]); on n8n 2.23 a port with maxConnections=1 returns the object directly -
// so we handle both.
const pickOne = (v) => (Array.isArray(v) ? v[0] : v);
const model = pickOne(await this.getInputConnectionData('ai_languageModel', 0));
const memory = pickOne(await this.getInputConnectionData('ai_memory', 0));
const rawTools = await this.getInputConnectionData('ai_tool', 0);
const tools = Array.isArray(rawTools) ? rawTools : (rawTools ? [rawTools] : []);

// LangChain modules may be unavailable in the sandbox - so no require at the top,
// but a soft attempt. Without ToolMessage a plain object with role: 'tool' works,
// without JsonOutputParser we parse the planner's answer by hand.
const tryRequire = (name) => { try { return require(name); } catch (e) { return null; } };
const coreMessages = tryRequire('@langchain/core/messages');
const coreParsers = tryRequire('@langchain/core/output_parsers');
const ToolMessageCtor = coreMessages ? coreMessages.ToolMessage : null;
const JsonOutputParserCtor = coreParsers ? coreParsers.JsonOutputParser : null;

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

const textOf = (r) => (typeof r === 'string' ? r : (r?.content ?? r?.text ?? String(r)));

const items = typeof $input.all === 'function' ? $input.all() : [$input.item];
const results = [];

for (const item of items) {
  const question = item.json.chatInput ?? item.json.text ?? '';
  const chatSessionId = item.json.sessionId ?? 'no-session';
  const traceStartedAt = new Date().toISOString();

  // ─── BLOCK 2. Run state ──────────────────────────────────────────────────
  // This part handles the state: the node has no memory between steps, so
  // everything the agent has learned we accumulate ourselves in these variables, and we decide
  // which of it goes into the next model call.
  const llmCalls = [];   // each model call with timings - for the trace
  const toolTrace = [];  // each tool call - for the trace and for the output
  const findings = [];   // findings per plan step - the input for the synthesis
  const progress = [];   // the progress log; in the author's version it went to the browser console,
                         // but with a webhook launch there is no console - so it goes into the output
  let steps = 0;
  let toolIterationsTotal = 0;

  const logStatus = (percent, details) => {
    const line = `[${new Date().toISOString().slice(11, 19)}] ${percent}% - ${details}`;
    progress.push(line);
    console.log(line);
  };

  // One model call with a record in the trace. The name is needed so that in Langfuse
  // the planner can be told apart from the research steps and from the synthesis.
  const callModel = async (llm, messages, name) => {
    const startTime = new Date().toISOString();
    const inputSnapshot = messages.map(asPlain);
    const resp = await llm.invoke(messages);
    llmCalls.push({
      name,
      startTime,
      endTime: new Date().toISOString(),
      input: inputSnapshot,
      output: asPlain(resp),
      usage: resp?.usage_metadata ?? resp?.response_metadata?.tokenUsage ?? null,
    });
    return resp;
  };

  // ─── BLOCK 3. Memory: reading ────────────────────────────────────────────
  // This part handles memory. The node does not mix it in by itself: the history
  // has to be read and put into the message array by hand. contextWindowLength=2
  // means the last two "question - answer" pairs.
  let history = [];
  if (memory) {
    const mem = await memory.loadMemoryVariables({});
    const stored = mem?.chat_history ?? mem?.[memory.memoryKey];
    if (Array.isArray(stored)) history = stored;
  }

  // ─── BLOCK 4. Planning ───────────────────────────────────────────────────
  // This part handles the plan. The first model call does not answer the question
  // but decides two things: whether external sources are needed at all and into which sub-queries
  // to split the question. The needs_research flag is also a stop condition: without it
  // a research agent pulls the tools even on "hello".
  logStatus(10, 'parsing the question and building the research plan');

  const toolsBrief = tools.length
    ? tools.map((t) => `${t.name}: ${(t.description || '').slice(0, 120)}`).join('; ')
    : 'инструментов нет';

  const planSystem = [
    'Ты планировщик исследования. Отвечай только JSON, без пояснений и без markdown-обрамления.',
    'Доступные инструменты: ' + toolsBrief + '.',
    `Если вопросу нужны внешние факты - needs_research=true и от 1 до ${MAX_PLAN_QUERIES} коротких подзапросов на поиск фактов.`,
    'Арифметику в подзапросы не выноси: она считается в конце, на числах, которые найдутся. Подзапросы - только про факты.',
    'Если ответ уже есть в истории диалога, или это приветствие, или общий вопрос про то, как всё устроено - needs_research=false и search_queries=[].',
    'Формат: {"needs_research": true|false, "research_topic": "короткое название", "search_queries": ["..."], "report_sections": ["..."]}',
  ].join('\n');

  const planMessages = [
    { role: 'system', content: planSystem },
    ...history,
    { role: 'user', content: question },
  ];

  let plan = { needs_research: false, research_topic: '', search_queries: [], report_sections: [] };
  let planError = null;
  try {
    const planResp = await callModel(model, planMessages, 'plan');
    const rawPlan = textOf(planResp);
    if (JsonOutputParserCtor) {
      // The author's pattern: JsonOutputParser strips the markdown wrapping from the JSON itself.
      plan = await new JsonOutputParserCtor().parse(rawPlan);
    } else {
      const cleaned = rawPlan.replace(/```json/gi, '').replace(/```/g, '').trim();
      plan = JSON.parse(cleaned.slice(cleaned.indexOf('{'), cleaned.lastIndexOf('}') + 1));
    }
  } catch (e) {
    // Degrade softly: the plan did not parse - treat the question as a research one
    // and go in one step with the original wording.
    planError = String(e.message).slice(0, 200);
    plan = { needs_research: tools.length > 0, research_topic: question.slice(0, 60), search_queries: [question], report_sections: [] };
  }

  const queries = Array.isArray(plan.search_queries) ? plan.search_queries.slice(0, MAX_STEPS) : [];
  const needsResearch = Boolean(plan.needs_research) && queries.length > 0 && tools.length > 0;
  logStatus(20, needsResearch
    ? `plan ready: ${queries.length} sub-queries on the topic "${plan.research_topic ?? ''}"`
    : 'external sources are not needed, answering from the history and the knowledge of the model');

  // ─── BLOCK 5. Tools: one pass of "model -> tools -> model" ────────────────
  // This part handles the execution of calls. The model only asks "call
  // Wikipedia with these arguments"; finding the tool, running it and putting the
  // result back into the dialogue is the node code's job. The inner loop is bounded by
  // MAX_TOOL_ITERATIONS: without a counter the model can pull the tool endlessly.
  const modelWithTools = tools.length > 0 ? model.bindTools(tools) : model;

  const runWithTools = async (messages, label, stepNo, percent) => {
    let resp = await callModel(modelWithTools, messages, label);
    let toolIterations = 0;

    while (
      Array.isArray(resp.tool_calls) &&
      resp.tool_calls.length > 0 &&
      toolIterations < MAX_TOOL_ITERATIONS
    ) {
      toolIterations += 1;
      toolIterationsTotal += 1;
      messages.push(resp);

      for (const call of resp.tool_calls) {
        const tool = tools.find((t) => t && t.name === call.name);
        const toolStartedAt = new Date().toISOString();
        let observation;
        if (!tool) {
          observation = 'Tool ' + call.name + ' is not connected to the node';
        } else {
          try {
            observation = await tool.invoke(call.args);
          } catch (toolError) {
            observation = 'Tool ' + call.name + ' failed: ' + String(toolError.message).slice(0, 200);
          }
        }
        const text = typeof observation === 'string' ? observation : JSON.stringify(observation);
        toolTrace.push({
          step: stepNo, tool: call.name, args: call.args,
          result: text.slice(0, 1000),
          startTime: toolStartedAt, endTime: new Date().toISOString(),
        });
        logStatus(percent, `tool ${call.name} returned ${text.length} characters`);

        messages.push(
          ToolMessageCtor
            ? new ToolMessageCtor({ content: text, tool_call_id: call.id, name: call.name })
            : { role: 'tool', content: text, tool_call_id: call.id, name: call.name },
        );
      }

      resp = await callModel(modelWithTools, messages, `${label}-after-tools-${toolIterations}`);
    }

    return { resp, toolIterations };
  };

  // ─── BLOCK 6. Research loop ─────────────────────────────────────────────
  // This part handles the outer loop: the pass through the plan steps. Each step is
  // a separate dialogue with the model, the state between steps is held by the findings array.
  // A step's error is caught here so that one failed tool does not bring down the run.
  const STEP_SYSTEM = [
    'Ты исследователь. Ответь на подзапрос фактами, до пяти предложений, по-русски.',
    'Факты бери из инструмента wikipedia_search, а не из памяти модели.',
    'Запрос к инструменту формулируй коротко, названием статьи (например: Минск).',
    'Для любой арифметики вызывай calculator, сам не считай.',
    'Если инструмент ничего не нашёл, так и скажи и не выдумывай цифры.',
  ].join(' ');

  if (needsResearch) {
    for (const query of queries) {
      steps += 1;
      const percent = 20 + Math.floor((steps / queries.length) * 50);
      logStatus(percent, `step ${steps}/${queries.length}: ${query}`);

      const stepMessages = [
        { role: 'system', content: STEP_SYSTEM },
        { role: 'user', content: query },
      ];

      try {
        const { resp, toolIterations } = await runWithTools(stepMessages, `step-${steps}`, steps, percent);
        findings.push({ query, result: textOf(resp), tool_iterations: toolIterations });
      } catch (stepError) {
        // The step failed - record that as a finding and move on: the synthesis must
        // take place even on incomplete data.
        findings.push({ query, result: 'Step not completed: ' + String(stepError.message).slice(0, 200), tool_iterations: 0 });
        logStatus(percent, `step ${steps} failed: ${String(stepError.message).slice(0, 100)}`);
      }
    }
  }

  // ─── BLOCK 7. Synthesis ──────────────────────────────────────────────────
  // This part handles assembling the answer. The model sees the question a second time,
  // but now together with the findings of all steps - the collected state from block 2.
  // If no research was needed, we answer right away, with the history in context.
  logStatus(80, needsResearch ? 'combining the findings into an answer' : 'answering without tools');

  let finalText;
  if (needsResearch) {
    const findingsText = findings
      .map((f, i) => `Подзапрос ${i + 1}: ${f.query}\nНайдено: ${f.result}`)
      .join('\n\n');
    const synthesisMessages = [
      {
        role: 'system',
        content: 'Ты аналитик. Собери из находок связный ответ по-русски, до восьми предложений. Опирайся только на находки, своих фактов не добавляй. Если в вопросе есть вычисление - вызови calculator на числах из находок, сам не считай. Поиск на этом шаге уже закончен: wikipedia_search не вызывай. Если находки противоречат друг другу, скажи об этом.',
      },
      ...history,
      { role: 'user', content: `Вопрос: ${question}\n\nНаходки:\n${findingsText}` },
    ];
    // The synthesis runs with tools: the calculation depends on the numbers found,
    // and up to this point the planner did not know them - they can only be computed now.
    const { resp } = await runWithTools(synthesisMessages, 'synthesis', 'synthesis', 90);
    finalText = textOf(resp);
  } else {
    const directMessages = [
      { role: 'system', content: 'Ты демо-агент занятия. Отвечай кратко, по-русски, опираясь на историю диалога.' },
      ...history,
      { role: 'user', content: question },
    ];
    finalText = textOf(await callModel(model, directMessages, 'direct-answer'));
  }

  // The report as a document is the author's idea: the chat gets a digest, and the full text
  // with the methodology goes further along the workflow (to a file, to email, to a database).
  // In the author's version this was a second main output and the return [[...], [...]] format;
  // here there is one output, because the answer goes back to the chat, and it is also the report.
  const reportMarkdown = needsResearch
    ? [
        `# ${plan.research_topic || question}`,
        ``, `**Вопрос:** ${question}`,
        `**Шагов исследования:** ${steps}`, `**Вызовов инструментов:** ${toolTrace.length}`,
        ``, `## Ответ`, ``, finalText,
        ``, `## Методология`, ``,
        ...findings.map((f, i) => `${i + 1}. ${f.query}`),
      ].join('\n')
    : null;

  // ─── BLOCK 8. Memory: writing ────────────────────────────────────────────
  // This part makes sure the next dialogue turn remembers this one.
  // We save the digest, not the whole report: memory gets what will be needed
  // as context, not everything the agent saw.
  if (memory) {
    await memory.saveContext({ input: question }, { output: finalText });
  }

  // ─── BLOCK 9. Observability ──────────────────────────────────────────────
  // This part handles the run's trace in Langfuse: trace - the whole run,
  // generation - each model call, span - each tool call.
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
          name: 'm3-research-agent',
          sessionId: chatSessionId,
          input: question, output: finalText,
          metadata: {
            needs_research: needsResearch,
            steps, tool_iterations: toolIterationsTotal,
            history_len: history.length,
            research_topic: plan.research_topic ?? null,
            node: 'LangChain Code',
          },
        },
      },
      ...llmCalls.map((c) => ({
        id: uid(), type: 'generation-create', timestamp: now(),
        body: {
          id: uid(), traceId, name: c.name,
          model: MODEL_NAME,
          startTime: c.startTime, endTime: c.endTime,
          input: c.input, output: c.output,
          ...(c.usage ? { usage: { input: c.usage.input_tokens ?? c.usage.promptTokens, output: c.usage.output_tokens ?? c.usage.completionTokens } } : {}),
        },
      })),
      ...toolTrace.map((t) => ({
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

  logStatus(100, `done: ${steps} steps, ${toolTrace.length} tool calls, ${llmCalls.length} model calls`);

  // ─── BLOCK 10. Output ────────────────────────────────────────────────────
  // This part handles diagnostics. Everything that lives inside in the AI Agent node
  // is returned outward here: how many steps there were, what was asked of the tools,
  // how many messages came from memory, whether the trace went out.
  results.push({
    json: {
      output: finalText,
      question,
      needs_research: needsResearch,
      research_topic: plan.research_topic ?? null,
      plan_queries: queries,
      plan_error: planError,
      iterations: steps,
      tool_iterations: toolIterationsTotal,
      llm_calls: llmCalls.length,
      tool_calls: toolTrace,
      findings,
      history_len: history.length,
      tools_available: tools.map((t) => t && t.name).filter(Boolean),
      modules: { tool_message: Boolean(ToolMessageCtor), json_parser: Boolean(JsonOutputParserCtor) },
      report_markdown: reportMarkdown,
      progress,
      langfuse: langfuseStatus,
    },
  });
}

return results;
