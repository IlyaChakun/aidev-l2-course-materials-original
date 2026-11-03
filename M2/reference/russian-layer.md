# RAG in Russian · Module 2 handout · date 10.08.2026

What changes when the corpus is in Russian: choosing an embedder and a reranker, model prefixes,
cross-lingual search, and working stacks from practice.

**How to use it.** This section is about corrections to the general scheme, not a separate architecture: everything
else (hybrid, metadata, evaluation) works the same way. Model names and benchmark figures
are a starting point for a shortlist, not a ready choice: the final decision is always by measurement
on your own data.

---

## 1. The main mistake

There is one, and it keeps repeating: **an English-language embedding model on Russian documents**.
A typical picture from consulting practice: a team comes in, you look at the embedder, and it is the cheapest
option with no Russian support. Encoding is bad, retrieval is too, and it is diagnosed
simply by what the database returns for a meaningful query.

Second in frequency: **forgotten prefixes**. Models of the e5 family and FRIDA were trained with the prefixes
`query:` and `passage:`, and without them quality drops silently. The rule: read the model card
and follow it literally.

## 2. Model reference points

The ruMTEB benchmark (23 tasks, 7 categories) has been the starting point since 2024. On the retrieval slice specifically,
among non-instruction models the leaders are **bge-m3** (567M, retrieval 74.79, average 61.58)
and **multilingual-e5-large** (560M, retrieval 74.04, average 61.41). The `ru-en-RoSBERTa` model (404M)
is higher on the overall average (61.77) but weaker specifically on retrieval (66.52).

Newer contenders whose **dates and claims conflict**, so both figures come from
the developers and there is no direct comparison between them:

- **FRIDA** (an encoder based on FRED-T5, about 823M): claimed first place on the leaderboard, over
  70 points. There is a GGUF-quantized build for CPU inference.
- **GigaEmbeddings**: claims an average of 69.1.

Two more useful details:

- **USER-bge-m3** (359M, bge-m3 trimmed to a Russian and English vocabulary) beats the base
  bge-m3 on the overall average (0.706 vs 0.689) but loses on retrieval (0.934 vs 0.945).
- The **RusBEIR** benchmark (17 datasets) gives a sobering picture: on long documents **BM25
  remains a strong baseline** and beats neural models by 13-27 percentage points,
  because those are limited by context length. The best combination there: bge-m3 plus bge-reranker-v2-m3.

An independent applied measurement on a narrow legal corpus (858 acts, 30 questions, a small sample)
put OpenAI text-embedding-3-large, Voyage voyage-3 and the local deepvk/USER2-base in the top group with no significant difference.
The disagreement with ruMTEB: there bge-m3 and e5 are on top, but in this measurement
they were simply not tested.

## 3. Rerankers for Russian

- **bge-reranker-v2-m3** (568M, context 8192): the de facto industry standard, appears
  as a baseline in all measurements found.
- **jina-reranker-v2-base-multilingual** (278M): according to the developer, better on cross-lingual
  sets and noticeably faster, but loses on English-language BEIR.
- An applied measurement on a Russian legal corpus: **jina-reranker-v3**
  and **bge-reranker-v2-m3** turned out to work, while `mxbai-rerank-base-v2` significantly **worsened** the result,
  and an English-language cross-encoder on Russian is neutral or slightly harmful.
- An important observation from the same source: **the reranker's effect is inversely proportional to the strength of the embedder**.
  On top embeddings the gain is within the margin of error; on weak ones it gives +9-12 nDCG points.

Warning: the web has comparison pages with obviously broken metrics (ELO 1327 vs 327
at almost equal nDCG) and mentions of models with no independent confirmation. Do not carry
such figures into decisions.

## 4. Cross-lingual search

The main source of error is not that the query and the document are in different languages, but **ranking bias
between documents**: the retriever prefers documents in the query's language or in
English regardless of relevance. On an enterprise benchmark the losses reach 40%.

What helps (confirmed by experiment):

- **Balanced retrieval**: take an equal number of documents from each language, for example 10 plus 10
  from the top 20.
- **Query translation** and merging the two ranked lists.
- **Query-Synergy**: add the query's English translation to the query and merge the similarity scores
  of both versions without translating documents, a training-free method.

A separate problem at generation: the model slides into English with a mixed-language context,
especially in reasoning. This is not a failure to understand but a decoder bias toward frequent English tokens,
and it is cured by a penalty on non-target tokens at the decoding level.

A practical requirement: **compute metrics separately per language from day one**. An aggregate
masks the degradation of a specific language.

## 5. Working stacks from practice

- Fully local: pgvector plus `deepvk/USER-bge-m3` (1024 dimensions, Russian-tuned) plus
  Ollama for indexing, wrapped in an MCP server. The volume limit for pgvector depends on tuning
  and extensions: real installations run on tens of millions of vectors.
- Classic: bge-m3 or FRIDA with prefixes, the bge-reranker-v2-m3 reranker, generation on
  T-lite (a fine-tuned Qwen 2.5 7B) or RuadaptQwen.
- By generative model size: at the start and with small volumes 7-8B is enough; for RAG with a large
  context 8B is no longer suitable, the guideline is 32B, or a 70B and 8B pair with speculative decoding.
- A useful observation: **prompts for RAG over Russian documents are often better written
  in English**, since models are trained predominantly on English.
- A known problem unfixed for years: one popular desktop application for
  local models searches poorly over Russian fragments.
