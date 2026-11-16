"""Step 11. Another embedding model: the model is a choice, and the collection is bound to it.

The same corpus and golden set with Ollama bge-m3 and FastEmbed bge-small next to OpenAI. Vectors come from the cache
filled by `make warm`, so the step runs without Ollama or FastEmbed afterwards. DEMO_EXPLAIN=1 adds the notes.
"""
import httpx
import numpy as np
from rich.syntax import Syntax
from rich.table import Table

from lib import (COLLECTION, EMBED_DIM, EMBED_MODEL, OTHER_MODELS, QDRANT_URL, STEP11_PHRASE, ModelUnavailable,
                 cache_note, check_collection, chunk_corpus, collection_body, console, embed, embed_other, explain,
                 header, load_corpus, load_golden, ndcg_at, qdrant, recall_at, search, search_body, short_json,
                 sources_of, to_points)

header("Step 11. Another embedding model",
       f"The default everywhere is {EMBED_MODEL} ({EMBED_DIM} numbers). Here the same corpus goes through two local "
       "models the homework allows, each into its own collection.")
check_collection()

chunks = chunk_corpus(load_corpus())
golden = [q for q in load_golden() if q["kind"] != "trap"]
texts = [c.text for c in chunks] + [q["question"] for q in golden] + [STEP11_PHRASE]

# Vectors of every model for every text: OpenAI from step 5's cache, the others from their own caches.
models = {EMBED_MODEL: (EMBED_DIM, "OpenAI API", embed(texts))}
for name, (model_id, dim, where) in OTHER_MODELS.items():
    try:
        models[model_id] = (dim, where, embed_other(name, texts))
    except ModelUnavailable as e:
        console.print(f"[yellow]Skipped {model_id}: {e}[/yellow]")
n_chunks, n_q = len(chunks), len(golden)


def collection_of(model: str) -> str:
    return COLLECTION if model == EMBED_MODEL else f"{COLLECTION}_{model.split('/')[-1].replace('.', '-')}"


# 11.1 The same question, three models
answer_i = next(i for i, c in enumerate(chunks) if c.label == "account-and-login > Forgot password")
other_i = next(i for i, c in enumerate(chunks) if c.source == "plans-and-pricing.md")
console.print(f"[bold]11.1 One question, three models[/bold]: \"{STEP11_PHRASE}\"")
t = Table(title="What each model returns, and how close the question is to two chunks")
t.add_column("model")
t.add_column("runs")
t.add_column("length", justify="right")
t.add_column("first 4 numbers")
t.add_column(f"cos → {chunks[answer_i].label}", justify="right")
t.add_column(f"cos → {chunks[other_i].label}", justify="right")
cosines = {}
for model, (dim, where, vecs) in models.items():
    q = vecs[-1]
    ca, co = float(q @ vecs[answer_i]), float(q @ vecs[other_i])
    cosines[model] = (ca, co)
    t.add_row(model, where, str(len(q)), " ".join(f"{x:+.3f}" for x in q[:4]), f"{ca:.3f}", f"{co:.3f}")
console.print(t)
console.print("Different lengths, different numbers, different cosine scales; the order (answer chunk closer) is "
              "what carries over.\n", style="dim")
spread = {m: c[0] - c[1] for m, c in cosines.items()}
explain([
    "Every model maps text to its own space: the vector length is set by the model (1536, 1024, 384), and number i of "
    "one model has nothing to do with number i of another.",
    "Cosine scales differ too: " + "; ".join(f"{m} gives {c[0]:.3f} vs {c[1]:.3f}" for m, c in cosines.items())
    + ". A threshold like 'cosine above 0.5' means something else for every model; only the order within one model "
    "is comparable.",
    "All three put the answer chunk closer than the unrelated one; the gap is "
    + ", ".join(f"{g:+.3f} ({m})" for m, g in spread.items()) + ".",
])

# 11.2 A question embedded by one model cannot search a collection built by another
other_model = next((m for m in models if m != EMBED_MODEL), None)
if other_model:
    body = search_body("dense", STEP11_PHRASE, models[other_model][2][-1].tolist(), limit=5)
    console.print(f"[bold]11.2 Wrong model[/bold]: the question embedded by {other_model} sent to \"{COLLECTION}\" "
                  f"(built by {EMBED_MODEL})  [cyan]POST /collections/{COLLECTION}/points/query[/cyan]")
    console.print(Syntax(short_json(body, max_floats=4), "json", theme="ansi_dark", word_wrap=True))
    r = httpx.post(f"{QDRANT_URL}/collections/{COLLECTION}/points/query", json=body, timeout=30)
    console.print(f"[red]response {r.status_code}[/red] {r.json().get('status', {}).get('error', r.text)[:160]}\n")
    explain([
        f"Different sizes ({models[other_model][0]} against {EMBED_DIM}) are the lucky case: Qdrant refuses with an error.",
        "The dangerous case is two models with the same size (for example text-embedding-3-large shortened to 1536): "
        "no error, five results, all meaningless. That is why the model name sits in the collection metadata and "
        "steps 6-11 check it before searching (the line 'Collection check' at the top).",
        "Changing the model means a new collection and re-embedding every chunk, and the questions must go through the "
        "same model at search time: in the homework, the same model in ingestion and in the n8n Embeddings node.",
    ])

# 11.3 One collection per model, same schema, same chunks
console.print("[bold]11.3 One collection per model[/bold] (schema of step 5, size and metadata from the model)")
for model, (dim, _, vecs) in models.items():
    if model == EMBED_MODEL:
        continue
    name = collection_of(model)
    qdrant("DELETE", f"/collections/{name}")
    qdrant("PUT", f"/collections/{name}", collection_body("h2-400tok", model=model, size=dim))
    points = to_points(chunks, vecs[:n_chunks])
    for i in range(0, len(points), 64):
        qdrant("PUT", f"/collections/{name}/points?wait=true", {"points": points[i:i + 64]})
    check_collection(name, model=model, size=dim)
console.print()

# 11.4 The models on the golden set: dense alone shows the model, hybrid shows what the user gets
t = Table(title="The models on the golden set (dense = the model alone, hybrid = with bm25 and RRF)")
for col in ("model", "dims", "147 vectors", "search", "core r@5", "core NDCG@5", "multi r@5", "multi r@10", "multi NDCG@5"):
    t.add_column(col, justify="left" if col in ("model", "search") else "right")
scores = {}
for model, (dim, _, vecs) in models.items():
    for mode in ("dense", "hybrid"):
        runs = {q["id"]: sources_of(search(mode, q["question"], vecs[n_chunks + i].tolist(),
                                           collection=collection_of(model)))
                for i, q in enumerate(golden)}

        def avg(fn, kind, k):
            qs = [q for q in golden if q["kind"] == kind]
            return sum(fn(runs[q["id"]], q["answer_docs"], k) for q in qs) / len(qs)
        m = [avg(recall_at, "core", 5), avg(ndcg_at, "core", 5), avg(recall_at, "multi", 5),
             avg(recall_at, "multi", 10), avg(ndcg_at, "multi", 5)]
        scores[(model, mode)] = m
        t.add_row(model if mode == "dense" else "", str(dim) if mode == "dense" else "",
                  f"{n_chunks * dim * 4 / 1024:.0f} KB" if mode == "dense" else "", mode, *(f"{x:.3f}" for x in m),
                  style="bold" if mode == "hybrid" else "")
    t.add_section()
console.print(t)
console.print("Same chunks, same questions, same metric code as step 8; only the embedding model changes.\n", style="dim")
best_dense = max((m for m in models), key=lambda m: (scores[(m, "dense")][4], scores[(m, "dense")][1]))
explain([
    "Read the dense rows to compare the models themselves: bm25 is the same in every hybrid row and hides part of "
    f"the difference. By two-document NDCG@5 the best dense model here is {best_dense}.",
    "The memory column is the raw vectors: length × 4 bytes × chunks. At this size it is nothing; at 10 million "
    "chunks 1536 numbers take about 61 GB, 384 about 15 GB.",
    "bge-m3 runs on your machine through Ollama (free, multilingual, 1024 numbers); bge-small runs inside Python "
    "through FastEmbed (no server, English only, 384). In the homework, Ollama has an n8n Embeddings node; FastEmbed "
    "has none, so that path searches bm25 through an HTTP Request in n8n and keeps the hybrid in the script.",
    "15 model-drafted questions cannot rank models reliably: this table shows how to compare, not which model wins. "
    "Pick the model on your own golden set, not on a leaderboard (slide 72).",
])
console.print("Takeaway: the embedding model is a choice measured on your golden set, and every collection is bound "
              "to the model that built it.")
console.print(cache_note(), style="dim")
