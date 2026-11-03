/**
 * M3 · Demo 3: an orchestrator -> three workers in parallel -> a synthesizer.
 * The orchestrator-workers pattern from Anthropic's article on effective agents,
 * assembled entirely inside ONE LangChain Code node.
 *
 * Five model calls per run: one planning, three executing (simultaneously) and one stitching.
 * The ports are declared in the node's Inputs/Outputs: main + ai_languageModel (two model nodes) + ai_memory -> 2 x main.
 *
 * DEVIATION FROM THE AUTHOR'S ORIGINAL. In the author's version the orchestrator and the synthesizer run on Claude, the workers on GPT.
 * The demo stand has one working LLM credential (OpenAI), so ALL five calls go to gpt-4.1-mini,
 * and the roles are separated by prompts and temperature. In production the orchestrator is usually set stronger than the workers:
 * it decides what to do at all, and its mistake costs all three subsequent calls.
 */

const LANGFUSE_HOST = 'https://your-langfuse.example.com';
const LANGFUSE_BASIC = '__LANGFUSE_BASIC__'; // Basic = base64 of "pk:sk"; substitute your own keys when publishing externally
const SUBTASK_COUNT = 3;

// ─────────────────────────────────────────────────────────────────────────────
// 1. PORTS. This part handles where the model and memory come from.
// Connected nodes are obtained by calling the port, not from $json: $json carries only the payload.
// TWO model nodes are connected to the ai_languageModel port, so the port returns an array, not a single object.
// ─────────────────────────────────────────────────────────────────────────────
const lmPort = await this.getInputConnectionData('ai_languageModel', 0);
const models = Array.isArray(lmPort) ? lmPort.filter(Boolean) : (lmPort ? [lmPort] : []);
if (models.length === 0) {
  throw new Error('The ai_languageModel port is empty: connect at least one model node to the node');
}
const memory = await this.getInputConnectionData('ai_memory', 0);

// Roles are separated by temperature, not by position in the array: the order depends on the order of connections
// and silently changes as soon as a connection is re-plugged. The cold model plans and stitches, the warm one writes.
const byTemp = [...models].sort((a, b) => (a?.temperature ?? 1) - (b?.temperature ?? 1));
const plannerModel = byTemp[0];
const workerModel = byTemp[byTemp.length - 1];
const modelsInfo = models.map((m) => ({
  model: m?.modelName ?? m?.model ?? 'unknown',
  temperature: m?.temperature ?? null,
}));

// A check of the node sandbox: in the author's version the code relies on require('@langchain/core/...').
// These modules are not needed here, but it is useful to see the status in the run diagnostics.
let requireProbe;
try {
  require('@langchain/core/prompts');
  requireProbe = 'ok';
} catch (e) {
  requireProbe = 'unavailable: ' + String(e.message).slice(0, 80);
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. UTILITIES. Event identifiers, message snapshots and parsing of the model's answer.
// ─────────────────────────────────────────────────────────────────────────────
const uid = () => 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
  const r = (Math.random() * 16) | 0;
  return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
});

const asPlain = (m) => ({
  role: m.role ?? (m._getType ? m._getType() : 'unknown'),
  content: typeof m.content === 'string' ? m.content : JSON.stringify(m.content),
});

// The model likes to wrap JSON in triple quotes or to precede it with a phrase.
// We take the piece from the first opening to the last closing brace - that is enough.
const parseJsonLoose = (raw) => {
  const text = String(raw ?? '');
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start < 0 || end <= start) return null;
  try {
    return JSON.parse(text.slice(start, end + 1));
  } catch (e) {
    return null;
  }
};

const items = typeof $input.all === 'function' ? $input.all() : [$input.item];
const chatOut = [];
const draftsOut = [];

for (const item of items) {
  const question = item.json.chatInput ?? item.json.text ?? '';
  const chatSessionId = item.json.sessionId ?? 'no-session';
  const traceStartedAt = new Date().toISOString();
  const runStartedMs = Date.now();

  // ───────────────────────────────────────────────────────────────────────────
  // 3. MEMORY (reading). This part handles the state between dialogue turns.
  // Without it the second turn does not understand what "shorten this" means: the node has no memory of its own,
  // all the state lives in the connected memory node and is mixed into the prompt by hand.
  // ───────────────────────────────────────────────────────────────────────────
  let history = [];
  if (memory) {
    const mem = await memory.loadMemoryVariables({});
    const stored = mem?.chat_history ?? mem?.[memory.memoryKey];
    if (Array.isArray(stored)) history = stored;
  }
  const historyText = history.map((m) => asPlain(m).role + ': ' + asPlain(m).content).join('\n');

  // ───────────────────────────────────────────────────────────────────────────
  // 4. CALL LOG. Each model call is written here with timings:
  // the trace is later assembled from this log, and it shows that the workers ran simultaneously.
  // ───────────────────────────────────────────────────────────────────────────
  const llmCalls = [];
  const callLLM = async (name, model, messages) => {
    const startTime = new Date().toISOString();
    const t0 = Date.now();
    const resp = await model.invoke(messages);
    const text = typeof resp === 'string' ? resp : (resp?.content ?? resp?.text ?? String(resp));
    llmCalls.push({
      name,
      startTime,
      endTime: new Date().toISOString(),
      ms: Date.now() - t0,
      offset_ms: t0 - runStartedMs, // offset from the run start: it is the same for the three workers
      input: messages.map(asPlain),
      output: text,
      usage: resp?.usage_metadata ?? resp?.response_metadata?.tokenUsage ?? null,
    });
    return text;
  };

  // ───────────────────────────────────────────────────────────────────────────
  // 5. ORCHESTRATION. This part handles splitting the work into subtasks.
  // The subtasks are NOT hardcoded: the model comes up with them for the specific request and returns JSON.
  // That is the difference from an ordinary chain - the composition of the work is determined at run time, not at build time.
  // ───────────────────────────────────────────────────────────────────────────
  const orchestratorMessages = [
    {
      role: 'system',
      content: 'Ты оркестратор. Ты НЕ пишешь документ сам. Ты делишь работу ровно на ' + SUBTASK_COUNT +
        ' независимые подзадачи, которые можно выполнить одновременно, не заглядывая в результат соседа. ' +
        'Верни ТОЛЬКО JSON вида {"topic":"...","subtasks":[{"id":"w1","role":"краткая роль","goal":"что на выходе","instruction":"что именно сделать, 1-2 предложения"}]}. ' +
        'Ровно ' + SUBTASK_COUNT + ' элементов в subtasks. Подзадачи не должны пересекаться по содержанию. Пиши по-русски.',
    },
    ...(historyText ? [{ role: 'user', content: 'Предыдущий ход диалога:\n' + historyText }] : []),
    { role: 'user', content: 'Запрос пользователя: ' + question },
  ];

  const planRaw = await callLLM('orchestrator', plannerModel, orchestratorMessages);
  let plan = parseJsonLoose(planRaw);
  let planFallback = false;

  // Degradation without failure: if the orchestrator returned non-JSON, the work is still split into three parts.
  if (!plan || !Array.isArray(plan.subtasks) || plan.subtasks.length === 0) {
    planFallback = true;
    plan = {
      topic: question,
      subtasks: [
        { id: 'w1', role: 'фактура', goal: 'основные факты по запросу', instruction: 'Собери основные факты и контекст по запросу.' },
        { id: 'w2', role: 'за', goal: 'аргументы за', instruction: 'Сформулируй сильные стороны и аргументы за.' },
        { id: 'w3', role: 'против', goal: 'аргументы против', instruction: 'Сформулируй риски, ограничения и аргументы против.' },
      ],
    };
  }
  const subtasks = plan.subtasks.slice(0, SUBTASK_COUNT);

  // ───────────────────────────────────────────────────────────────────────────
  // 6. PARALLELISM. The crux of the example: three workers go to work SIMULTANEOUSLY.
  // Promise.all starts all three calls at once and waits for the last one, so three calls
  // of ~8 seconds take ~8 seconds, not 24. Each worker has exactly one model call:
  // there are no loops inside, the stop condition is trivial - the call returned.
  // ───────────────────────────────────────────────────────────────────────────
  const workersStartedMs = Date.now();
  const workerTexts = await Promise.all(subtasks.map((task, i) => callLLM(
    'worker-' + (i + 1) + ':' + (task.id ?? 'w' + (i + 1)),
    workerModel,
    [
      {
        role: 'system',
        content: 'Ты воркер в команде из ' + SUBTASK_COUNT + ' исполнителей. Твоя роль: ' + (task.role ?? 'исполнитель') + '. ' +
          'Делай ТОЛЬКО свою часть, не пересказывай чужие. Ответ по-русски, до 200 слов, тезисами, без вступлений.',
      },
      {
        role: 'user',
        content: 'Общий запрос: ' + question + '\nТвоя подзадача: ' + (task.instruction ?? task.goal ?? '') +
          '\nЧто должно получиться: ' + (task.goal ?? 'полезный фрагмент документа'),
      },
    ],
  )));
  const workersWallMs = Date.now() - workersStartedMs;

  const workerDrafts = subtasks.map((task, i) => ({
    id: task.id ?? 'w' + (i + 1),
    role: task.role ?? 'исполнитель',
    goal: task.goal ?? '',
    instruction: task.instruction ?? '',
    draft: workerTexts[i],
  }));

  // ───────────────────────────────────────────────────────────────────────────
  // 7. SYNTHESIS. This part handles stitching three drafts into one document.
  // The synthesizer sees all the drafts at once and the dialogue history - which is why "shorten this"
  // works on the second turn: "this" lies in memory, not in the request text.
  // ───────────────────────────────────────────────────────────────────────────
  const synthesizerMessages = [
    {
      role: 'system',
      content: 'Ты синтезатор. На входе - черновики нескольких исполнителей по одному запросу. ' +
        'Собери из них ОДИН связный документ на русском: короткий заголовок, затем разделы. ' +
        'Убери повторы между черновиками, противоречия покажи явно. Ничего не выдумывай сверх черновиков.',
    },
    ...(historyText ? [{ role: 'user', content: 'Предыдущий ход диалога:\n' + historyText }] : []),
    {
      role: 'user',
      content: 'Запрос пользователя: ' + question + '\n\nЧерновики исполнителей:\n' +
        workerDrafts.map((d) => '### ' + d.role + '\n' + d.draft).join('\n\n'),
    },
  ];
  const finalText = await callLLM('synthesizer', plannerModel, synthesizerMessages);

  // ───────────────────────────────────────────────────────────────────────────
  // 8. MEMORY (writing). We save the request and the result. We do not put the workers' drafts into memory:
  // that is intermediate run state, not dialogue state, and it would only clog the window.
  // ───────────────────────────────────────────────────────────────────────────
  if (memory) {
    await memory.saveContext({ input: question }, { output: finalText });
  }

  // ───────────────────────────────────────────────────────────────────────────
  // 9. PARALLELISM DIAGNOSTICS. The sum of the workers' times against the wall-clock time:
  // if the sum is noticeably greater than the wall clock, the calls really did overlap.
  // ───────────────────────────────────────────────────────────────────────────
  const workerCalls = llmCalls.filter((c) => c.name.startsWith('worker-'));
  const workersSumMs = workerCalls.reduce((acc, c) => acc + c.ms, 0);
  const timings = {
    total_ms: Date.now() - runStartedMs,
    orchestrator_ms: llmCalls.find((c) => c.name === 'orchestrator')?.ms ?? null,
    workers_wall_ms: workersWallMs,
    workers_sum_ms: workersSumMs,
    workers_speedup: workersWallMs > 0 ? Number((workersSumMs / workersWallMs).toFixed(2)) : null,
    workers_parallel: workersWallMs < workersSumMs * 0.8,
    synthesizer_ms: llmCalls.find((c) => c.name === 'synthesizer')?.ms ?? null,
    per_call: llmCalls.map((c) => ({ name: c.name, ms: c.ms, offset_ms: c.offset_ms })),
  };

  // ───────────────────────────────────────────────────────────────────────────
  // 10. OBSERVABILITY. The run's trace goes to Langfuse in one batch.
  // trace - the whole run, generation - each of the five model calls with its own start and end.
  // The node sandbox has no SDK of its own and fetch is unavailable, so we send to the ingestion API
  // via this.helpers.httpRequest. In the trace the three workers overlap in time -
  // that is the visual proof of parallelism.
  // ───────────────────────────────────────────────────────────────────────────
  let langfuseStatus = 'off';
  if (LANGFUSE_BASIC && !LANGFUSE_BASIC.startsWith('__')) {
    const traceId = uid();
    const now = () => new Date().toISOString();
    const batch = [
      {
        id: uid(), type: 'trace-create', timestamp: now(),
        body: {
          id: traceId, timestamp: traceStartedAt,
          name: 'm3-orchestrator-agent',
          sessionId: chatSessionId,
          input: question, output: finalText,
          metadata: {
            node: 'LangChain Code',
            pattern: 'orchestrator-workers',
            subtasks: subtasks.length,
            plan_fallback: planFallback,
            history_len: history.length,
            models: modelsInfo,
            timings,
          },
        },
      },
      ...llmCalls.map((c) => ({
        id: uid(), type: 'generation-create', timestamp: now(),
        body: {
          id: uid(), traceId, name: c.name,
          model: 'gpt-4.1-mini',
          startTime: c.startTime, endTime: c.endTime,
          input: c.input, output: c.output,
          ...(c.usage ? { usage: { input: c.usage.input_tokens ?? c.usage.promptTokens, output: c.usage.output_tokens ?? c.usage.completionTokens } } : {}),
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

  const diagnostics = {
    plan_topic: plan.topic ?? question,
    plan_fallback: planFallback,
    subtasks: subtasks.map((t, i) => ({ id: t.id ?? 'w' + (i + 1), role: t.role ?? '', goal: t.goal ?? '' })),
    llm_calls: llmCalls.length,
    models_connected: modelsInfo,
    planner_temperature: plannerModel?.temperature ?? null,
    worker_temperature: workerModel?.temperature ?? null,
    history_len: history.length,
    langchain_require: requireProbe,
    langfuse: langfuseStatus,
    timings,
  };

  // OUTPUT 1 (main) - the result for the chat. OUTPUT 2 (main) - the workers' drafts, for a file or an archive.
  chatOut.push({ json: { output: finalText, question, sessionId: chatSessionId, diagnostics } });
  draftsOut.push({ json: { type: 'worker_drafts', question, sessionId: chatSessionId, plan_topic: plan.topic ?? question, drafts: workerDrafts, timings } });
}

return [chatOut, draftsOut];
