# M2 · Context, search, RAG and CAG: lecture materials

The slides and the live demos from the M2 lecture session. The homework text is in [`../M2/`](../M2/README.md); start the homework from [`../M2/homework.md`](../M2/homework.md).

## What is here

| Path | What it is |
|---|---|
| [`slides/m2-lecture-context-search-rag-cag.html`](slides/m2-lecture-context-search-rag-cag.html) | **M2 lecture** deck: context, search, vectors, hybrid, RAG, CAG, production. Opens in a browser with a double click; the Appendix button holds the worked examples |
| [`slides/m2-reingest-explorer.html`](slides/m2-reingest-explorer.html) | An interactive page linked from the deck: what happens to points in Qdrant when a document is re-ingested |
| [`demo/01-embeddings/`](demo/01-embeddings/README.md) | **Lab 01**: embeddings from scratch, BM25 vs dense, chunking, filling Qdrant, hybrid search, re-ingestion, recall@5 and NDCG@5 on the golden set, the answer step |
| [`demo/02-vector-db-internals/`](demo/02-vector-db-internals/README.md) | **Lab 02**: inside a vector DB on 50,000 DBpedia articles: brute force vs HNSW, HNSW settings, quantization, filters, sizing |
| [`demo/03-pgvector-vs-qdrant/`](demo/03-pgvector-vs-qdrant/README.md) | **Lab 03**: the same search in PostgreSQL + pgvector and in Qdrant |
| [`demo/04-multitenancy/`](demo/04-multitenancy/README.md) | **Lab 04**: multi-tenancy: how to isolate customers in one collection and how it breaks |
| [`demo/05-n8n-rag/`](demo/05-n8n-rag/README.md) | **Lab 05**: end-to-end RAG in n8n without code: ingestion workflow, an agent with Qdrant as a tool, the golden set through the agent |
| [`demo/_shared/`](demo/_shared/) | The Lumen support corpus and the golden set shared by the labs |

## Running the demos

Every lab has its own `README.md` and `RUNBOOK.md` (step by step, with the expected output) and runs with `make`. Start from Lab 01:

```bash
cd demo/01-embeddings
make help
```

Commands in the deck and the runbooks start from the repository root: `cd M2-Ilya/demo/<lab>`.

Keys go into `.env` files only (copy `.env.example`). They are in `.gitignore`: never commit them and never paste them into a chat.
