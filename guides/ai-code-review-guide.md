# AI Code Review: what works, what doesn't, and how to build a review agent

A collection of practices, numbers, pitfalls and architectural decisions for AI code review.
Compiled from the engineering blogs of companies that run review agents in production
(Uber, Cloudflare, Atlassian, Augment and others), academic benchmarks and
the experience of practitioners from professional communities. All links go to primary sources.

---

## 1. Context: why code review became the main problem of AI development

AI coding has shifted the developer's role: code is written quickly and cheaply, but it is
checked slowly and expensively. Review becomes the engineer's main activity
and the main bottleneck of the whole process:

- "The main bottleneck in development is almost always review" — [Nikolay Sheiko,
  a breakdown of AI agent practices](https://www.youtube.com/watch?v=nUT1YRvjG98).
- In teams where everyone writes with agents, PRs have ballooned to 800–1200 lines and
  arrive "on a cooldown" — [discussion](https://t.me/evilfreelancer_chat/218991).
- The lead of an AI-first team: "Writing code has become too easy, and everyone wants to merge
  their couple of thousand lines. The most typical message in the chat is 'ship the PR,
  please'" — [post](https://t.me/aostrikov_ai_agents/122) and
  [discussion](https://t.me/aostrikov_agents_chat/13315).
- An official AWS tweet: "More AI-generated code doesn't make your team faster.
  It might actually slow you down" (2.2M views) —
  [discussion context](https://t.me/aostrikov_agents_chat/18674).
- AI code shifts the load from juniors to seniors and breaks the mechanism of knowledge transfer
  through review: "Newcomers feel they have become more productive, but in
  reality the whole load falls on the experienced ones" — [Samat Galimov,
  CTO Daily](https://t.me/ctodaily/1864).

The conclusion to start a review agent project from: **the scarce resource is not the generation of
comments, but the attention of the human reviewer.** A good agent saves this
attention, a bad one burns it faster than its absence would.

---

## 2. Numbers: what production data and research say

### Production metrics of companies

| Company | Scale | Key numbers | Source |
|---|---|---|---|
| Uber (uReview) | 90%+ of ~65,000 diffs per week | 75% of comments were marked useful by engineers; 65% of comments were fixed in the same changeset, versus 51% for human comments | [Uber Engineering Blog](https://www.uber.com/us/en/blog/ureview/) |
| Atlassian (RovoDev Reviewer) | 1,900+ repositories, 54,000+ comments over a year | 38.7% of comments led to code changes; the PR cycle shrank by 30.8%; human comments became 35.6% fewer | [ICSE 2026 paper](https://arxiv.org/abs/2601.01129) |
| Anthropic (Claude Code Review) | Internal development | The share of PRs with substantive comments grew from 16% to 54%; on large PRs (1000+ lines) 84% get findings, 7.5 issues on average; <1% of findings were marked incorrect by developers; $15–25 per review | [Documentation](https://code.claude.com/docs/en/code-review), [breakdown](https://t.me/ai_product/2012) |
| Cloudflare | Tens of thousands of MRs | Up to 7 specialized reviewers + a coordinator; the system blocks merge on serious issues | [Cloudflare Blog](https://blog.cloudflare.com/ai-code-review/) |
| OpenAI (internal data) | — | 95% of engineers use Codex; active users open 70% more PRs; review shrank from 10–15 to 2–3 minutes | [breakdown](https://t.me/ai_product/8236) |

### Quality benchmarks for AI review

- **SWE-PRBench** (350 PRs with human-annotated ground truth): 8 frontier models
  find only **15–31%** of the issues flagged by humans. The most unexpected
  result: adding context **degrades** quality monotonically: a structured
  prompt of 2,000 tokens (diff + summary) beats a prompt of 2,500 tokens
  with full context on all 8 models. The mechanism is attention dilution:
  the model "drowns" in a long context — [arXiv](https://arxiv.org/abs/2603.26130).
- **Augment Code Review Bench**: the best tool has F1 53.8%, recall 62.8%,
  precision 47%. An instructive counterexample: Graphite showed precision of 75%,
  but found only 12 of 137 bugs (recall 8.8%, 0.3 comments per PR): you can
  "buy" precision with silence. Versus human reviewers: 1.03 fixed bugs
  per PR for the agent vs 0.54 for a human; meanwhile the most frequent category
  of human comments is the nitpick — [Augment
  Code](https://www.augmentcode.com/blog/how-we-built-high-quality-ai-code-review-agent).
- Related benchmarks for a deep dive: [SWR-Bench](https://arxiv.org/abs/2509.01494),
  [CR-Bench](https://arxiv.org/abs/2603.11078),
  [a comparison of models of different sizes](https://arxiv.org/abs/2606.15689) (spoiler:
  bigger is not always better), [Evaluating LLMs for Code Review](https://arxiv.org/abs/2505.20206).

### The cost of the question and the cost of error

- Data on 400 companies: teams without review write 2 times faster, but get
  2.5 times more bugs; the maximum ROI comes from the first reviewer —
  [digest](https://t.me/leadgr/2149).
- A Stanford study (100,000+ engineers, 600+ companies): AI coding gives
  +15–20% net productivity, but increases the number of bugs; the spread across types of
  projects and languages is huge — [breakdown](https://t.me/oestick/379).
- The industry's false positive rate: 5–15% depending on the codebase
  (TypeScript REST API — 3–5%, legacy Java — 6–12%). Practitioners without filtering
  report worse: consistently ~1/3 of review items are a false positive or a wrong
  priority — [analysis of the FP trap](https://tianpan.co/blog/2026-04-17-ai-code-review-at-scale-false-positive-trap).
- GitClear (211M changed lines, 2020–2024): the share of copy-paste grew
  from 8.3% to 12.3%, the share of refactoring fell from ~25% to <10%: a signal of growing
  review load and falling maintainability —
  [overview with sources](https://protsenko.dev/ai-code-review-7-limitations-i-found-in-production/).
- A public tracker of AI code incidents in production (crackr.dev/vibe-coding-failures):
  19 documented incidents, 6.3M+ affected records, 69 vulnerabilities —
  [digest](https://t.me/ctodaily/2051).

### Security of AI code (why a review agent needs a security lens)

- Veracode (100+ models tested): **45%** of AI-generated code
  contains vulnerabilities from the OWASP Top 10. Java is the worst: 72% failures. The most
  frequent vulnerability is XSS (86% of cases). Model size does not
  affect security.
- OpenAI Codex Security scanned 1.2M commits in its first cycle and found
  792 critical vulnerabilities.
- An instructive testbed: a notes app deliberately built by an AI agent
  with auth and an admin panel contained 37 vulnerabilities: SQL injection, OS command
  injection, MD5 passwords, broken access control.

---

## 3. What works: proven practices

### 3.1. Multi-level review: AI is the first line, the human is the second

The most stable pattern across all sources. AI review catches the base layer
(security anti-patterns, error handling, typical bugs, compliance with
guidelines), and the human spends attention only on the hard things: architecture, intent,
implicit invariants of the system.

- A three-level scheme: automatic review by the agent → human review (a senior
  has "implicit context built up over years" that the model lacks) → follow-up
  questions to the agent on the results of its review — [Nikolay
  Sheiko](https://www.youtube.com/watch?v=Cuk8bMt88F8).
- "AI review does not replace human review. It is the first line. The principles of review are the same
  no matter whether a human or an AI wrote the code" — [Refat
  Ametov](https://www.youtube.com/watch?v=xxHbWrlaceE).
- A case: a team built an AI reviewer that checks MRs against requirements
  and returns a verdict of OK / not OK / needs rework. The reviewer project turned out
  more successful than the AI developer on the same team: of 200+ MRs, 43% were accepted
  with minimal edits — [Oleg Zagorulko](https://www.youtube.com/watch?v=-1jQX9FlAqI).

### 3.2. The reviewer must not see the author's context

A fundamental conclusion of the ionix team: they first asked the same agent session
that wrote the code to review it, and it confidently missed critical bugs,
because it had "already decided the code was correct". The reviewer must start
from a clean context: without design discussions, without the ticket, without sunk cost.
Their prompt begins with: "You did NOT write this code and have no prior context
on it" — [ionix: We built an AI PR reviewer](https://www.ionix.io/blog/we-built-an-ai-pr-reviewer/).

An extension of the same principle is **cross-model review**: one model generated,
another checks, preferably of a different architecture.

- "It is useless to check your own work, so the opposite model is used
  as a matter of principle" — the principle of the tool
  [noodle](https://github.com/poteto/noodle) ([breakdown](https://t.me/ai_product/2010)).
- "If the code was generated in Claude Code, review through Codex, and vice versa; it is important that
  the checking models be of different architectures" —
  [community recommendation](https://t.me/neuraldeepchat/64238).
- For large PRs: a diagonal skim by eye + review by three different models,
  then only the suspicious parts are examined by hand: a stable practice
  from several independent sources.

### 3.3. Reviewing the plan before reviewing the code

- "A mistake in the plan produces hundreds of lines of bad code. One line of bad
  code is just one line" — [Cole Medin](https://www.youtube.com/watch?v=uvs1Igr4u6g).
- Teams open separate PRs for plans, tasks and code, each reviewed with its own
  prompt — [discussion](https://t.me/seniorsoftwarevlogger_chat/131804).
- Augment states the target model of AI-native review directly: **humans review
  specifications and architecture, AI reviews the implementation details** —
  [Augment Code](https://www.augmentcode.com/blog/how-we-built-high-quality-ai-code-review-agent).

### 3.4. Iterations + tests as proof

- Review in 2–3 iterations + growing the test coverage noticeably raise
  quality regardless of the model — [practice](https://t.me/vibecod3rs/39457).
- The right order: tests first (unit/e2e), then review, then fixes.
  Without a test there is no proof that the issue found was actually fixed.
  It is important to state exactly what the test checks; otherwise the model will write a test
  for the incorrect code.
- The "touch the code minimally" approach: mass edits only through tests,
  surrounding the code with checks from all sides instead of reading every line —
  [discussion of practices](https://t.me/llm_driven_products/71346).
- Be careful with the extreme of "tests instead of review": review is also the team's shared
  context, not only a search for bugs.

### 3.5. Analyze the project first, comments second

Before review, let the agent analyze the project's architecture, code style and patterns,
and only then ask for comments. This preserves consistency
and removes generic advice — [practice](https://t.me/vibecod3rs/51175).

The same conclusion in numbers: without a stored codebase context ~54%
of an AI reviewer's comments are irrelevant; with a persistent repository index
and knowledge of the conventions, ~16% —
[analysis](https://tianpan.co/blog/2026-04-17-ai-code-review-at-scale-false-positive-trap).

The agent reproduces the style of the codebase: "If it sees that the project is already crap,
it will write crap in the same style" — which is why slop must not be committed
without looking — [discussion](https://t.me/elkornacio_chat/18838).

### 3.6. The reviewer's learning loop (the main secret of long-lived agents)

A reviewer prompt written once degrades. Working teams build
a loop: human findings → agent instructions.

- Take the last 300 valuable comments from human reviewers → build from them
  a review skill for the team's specific components → keep adding new
  cases — [the experience of an AI-first team](https://t.me/aostrikov_ai_agents/122).
- The tech lead does not read every PR: about once every ~5 PRs they review one in full, and everything
  that "catches the eye" goes back into the instructions of the coding agent
  and the reviewer agent — [interview](https://www.youtube.com/watch?v=y2NnheH1-eU).
- Uber: a "Useful / Not Useful" rating on every comment, feedback tied
  to the language, category and assistant variant → targeted prompt improvements
  and switching off the failing categories — [Uber](https://www.uber.com/us/en/blog/ureview/).
- Augment: any recurring comment based on tribal knowledge
  ("we don't log fields of type X", "all API responses are backward compatible") should be
  documented in the guidelines; then it becomes a machine-readable
  constraint for the agent — [Augment Code](https://www.augmentcode.com/blog/how-we-built-high-quality-ai-code-review-agent).

### 3.7. Context: the golden mean, not the maximum

Three independent sources agree: **there should be enough context,
but not too much**.

- SWE-PRBench: full context worsens the result on all 8 models;
  a structured short prompt wins — [arXiv](https://arxiv.org/abs/2603.26130).
- Practitioners: quality review needs a reasoning model + relevant
  context; excess harms as much as too little. Pre-indexing is useful:
  call graph, type hierarchy, file structure; an example tool:
  [code-review-graph](https://github.com/tirth8205/code-review-graph).
- Production experience: overloading with instructions lowers quality: the model spends
  attention on checking against the checklist and misses problems outside it —
  [7 limitations](https://protsenko.dev/ai-code-review-7-limitations-i-found-in-production/).

### 3.8. The simplify pass

All modern models are prone to overengineering: extra abstractions, extra
constructs. A separate "simplify" review pass is an established practice; the fight
has to happen at all stages: brief, spec, plan, review —
[breakdown](https://www.youtube.com/watch?v=O3RKuenDtK4).

A related technique: add "do not praise" to the reviewer prompt; the comments
become more honest, without polite noise.

---

## 4. What does NOT work: pitfalls and limitations

### 4.1. Noise kills the agent (the main risk of the project)

The typical adoption trajectory: enthusiasm → a wave of useful findings → a slow
drift to complete ignoring. Engineers develop muscle memory
of "close without reading", and it persists even after the tool
has been fixed.

- The math: 20 comments per PR × 40% noise = 8 useless readings
  per PR; at 50 PRs a week, 400 "idle" interruptions. "Noise trains
  inattention" — [analysis of the FP trap](https://tianpan.co/blog/2026-04-17-ai-code-review-at-scale-false-positive-trap).
- A field case: after half a year the team silently resolved all 11 of the agent's comments
  without a single fix: "the tool worked, but became hollow". The cure is
  to measure the actioned-rate — [field notes](https://antigravitylab.net/en/articles/agents/ai-code-review-agent-comment-fatigue-actioned-rate-field-notes).
- ionix: more dangerous than false positives are **true but irrelevant** comments
  ("extract to a helper", "tests are missing"): they are true, so they are
  harder to argue with, and they burn attention just the same —
  [ionix](https://www.ionix.io/blog/we-built-an-ai-pr-reviewer/).
- Uber: developers consistently give low ratings to comments about
  readability, style, minor logs and micro-optimizations. High ratings go to correctness bugs,
  missing error handling and best-practice violations
  with examples — [Uber](https://www.uber.com/us/en/blog/ureview/).

### 4.2. Seven limitations from production

Two months of daily AI review of real PRs, systematized with links
to research — [Dmitry Protsenko](https://protsenko.dev/ai-code-review-7-limitations-i-found-in-production/):

1. **Unverified fixes.** A proposed patch ≠ a verified patch (in a Copilot study
   75% of generated methods did not compile).
2. **Large PRs are reviewed worse.** A small PR gets precise findings; a large one:
   the model forgets instructions, gets lazy and may leave an "LGTM" for nothing.
3. **Anchoring on the spec.** A non-obvious one: an attached detailed spec and a confident
   PR description make review worse: the model starts to trust the code ("looks
   well planned") and leans toward approval.
4. **Repeat passes are weaker.** After the first batch of comments the next
   iteration is noticeably sloppier: "the work is already done".
5. **Instruction overload.** A checklist that is too long competes with the code
   for the model's attention.
6. **Unstable rule application.** "I stated the rule once" ≠ "it
   is applied every time": even at temperature 0 the outputs are not reproducible.
7. **Missing intent.** The model does not know why the change was made and cannot
   challenge whether it makes sense: it sees only the code.

### 4.3. False findings and "confident denial"

- Consistently ~1/3 of AI review items are a false positive or a wrong priority;
  fixing everything on the agent's list = making the code worse.
- A case: a paid review found a "critical error"; when asked to fix it, it said
  "there is no error". Always validate findings before applying them.

### 4.4. Culture eats the review agent for breakfast

- Human review of AI code works only in a team with a good engineering
  culture: a senior sees signal in an LLM PR where a junior sees noise. In a bad
  culture, mandatory review makes things worse: seniors block juniors
  so as not to answer for their AI code, and a KPI on review produces formal approvals —
  [discussion](https://www.youtube.com/watch?v=Ijn0I6gWnWA).
- Responsibility is not delegated: "I need the person sending code
  for review to be responsible for every line. Let them do their part of the
  work, not be a gasket between me and the AI" —
  [discussion](https://t.me/seniorsoftwarevlogger_chat/131181).
- A rule from a company after scaling up AI coding: the first review of AI code
  is always done by the author themselves, and only then a colleague —
  [Danila Simonov](https://www.youtube.com/watch?v=BVHfDZ0kknc).

### 4.5. What the agent cannot do yet

- Architecture and "why the code exists": the agent will say that a function is long,
  but will not say that it is that way because of a contract with an external API agreed
  a year and a half ago. Uber says it directly: better at catching bugs than assessing
  system design.
- Deep human expertise: "an enormous amount of human knowledge is invested in code review,
  and it is not captured by an ordinary agent with access to the repository" — an engineer on an OpenAI infrastructure team,
  [talk](https://www.youtube.com/watch?v=z3pbrFKVyQE).
- The worst scenario, warned about by almost all sources: AI code
  that is reviewed only by AI — "a slop factory: two machines nodding at each other
  while nobody checks the assumptions".

---

## 5. How production review agents are built: an analysis of architectures

### 5.1. Uber uReview — the reference filtering pipeline

[Full breakdown](https://www.uber.com/us/en/blog/ureview/). A modular
prompt-chaining architecture of 4 stages:

1. **Ingestion / preprocessing:** filtering out low-signal files (configs,
   generated code), assembling a structured prompt with surrounding context
   (neighboring functions, class definitions, imports).
2. **Generation — specialized assistants** (pluggable): Standard (bugs,
   error handling, logic), Best Practices (company conventions from a shared
   rule registry), AppSec (vulnerabilities). Each is developed and evaluated
   independently, with its own prompts and context.
3. **Postprocessing — the key stage:** (a) a secondary prompt evaluates each
   comment and assigns a confidence score, the cutoff thresholds are configured
   at the "assistant × language × category" level; (b) a semantic filter
   merges duplicates; (c) a category classifier suppresses categories
   with historically low value.
4. **Delivery and feedback:** inline comments, a Useful/Not Useful rating,
   all the metadata goes to the analytics store.

Uber's lessons, verbatim: quality matters more than quantity; feedback must be built in;
**guardrails matter no less than prompts** ("single-step prompting is insufficient
even with strong models: the generate → grade → filter → consolidate chain
gave reliability, postprocessing turned out to matter more than prompt design").

A separate trick: the check "has the comment been fixed" is done by running the review
on the final commit **5 times**: an LLM is stochastic, a single run
misses or "resurrects" issues.

### 5.2. Cloudflare — orchestrating specialists + a coordinator

[Full breakdown](https://blog.cloudflare.com/ai-code-review/). They started like everyone:
"stuff the git diff into a prompt", and got a stream of vague advice
and hallucinated syntax errors. The final scheme:

- Up to **7 specialized reviewers** in parallel: security, performance,
  code quality, documentation, release management, compliance with the internal
  engineering code.
- A **coordinator** deduplicates findings, assesses the real severity and posts
  one structured comment (not 7 threads of noise).
- CI-native: built around an open-source agent (OpenCode) on a composable
  plugin architecture; the system can approve clean code and block
  merge on serious issues.

### 5.3. Atlassian RovoDev — quality through double-checking comments

[ICSE 2026 paper](https://arxiv.org/abs/2601.01129). Three components:
(1) zero-shot generation taking review guidelines and context into account; (2) checking
each comment for **factual correctness** (filtering out the irrelevant,
inaccurate, meaningless); (3) a check for **actionability**: will the
comment lead to an edit. The result on 1,900 repositories: 38.7% of comments
are resolved by code, PR cycle -30.8%, load on human reviewers -35.6%.

### 5.4. Augment — context decides

[Breakdown](https://www.augmentcode.com/blog/how-we-built-high-quality-ai-code-review-agent).
Diff-only review breaks on real codebases: to assess the removal of
a permission check, you need to know how authentication is built in the repo, who
interacts with the service and what implicit assumptions exist. Three pillars:
semantic search over the codebase (a context engine), the design of the agent system
(tools, prompts, models, guardrails), strict evaluation loops. Plus a cultural
rule on tribal knowledge → guidelines (see § 3.6).

### 5.5. ionix — "teach the agent to keep quiet"

[Breakdown](https://www.ionix.io/blog/we-built-an-ai-pr-reviewer/). A design
built from one constraint: comments must be so rare that a human
reads all of them.

- **Noise budget:** the agent is allowed only 2 classes of findings: exploitable
  security vulnerabilities and bugs producing incorrect behavior/a crash/data loss
  on plausible input. Only high/critical. In the prompt the "what NOT to
  report" list is longer than the "what to look for" list: style, naming, readability, tests,
  complexity, duplicates, refactoring, anything with the words "consider / might want / nit".
- The reviewer is a **different stack** with a clean context (see § 3.2).
- The agent reads its own published comments back as state: a repeat
  push becomes a cheap extra check, not a second opinion from scratch.
- On a clean PR the agent writes one sentence "all ok" and keeps quiet.

### 5.6. Four more architectures to study

- **Alibaba open-code-review** — deterministic pipelines + an agent
  with the tools code_search / file_read / file_find; built-in rules
  for bug classes (NPE, thread safety, XSS, SQL injection)
  with a four-level priority chain. Battle-tested at Alibaba scale —
  [repository](https://github.com/alibaba/open-code-review).
- **noodle (adversarial review)** — cross-model Claude ↔ Codex review;
  the number of reviewers scales with the diff size: <50 lines — Skeptic, 50–200 —
  +Architect, 200+ — +Minimalist; finding dedup, ranking by severity,
  PASS / CONTESTED / REJECT verdicts, false positive labeling —
  [repository](https://github.com/poteto/noodle).
- **A home-grown GitLab MR reviewer** — a sound separation of responsibilities:
  the worker builds the diff artifacts and metrics itself, the LLM gets only
  a prompt + schema and returns only review JSON; the sticky comment
  is tied to head_sha (does not go stale); inline comments are posted only
  at valid line positions, otherwise it is noise —
  [architecture breakdown](https://t.me/gleb_pro_ai_chat/99) (in a channel thread).
- **A multi-vendor state-machine pipeline** — task → context → plan →
  3 independent design reviewers (until zero critical findings) → implementation
  plan → 3 plan reviewers → code → 5 targeted + 2 general code reviews →
  a report to the tracker. The orchestrator is one agent, the reviewers are models of three different
  vendors — [description](https://t.me/gleb_pro_ai_chat/99).

Additionally: at Google, each language has its own fine-tuned auto-review model,
fine-tuned on style guides and past examples of good code, and teams on top
add their own product review prompts —
[talk](https://www.youtube.com/watch?v=7gujZrJ9L5I).

---

## 6. Metrics: how to tell that a review agent is useful

"Works" and "is running" are different things. A minimal set of metrics
([source 1](https://tianpan.co/blog/2026-04-17-ai-code-review-at-scale-false-positive-trap),
[source 2](https://antigravitylab.net/en/articles/agents/ai-code-review-agent-comment-fatigue-actioned-rate-field-notes)):

| Metric | What it measures | Guideline |
|---|---|---|
| **Actioned rate** (comment action rate) | % of comments that led to an edit or a substantive discussion | <40%: the agent generates more noise than signal; tune up to 55–60%+ |
| **False positive rate** | % of comments closed as wontfix / not applicable | Industry: 5–15%; count not the percentage but "how many false readings per week the team has" |
| **Comments per PR** (median) | Load on attention | 3–8 precise ones are better than 30 with eight useful |
| **Category breakdown** | Which categories of findings actually get fixed | Usually 2–3 categories give 80% of the value; the rest are candidates for switching off |
| **Impact on cycle time** | Whether the median time to merge changed | If not, the saving is eaten by sorting through noise |
| **Regression detection rate** | How often the agent flagged an issue, it was dismissed, and it reached production | A signal for calibrating trust |

Guidelines from successful rollouts: -10–20% median PR time, -40%+
production bugs in the categories the agent covers, action rate 55%+.

**The rollout playbook:** launch on 2–3 teams in non-blocking mode →
collect metrics for 6–8 weeks → tune the configuration until the action rate
exceeds ~60% → only then expand and make it mandatory. A mandate
before calibration trains the reflex of ignoring, which then cannot be cured.

---

## 7. Prompt techniques for review

- **A question about invariants.** Instead of "find bugs": "Which invariants have been broken
  or changed within this PR?" The word "invariant" primes the model to look for
  conditions that must always hold; it works even if you do not know
  where exactly the problem is.
- **The suppress list is longer than the find list.** Explicitly list what NOT to report
  (style, naming, tests, refactoring, anything with "consider"), and require
  silence on clean code (the ionix pattern).
- **A structured response format with severity.** Verdict → strengths →
  risks by P0/P1/P2 (for each: the problem, why it is a risk, where, the minimal
  fix) → checklist. Forbid "rewrite everything from scratch" and drifting into cosmetics.
- **Separate lenses.** Not one "check everything" prompt, but separate passes:
  correctness, security, performance, compliance with conventions. One call,
  one perspective (confirmed by the Uber and Cloudflare architectures).
- **Multi-pass for security.** First the code skeleton, then separate
  runs: refactoring → security → compliance with guidelines. There are
  too many rules for one context.
- **"Do not praise".** Removes polite noise, leaves the comments.
- **Sequential passing of context** (the "Turnip" technique, after the folk tale): architecture →
  code → review, each next prompt receives the results of the previous ones.
- **Verification through execution.** A review chain with running the code: execute →
  auto-fix of runtime errors → review. It protects against hallucinated imports
  and methods.

And two anti-patterns from § 4.2 that directly affect prompts: do not attach to the
reviewer a confident spec explaining why the code is right (anchoring),
and do not bloat the checklist (instruction overload).

---

## 8. Security: minimal hygiene

Three rules for AI-assisted development (community + vendor guides):

1. **Human pilot.** Treat AI code as a junior's code: review everything,
   ask the agent to explain unclear places (while explaining, it often finds
   its own bugs itself).
2. **Automated verification.** SAST (Semgrep, Snyk Code, GitHub CodeQL)
   + SCA in CI/CD and in the agent's feedback loop: just as mandatory as tests.
3. **A codified security process.** Learn the typical OWASP vulnerabilities,
   describe the security review process in text and put it into the agent's rules, so that
   it runs it before committing.

A working two-stage audit for fast projects: a SAST analyzer for the language +
a separate LLM pass with the role "senior security engineer, find all vulnerabilities".

A pattern for the agent: a security reviewer as a separate persona with a document
on what a "secure interface" means (no public mutations without auth,
no PII in logs, no SQL concatenation), plus separate reliability checks
(retry + timeout on all network code). Every PR must pass both.

---

## 9. A checklist for your own review agent

A condensed digest of the whole document: you can use it to design and check
your own solution:

1. Define a **narrow mandate**: which classes of problems the agent has the right
   to comment on. Everything else is silence. Undeclared = noise.
2. The reviewer starts **from a clean context** and preferably on a different model
   than the one that wrote the code.
3. Give the agent **codebase context** (conventions, neighboring code, dependency
   graph), but do not dump everything: a structured short context
   beats a full one.
4. Build a **pipeline, not a prompt**: generation → confidence scoring →
   filtering → deduplication → one structured output. Postprocessing
   matters more than prompt wording.
5. Rank findings by **severity** and require for each: what, where, why
   it is a risk, the minimal fix.
6. **Validate findings** before applying them (a second pass / another model /
   a human): a third may be garbage.
7. Prove every finding with a **test**: test first, then fix.
8. Do not block merge until calibrated: first a **non-blocking** mode
   and metrics.
9. Measure **actioned rate and FPR from the first week**. An action rate <40%: fix it,
   do not expand it.
10. Build in **feedback**: a rating on every comment, switching off categories
    with low value.
11. Build a **learning loop**: human findings and missed bugs → agent
    instructions.
12. Separate **lenses** for security and reliability; SAST in the pipeline.
13. Review the **plan before the code**: that is where the leverage is greatest.
14. Remember the limitations: large diffs, anchoring on the spec, weak repeat
    passes, missing intent. Design the process so that a human owns
    the final decision.
15. Responsibility for merged code is borne by the **author**, not the agent.

---

## 10. Tools to study

| Tool | What it is | Link |
|---|---|---|
| Claude Code `/code-review` | A multi-agent PR review from Anthropic | [docs](https://code.claude.com/docs/en/code-review) |
| OpenAI Codex CLI + plugin for Claude Code | Cross-model review: `/codex:review`, `/codex:adversarial-review` | [github](https://github.com/openai/codex-plugin-cc) |
| noodle | Adversarial cross-review Claude ↔ Codex | [github](https://github.com/poteto/noodle) |
| Alibaba open-code-review | A production review agent with rules for bug classes | [github](https://github.com/alibaba/open-code-review) |
| CodeRabbit CLI | Review with `--prompt-only`: the output is fed back to the agent | [integration example](https://t.me/countwithsasha/586) |
| Greptile | AI PR review, the State of AI Coding report | [greptile.com](https://www.greptile.com) |
| code-review-graph | A codebase graph for the review agent's navigation | [github](https://github.com/tirth8205/code-review-graph) |
| entireio/cli | A pre-review gate: AI approval before the human | [github](https://github.com/entireio/cli) |
| git-ai | An AI-assisted git workflow with auto-review of diffs | [github](https://github.com/git-ai-project/git-ai) |
| coddy-bot | An open-source review bot for GitHub (philosophy: the bot helps, the human answers) | [github](https://github.com/coddy-project/coddy-bot) |
| Claude Code best practices | A collection of practices, including the cross-model workflow | [anthropic.com](https://www.anthropic.com/engineering/claude-code-best-practices), [github](https://github.com/shanraisshan/claude-code-best-practice) |

---

## 11. All sources

**Engineering blogs (production experience):**

- Uber — uReview: Scalable, Trustworthy GenAI for Code Review —
  https://www.uber.com/us/en/blog/ureview/
- Cloudflare — Orchestrating AI Code Review at scale —
  https://blog.cloudflare.com/ai-code-review/
- Augment Code — How we built a high-quality AI code review agent —
  https://www.augmentcode.com/blog/how-we-built-high-quality-ai-code-review-agent
- ionix — We built an AI PR reviewer. The hard part was teaching it to say
  nothing — https://www.ionix.io/blog/we-built-an-ai-pr-reviewer/
- AI Code Review at Scale: The False Positive Trap —
  https://tianpan.co/blog/2026-04-17-ai-code-review-at-scale-false-positive-trap
- LLM Code Review in Production: Building a Diff Pipeline That Engineers
  Actually Trust — https://tianpan.co/blog/2026-05-05-llm-code-review-production-diff-pipeline
- AI Code Review: 7 Limitations I Found in Production —
  https://protsenko.dev/ai-code-review-7-limitations-i-found-in-production/
- Field Notes on Measuring Actioned-Rate —
  https://antigravitylab.net/en/articles/agents/ai-code-review-agent-comment-fatigue-actioned-rate-field-notes
- Building an AI Code Review Agent: Architecture, Patterns, and Production
  Deployment — https://niteagent.com/blog/building-ai-code-review-agent/
- Design an AI Code Review Bot — A Guided System Design —
  https://vibeengines.com/ai-system-design/code-review-bot-system-design

**Research and benchmarks:**

- SWE-PRBench (350 PRs, 8 models, 15–31% recall) — https://arxiv.org/abs/2603.26130
- RovoDev Code Reviewer at Atlassian (ICSE 2026) — https://arxiv.org/abs/2601.01129
- SWR-Bench — https://arxiv.org/abs/2509.01494
- CR-Bench: Real-World Utility of AI Code Review Agents — https://arxiv.org/abs/2603.11078
- Bigger Isn't Always Better: LLMs for Automated Code Review — https://arxiv.org/abs/2606.15689
- Evaluating Large Language Models for Code Review — https://arxiv.org/abs/2505.20206
- Deep Learning-based Code Reviews: A Paradigm Shift or a Double-Edged Sword? —
  https://arxiv.org/abs/2411.11401

**Talks and podcasts (YouTube):**

- How to prepare agents: review as a bottleneck — https://www.youtube.com/watch?v=nUT1YRvjG98
- Subagents and a virtual team (Codex CLI for review) — https://www.youtube.com/watch?v=Cuk8bMt88F8
- AI agents in the enterprise: an AI MR reviewer — https://www.youtube.com/watch?v=-1jQX9FlAqI
- Feedback-first AI coding — https://www.youtube.com/watch?v=xxHbWrlaceE
- Claude Code agent teams (plan review) — https://www.youtube.com/watch?v=uvs1Igr4u6g
- Engineering culture and AI review — https://www.youtube.com/watch?v=Ijn0I6gWnWA
- Tech lead: selective PR control and the learning loop — https://www.youtube.com/watch?v=y2NnheH1-eU
- AI agents and productivity (heads of engineering at large companies) —
  https://www.youtube.com/watch?v=UG2a6i2lHko
- Agentic engineering workflow: overengineering and simplify —
  https://www.youtube.com/watch?v=O3RKuenDtK4
- Infrastructure teams and review (the limits of automation) —
  https://www.youtube.com/watch?v=z3pbrFKVyQE
- Agents at Google/DeepMind scale — https://www.youtube.com/watch?v=7gujZrJ9L5I
- Practical cases of AI in development (the first-review rule) —
  https://www.youtube.com/watch?v=BVHfDZ0kknc

**Practitioner discussions (Telegram, public channels and chats):**

- Pains of an AI-first team: review, architecture, tasks —
  https://t.me/aostrikov_ai_agents/122 and https://t.me/aostrikov_agents_chat/13315
- AI code and knowledge transfer — https://t.me/ctodaily/1864
- A tracker of AI code incidents — https://t.me/ctodaily/2051
- Data on 400 companies — https://t.me/leadgr/2149
- The Stanford productivity study — https://t.me/oestick/379
- Anthropic Code Review: the numbers — https://t.me/ai_product/2012
- noodle / adversarial review — https://t.me/ai_product/2010
- OpenAI Codex statistics — https://t.me/ai_product/8236
- Cross-model review — https://t.me/neuraldeepchat/64238
- Reviewing plans in separate PRs — https://t.me/seniorsoftwarevlogger_chat/131804
- The author's responsibility — https://t.me/seniorsoftwarevlogger_chat/131181
- Reviewing prompts instead of code, guardrails — https://t.me/seniorsoftwarevlogger/1969
- Do not commit slop — https://t.me/elkornacio_chat/18838
- Analyzing the project before review — https://t.me/vibecod3rs/51175
- Iterations + tests — https://t.me/vibecod3rs/39457
- PR overload and pre-review gates — https://t.me/evilfreelancer_chat/218991
- Integrating CodeRabbit into the agent loop — https://t.me/countwithsasha/586
- The Codex plugin for Claude Code — https://t.me/the_ai_architect/272
- The architecture of a GitLab MR reviewer and a state-machine pipeline — https://t.me/gleb_pro_ai_chat/99
