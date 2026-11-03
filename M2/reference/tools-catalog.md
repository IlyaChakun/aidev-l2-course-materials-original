# RAG tools and frameworks · Module 2 handout · date 10.08.2026

A landscape overview as of mid-2026: orchestration frameworks, low-code platforms,
managed services, observability and evaluation, ready-made open-source platforms.

**How to use it.** This is a map of "why people pick it and where it hits limits", not a ranking. Choose by the
"where it hits limits" column: it describes the limitation you will run into in three months. Prices and project
statuses go stale within weeks, so check any figure from here against the vendor's current
page before you make a decision.

---

## 1. Orchestration frameworks

A controlled benchmark on an identical stack (one model, one embedder, one retriever) gives an
important result: **accuracy is the same for LangChain, LlamaIndex and Haystack**. Only the
overhead differs: Haystack about 5.9 ms per request, LlamaIndex about 6 ms (about 1,600 tokens),
LangChain about 10 ms and more tokens, LangGraph about 14 ms, DSPy about 3.5 ms. Conclusion: choosing
a framework by "accuracy" is pointless; you choose by the architectural task.

| Framework | Why people pick it | Where it hits limits |
|---|---|---|
| LangChain / LangGraph | The default for agentic multi-step pipelines, LangGraph 1.0 GA since autumn 2025 | The heaviest abstraction surface, higher latency and token consumption; for simple retrieval it is excess weight |
| LlamaIndex | Data-first RAG, heavy document loading, 160+ connectors, the best out-of-the-box parsing | Query engine abstractions get in the way if the bottleneck is not loading but orchestration |
| Haystack | Typed declarative pipelines, auditability, Apache 2.0 | Smaller community and fewer integrations; the 1.x→2.x transition was almost a complete rewrite |
| DSPy | Programmatic prompt optimization instead of manual tuning | Steep learning curve, production patterns are still maturing |

The criticism of heavy frameworks sounds the same from different practitioners: "it was hard to tell where
the model ends and the framework begins". The refactoring "replace the framework with direct API calls"
became a routine task in 2026. A regional survey (87 companies) shows stratification:
LangGraph leads (38%) in regulated industries where a checkpointer and replay are needed, while a **custom
stack holds 19%** precisely among fintech and teams with strong engineers.

One separate figure that explains a lot: in a survey of 1,340 practitioners, **fewer than 20% of production
RAG pipelines have automated quality evaluation**. The rest live on manual spot checks.

## 2. Low-code and visual platforms

| Tool | What it is for | Where it hits limits |
|---|---|---|
| n8n | AI as one step inside business automation: triggers, retries, 200+ business nodes | Not LLM-first: weak RAG, no built-in record manager, poor debugging of agent chains (only the logs of the last one are visible) |
| Flowise | A quick path to a RAG chatbot; Document Store combines vectorization, chunking and a record manager in one node | A complexity ceiling on multi-agent graphs; in practitioners' assessment there is no built-in reranker, which is critical; requires duplicating data (original, chunks, vectors) |
| Dify | A production LLM application: API gateway, RBAC, SSO, audit, the best built-in RAG and evaluation | Weaker outside the AI application itself, some management is Enterprise-only |
| Langflow | Production RAG: 15+ vector stores, hybrid search, reranking, export to plain Python | No broad business integrations, more backend work for SSO and RBAC |

The practitioners' position is unambiguous: **complex RAG is not built on n8n and Flowise add-ons**, only
relatively simple RAG. A typical production pattern: n8n as an outer orchestration layer (triggers,
routing, integrations) calls Flowise or Langflow over the API for the AI-heavy part. All three break
on long-lived multi-agent state, a sub-second response requirement and CI-level tests:
there teams move to code.

A recommendation that recurs among different practitioners: **prototype in a visual builder,
move critical systems to code**.

## 3. Managed services

| Service | Price | Limitation |
|---|---|---|
| AWS Bedrock Knowledge Bases | Model tokens plus vector store (OpenSearch Serverless from ~$345-700/month) plus storage, as separate line items | A black box with custom chunking and reranking; a bill of 15+ billable services is hard to forecast |
| Azure AI Search + AI Foundry | By search units and tiers; the first paid tier is noticeably more expensive than comparable full-text search | Not one product but an assembly; 16 MB per file limit |
| Vertex AI Search | $4-6 per 1,000 queries | The product is being renamed and consolidated |
| Pinecone Assistant | ~$50-500/month at MVP volume | Reviews refer to the vector database, not to the Assistant itself |
| Ragie | Free → $100/month → $500/month → Enterprise | A young vendor, the per-page metric grows with volume |
| Vectara | By some sources from $100K/year, by others a free tier with custom enterprise | No LLM of its own (only the vendor's proprietary models); pricing data conflicts |

A structural market shift worth keeping in mind: in a survey of 101 enterprise customers,
**built-in retrieval from model providers has already overtaken dedicated vector databases in actual
use** (one vendor's file search 40%, another's search 38%), even though 36% state
an intention to stay best-of-breed. Another measurement from the same series: the intention to move to hybrid
retrieval **tripled in a quarter** (10.3% → 33.3%), and the share of companies with no production RAG at all
grew from 8.6% to 22.2%.

## 4. Observability and evaluation

| Tool | What it covers | Limitation |
|---|---|---|
| Langfuse | Tracing with nested spans, LLM-as-judge, manual annotation queues, dataset regression in CI; MIT, self-host | Not a metrics framework by itself, metrics are plugged in separately |
| LangSmith | A unified view of cost across the whole workflow, calibrated judges, side-by-side comparisons | The path of least resistance only inside its own ecosystem |
| Arize Phoenix | OpenTelemetry-native, self-host, embedding space visualization, drift detection | Fewer metrics, some features in the cloud |
| RAGAS | Canonical RAG metrics plus synthetic set generation | No dashboard or production monitoring out of the box |
| DeepEval | "Pytest for LLM evaluation", 14+ metrics, native CI/CD | Cloud features are paid |
| TruLens | The "RAG triad", feedback functions for enterprise | Harder to set up, less widespread |

Consensus: **no single tool covers everything**. A mature team keeps two: one for evaluation
at the development stage, one for observability in production. A correlation from the same survey: among companies
with measurable returns, 95% use observability tools versus 52% among the rest.

## 5. Ready-made open-source platforms

| Platform | State as of 2026 | Strength | Weakness |
|---|---|---|---|
| RAGFlow | Active, about 83K stars | Layout-aware parsing of tables and figures before chunking, explainable template-based chunking | A resource-hungry full stack, a weak connector ecosystem |
| R2R | Commits continue, no tagged release since mid-2025 | An API-first backend: hybrid search with RRF, auto-graph, agentic retrieval, authorization out of the box | A slowed release cycle, a risk for a product built on it |
| Verba | **Archived in June 2026, development stopped** | Was a reference UI | Not an option for new projects |
| Onyx (formerly Danswer) | Active, MIT | 40+ connectors with permission inheritance, the only self-hosted platform with such connector breadth; deployments for 37,000+ users | It is enterprise search, not an engine for your own product |
| Kotaemon | Active, about 25K stars | A ready-made chat-with-documents, comes up in an evening, multimodal QA | Less production density (authorization, orchestration) |

A practical warning: **in this category the star count is misleading**; look at the date of the
last release and commit. Example: a project with a large number of stars quietly repositioned itself
from a ready-made solution into a library and is no longer what it is taken for.

## 6. What is advised to beginners

- Do not build from scratch: take a ready-made engine or service, hit a specific limitation,
  and only then write your own. A practitioner's estimate: DIY from scratch in code is at least a year and a half.
- Start with a visual builder to get a hands-on feel for the mechanics, and in parallel build
  a console version on a framework to understand what happens under the hood.
- "Don't solve problems you don't have yet": a typical beginner's mistake is to arrive intending
  to build graph RAG without having built a single ordinary one.

---

## A caveat on graph add-ons

Overviews and comparison tables regularly mention **LazyGraphRAG** as a cheap
alternative to classic graph RAG: the graph is built without model calls, extraction
is deferred until query time, and indexing cost is orders of magnitude lower.

**You cannot take it into a stack today.** Results have been published, not a working integration:
its inclusion in the open library is closed, with no timeline. Do not plan an architecture around it,
count on its figures in a cost estimate, or promise it to a client. If an overview
lists it alongside installable tools, that is an error in the overview, not a signal
of availability.
