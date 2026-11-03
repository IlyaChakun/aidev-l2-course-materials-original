# What to read for module 2

> Links to vendor pages and repositories were checked on **10.08.2026**. Academic papers are given
> by identifier: the arXiv address is assembled as `arxiv.org/abs/<ID>`, and if a page for some
> reason did not open, search by the identifier or by the title. Vendor addresses live their own
> lives and change without warning: if a link leads somewhere else, look for the page by the
> section title.
>
> You do not need to read the whole list. The first two sections are needed to do the homework.
> The rest are for making decisions on your own project, and are taken as needed.

---

## 1. The homework stack: Qdrant and n8n

This is the minimum without which the assignment is done blindly.

| What | Address | Why read it |
|---|---|---|
| Qdrant, local launch | `qdrant.tech/documentation/quickstart/` | One `docker run` command, ports 6333 and 6334, a volume for the data, the Web UI address. The first step of the assignment starts from this page |
| Qdrant, hybrid queries | `qdrant.tech/documentation/search/hybrid-queries/` | The module's main page. `prefetch`, `rrf` and `dbsf` fusion, **weighted RRF** (that very `weights` array, whose number of entries must match the number of branches), multi-stage queries and rescoring. It also says honestly here that no fusion method wins always and you have to choose on your own set of questions |
| Qdrant, hybrid search in practice | `qdrant.tech/documentation/search/text-search/hybrid-search/` | A ready example of a collection with a dense vector and a named sparse one for BM25, with code in five languages. Faster than assembling the schema from your head |
| Qdrant, releases | `github.com/qdrant/qdrant/releases` | Check what exactly changed in your version. The legacy endpoints `/search`, `/recommend`, `/discover` have been removed from recent versions, and this breaks any copied snippet that is two years old |
| The Qdrant Vector Store node in n8n | `docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.vectorstoreqdrant` | The node's four modes and the difference between them. The assignment requires specifically **Retrieve Documents (As Tool for AI Agent)**: the neighboring mode has a different output, and it does not connect to the agent |
| The official Qdrant node for n8n | `qdrant.tech/documentation/platforms/n8n/` · `github.com/qdrant/n8n-nodes-qdrant` | The only way to assemble a hybrid query inside n8n rather than in a script: the `queryPoints` operation accepts `prefetch`, `using` and `fusion`. Works on self-hosted and on a suitable cloud plan |
| Installing community nodes | `docs.n8n.io/integrations/community-nodes/installation/` | The installation procedure and the environment variables. Without them a community node will not connect to the agent as a tool |

## 2. Context caching (advanced level)

| What | Address | Why read it |
|---|---|---|
| Prompt caching at Anthropic | `platform.claude.com/docs/en/build-with-claude/prompt-caching` | The `cache_control` mechanics, the minimum prefix length by model, the TTL and the write price versus the read price. The fields `cache_creation_input_tokens` and `cache_read_input_tokens` are what you will put into the savings table |
| Prompt caching at OpenAI | `developers.openai.com/api/docs/guides/prompt-caching` | The 1024-token threshold, the `cached_tokens` field, explicit break points and the cache key. The case where `cached_tokens` is zero with thousands of identical tokens is described separately: the most frequent complaint |
| Cache-Augmented Generation, the original source | `arxiv.org/abs/2412.15605` | Look not at the conclusions but at the table by configuration: you can see where the approach beats retrieval and where it stops |
| audit-prompt-caching | `github.com/sernote/audit-prompt-caching` | An open skill for auditing your agent's caching: it checks prompt builders, tool schemas and logs, and finds the silent causes of a cache break (a timestamp in the system prompt, reordering of tools, switching to a fallback provider). Checked: Anthropic, Bedrock, OpenAI, OpenRouter, vLLM; scripts on the standard library. Search strictly by the full path: the repository has dozens of empty clones with almost the same name. Run it on your agent before measuring the savings |

## 3. Data preparation and parsing

| What | Address | Why read it |
|---|---|---|
| Docling | `github.com/docling-project/docling` | An open parser for PDF, DOCX, PPTX, XLSX, HTML and images, with structure and table parsing. A working starting point if the documents do not arrive in Markdown |
| Chonkie | `docs.chonkie.ai/oss/quick-start` | A chunking library with ready strategies. Useful because other people's strategies can be seen side by side and compared with your own |

## 4. Chunking

| What | Address | Why read it |
|---|---|---|
| A technical report on chunking evaluation (Chroma, 07.2024) | `research.trychroma.com/evaluating-chunking` | The first coherent methodology: evaluation at the token level, not the document level. A conclusion worth taking away: an ordinary recursive splitter with tuned parameters holds in the top group, while the default settings of popular strategies work poorly |
| The repository for the report | `github.com/brandonstarxel/chunking_evaluation` | The same method as code: it generates a question set from **your** corpus and compares strategies. A cheap way to check your chunking instead of arguing about chunk size |
| A systematic check of overlap (ECIR 2026) | `arxiv.org/abs/2601.14123` | Checks what everyone does out of habit: overlap gives no measurable recall gain, and it is justified only under strict sensitivity to boundaries. Keep it in mind when choosing between 10% and 20% |
| Chunking code by the syntax tree | `arxiv.org/abs/2605.04763` | Read in a pair with the cAST paper (EMNLP 2025 Findings): their conclusions are opposite, and this is the best reminder that a "right" chunk size does not exist outside your corpus |

## 5. Embedders

| What | Address | Why read it |
|---|---|---|
| The MTEB leaderboard | `leaderboard.mteb.org` | Look at **the slice for your language and your task**, not the average score. The average score glues together tasks that have nothing to do with yours |
| FastEmbed | `github.com/qdrant/fastembed` · `qdrant.github.io/fastembed/` | Local embeddings on ONNX without a GPU, a short path through `qdrant-client[fastembed]`. For the homework what matters is: **there is no FastEmbed node in n8n** (see `homework.md`) |
| Embeddings in Ollama | `ollama.com/blog/embedding-models` | The list of models and the call through `/api/embed`. A working replacement for a cloud embedder if there is no key or the data cannot be sent outside |

## 6. Search, fusion and reranking

| What | Address | Why read it |
|---|---|---|
| Reciprocal Rank Fusion, the original paper (SIGIR 2009) | `dl.acm.org/doi/10.1145/1571941.1572114` | Fifteen lines of formula on which all modern hybrid search stands. It is useful to see how simple a thing it is |
| Cohere Rerank, API reference | `docs.cohere.com/reference/rerank` · `docs.cohere.com/docs/rerank-overview` | The request and response contract, the document length limit, score normalization. It is worth reading separately that a score of 0.9 does not mean "twice as relevant" as 0.45 |
| Sufficient context (ICLR 2025) | `arxiv.org/abs/2411.06037` | The only careful measurement of the fact that retrieval **lowers** the model's willingness to refuse to answer. It directly explains why the assignment has two trap questions |
| A comparison of four search paradigms | `arxiv.org/abs/2508.01405` | All combinations of dense, sparse and reranking on one test bench. Useful as a map of what makes sense to try at all |
| Fusion of rewritten queries in production | `arxiv.org/abs/2603.02153` | A negative result with conditions: a technique that looks like a free improvement in papers did not pay off on live traffic |
| The illusion of coverage | `arxiv.org/abs/2605.27220` | Twenty thousand "query and scenario" pairs: how a system looks like it works as long as the questions resemble the ones it was tuned for |
| Filtered vector search (ACORN) | `arxiv.org/abs/2403.04871` | Why a metadata filter sometimes drops search quality rather than only speeding it up. Read before hanging filters on a production collection |
| pgvector | `github.com/pgvector/pgvector` | An alternative to a separate vector database if you already have Postgres. The README directly describes the index and filtering strategies |

## 7. Security

| What | Address | Why read it |
|---|---|---|
| OWASP RAG Security Cheat Sheet | `cheatsheetseries.owasp.org/cheatsheets/RAG_Security_Cheat_Sheet.html` | Fourteen sections for the whole pipeline: corpus poisoning, access-rights inheritance, chunk isolation, cache risks, fail-safe denial. A ready self-check checklist, taken whole |
| OWASP, vector and embedding weaknesses | `genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/` | A short analysis of the same with examples of incidents. Good as a text you can show a non-engineer |
| PoisonedRAG (USENIX Security 2025) | `arxiv.org/abs/2402.07867` | How many documents you need to plant in a corpus to control the answer. The answer is unpleasantly small |
| Embedding inversion (EMNLP 2023) | `arxiv.org/abs/2310.06816` | Where the rule "an embedding is a copy of the data, not a hash of it" came from. Almost all of the original text is recovered from the vectors |
| Inversion without training on the model | `arxiv.org/abs/2504.00147` | A continuation of the same line: adding noise has stopped being a defense |

## 8. Economics

| What | Address | Why read it |
|---|---|---|
| Model prices | `anthropic.com/pricing` · `openai.com/api/pricing` · `cohere.com/pricing` | The only correct source of the number on the day of the calculation. Prices move faster than any guides are updated, this one included |

A useful habit for the whole course: **take any price from the primary source on the day of the
calculation**, and in the report write the date the rate was taken for. Otherwise a month later
you cannot tell an error in the calculation from a model that has become more expensive.

## 9. Graph search (if you are wondering whether you need it)

| What | Address | Why read it |
|---|---|---|
| GraphRAG, the original paper | `arxiv.org/abs/2404.16130` | The problem statement and the questions on which a graph really wins: aggregating and multi-hop ones, not fact lookup |
| LightRAG | `github.com/HKUDS/LightRAG` | The most practical entry into the topic: you can see what the graph is assembled from and what building it costs |
| Graphiti, a temporal graph | `github.com/getzep/graphiti` · `arxiv.org/abs/2501.13956` | If the questions have a time anchor. An ordinary graph answers such questions wrongly and confidently |

General advice for this section: a graph goes in **last**, after everything has been squeezed out of
an ordinary pipeline: hybrid, a reranker, metadata, proper document preparation. Setting up a graph
takes several times more time, and the gain appears only on connected corpora.

---

## How to use this

For the homework the first two sections are enough. Everything else is a reference for a specific
decision: you are choosing an embedder, open section 5; arguing about chunk size, section 4;
about to point search at data with different access rights, section 7.

If a source has a number, look not at it but at how it was measured: on what corpus, in what way,
for what date. Three loud numbers "about the same thing" in this field usually measure three
different quantities.
