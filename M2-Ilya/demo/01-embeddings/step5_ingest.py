"""Step 5. Ingestion into Qdrant step by step: collection -> embeddings -> upsert -> verify.

DEMO_EXPLAIN=1 adds a "how to read this" note after every sub-step.
"""
import time

from rich.syntax import Syntax
from rich.table import Table

from lib import (COLLECTION, EMBED_DIM, EMBED_MODEL, QDRANT_URL, cache_note, chunk_corpus, console, embed, explain,
                 header, load_corpus, points_count, qdrant, short_json)

BATCH = 64

header("Step 5. Loading into Qdrant step by step",
       f"Qdrant {qdrant('GET', '/')['version']} at {QDRANT_URL}, collection \"{COLLECTION}\".")
explain([
    "Steps 1-4 kept everything in Python memory. Now the chunks go into a real vector database, Qdrant, running in "
    f"Docker ({QDRANT_URL}, started by 'make up'). Steps 6 and 7 query and change this data.",
    "The script talks to Qdrant over plain HTTP with JSON, the same REST API you see in the Dashboard console. "
    "Every request is printed: a bold title, the method and path in cyan, the JSON body, then the response.",
    f"Qdrant words: a collection is like a table; a point is like a row (an id, one or more vectors, and a JSON "
    f"payload with the text and metadata). Here: collection \"{COLLECTION}\", one point per chunk.",
])


def show(title: str, method: str, path: str, body: dict | None = None) -> dict:
    console.print(f"[bold]{title}[/bold]  [cyan]{method} {path}[/cyan]")
    if body is not None:
        console.print(Syntax(short_json(body), "json", theme="ansi_dark", word_wrap=True))
    res = qdrant(method, path, body)
    console.print(f"[dim]response: {short_json(res.get('result'))[:200]}[/dim]\n")
    return res


# 5.1 Recreate the collection: the schema lives in code, one command rebuilds it.
existing = [c["name"] for c in qdrant("GET", "/collections")["result"]["collections"]]
if COLLECTION in existing:
    show("5.0 The collection already exists, deleting it (the schema lives in code, one command recreates it)",
         "DELETE", f"/collections/{COLLECTION}")

show("5.1 Creating the collection: unnamed dense + named sparse \"bm25\"", "PUT", f"/collections/{COLLECTION}", {
    "vectors": {"size": EMBED_DIM, "distance": "Cosine"},
    "sparse_vectors": {"bm25": {"modifier": "idf"}},
    "metadata": {"embedding_model": EMBED_MODEL, "sparse_model": "Qdrant/bm25", "chunker": "h2-400tok"},
})
explain([
    "5.0: if the collection exists from an earlier run, it is deleted first. The schema lives in this script, so one "
    "command rebuilds the whole collection the same way every time.",
    f"5.1 creates the collection with two kinds of vectors per point. 'vectors': the dense embedding, size {EMBED_DIM} "
    f"(must equal the model's output, {EMBED_MODEL}), compared by Cosine. It has no name, so it is the default vector; "
    "the n8n Qdrant node in the homework expects exactly that.",
    "'sparse_vectors' → 'bm25': a second, named vector for word matching (BM25, as in step 1). Sparse = it has a "
    "value only for the words present in the chunk, all other positions are zero and not stored.",
    "'modifier: idf': Qdrant itself keeps the IDF of every word across the collection and applies it at query time, "
    "so IDF stays correct as you add or delete points.",
    "'metadata': a note on the collection itself: which models built it. If someone later searches with another "
    "embedding model, a script can compare and refuse instead of returning garbage.",
    "response: true = the collection was created.",
])

show("5.2 Index on metadata.source before loading (needed for filters and deletion in step 7)",
     "PUT", f"/collections/{COLLECTION}/index", {"field_name": "metadata.source", "field_schema": "keyword"})
explain([
    "A payload index works like an index in a SQL database: Qdrant can find all points with "
    "metadata.source = 'account-and-login.md' without scanning every point.",
    "keyword = exact match on a string (not full-text search). Step 7 uses it to delete all chunks of one document "
    "by a filter; filtered searches use it too.",
    "Create it before loading: Qdrant then builds the search structures with the filter in mind. "
    "'acknowledged' = the request was accepted.",
])

# 5.3 Chunks and dense vectors. The cache makes reruns free; the API sees only new texts.
docs = load_corpus()
chunks = chunk_corpus(docs)
t0 = time.time()
dense = embed([c.text for c in chunks], batch_size=100)
console.print(f"[bold]5.3 Embeddings[/bold]: {len(chunks)} chunks from {len(docs)} documents → matrix {dense.shape}, "
              f"{time.time() - t0:.1f} s. {cache_note()}\n")

c0 = chunks[0]
console.print(f"[bold]5.4 Chunk identifier[/bold]: uuid5(namespace, \"{c0.source}#{c0.index}\") = {c0.id}\n"
              "[dim]The same document and number give the same id on every restart: upsert overwrites the point "
              "instead of creating a duplicate.[/dim]\n")
explain([
    f"5.3: the {len(chunks)} chunk texts are turned into dense vectors, the same way as in steps 2-3. "
    "'from cache' = no OpenAI call was needed; the time is near zero because nothing went over the network.",
    "5.4: every point needs an id. uuid5 is not random: it is a hash of a fixed namespace plus the text "
    f"\"{c0.source}#{c0.index}\" (file name # chunk number from step 4). The same input always gives the same id.",
    "Why it matters: loading the same chunk again then overwrites the existing point. With random ids (uuid4) "
    "every reload would add a copy. Step 7 shows both cases.",
])

# 5.5 Upsert in batches. Sparse is computed by Qdrant itself from the text (server-side "Qdrant/bm25").
console.print(f"[bold]5.5 Upsert in batches of {BATCH}, wait=true[/bold]  [cyan]PUT /collections/{COLLECTION}/points?wait=true[/cyan]")
sample_point = None
for start in range(0, len(chunks), BATCH):
    points = []
    for c, v in zip(chunks[start:start + BATCH], dense[start:start + BATCH]):
        points.append({
            "id": c.id,
            "vector": {
                "": v.tolist(),                                          # dense, unnamed
                "bm25": {"text": c.text, "model": "Qdrant/bm25"},        # sparse, computed by the server
            },
            "payload": c.payload(),
        })
    if sample_point is None:
        sample_point = points[0]
        console.print(Syntax(short_json({"points": [sample_point, "..."]}), "json", theme="ansi_dark", word_wrap=True))
    t0 = time.time()
    res = qdrant("PUT", f"/collections/{COLLECTION}/points?wait=true", {"points": points})
    console.print(f"  batch {start // BATCH + 1}: points {len(points)}, status {res['result']['status']}, "
                  f"{time.time() - t0:.2f} s")
console.print()
explain([
    "upsert = insert or update: a point with a new id is added, a point with an existing id is overwritten.",
    f"The JSON above is the first point of the first request: 'id' from 5.4; 'vector' with two parts: "
    f"\"\" (the unnamed dense vector, {EMBED_DIM} numbers, shortened on screen) and 'bm25' given as text + model. "
    "For the sparse part we send words, not numbers: Qdrant computes the BM25 vector on the server with its "
    "built-in 'Qdrant/bm25' model.",
    "'payload': the data stored next to the vectors and returned with search results. 'content' is the chunk text "
    "(what the model will read), 'metadata' is where it came from. These two keys are the layout n8n expects.",
    f"Points go in batches of {BATCH} so one request does not get too large; {len(chunks)} chunks = "
    f"{-(-len(chunks) // BATCH)} requests.",
    "wait=true: Qdrant answers only after the points are written and searchable ('status completed'). Without it "
    "Qdrant answers at once, and a count or a test run straight after loading can see fewer points.",
])

# 5.6 Verify: count, collection config, one stored point.
info = qdrant("GET", f"/collections/{COLLECTION}")["result"]
t = Table(title="5.6 Verification after loading")
t.add_column("what", style="bold")
t.add_column("value")
t.add_row("chunks sent", str(len(chunks)))
t.add_row("points in the collection (count exact)", str(points_count()))
t.add_row("collection status", info["status"])
t.add_row("dense", f"size={info['config']['params']['vectors']['size']}, distance={info['config']['params']['vectors']['distance']}")
t.add_row("sparse", str(info["config"]["params"].get("sparse_vectors")))
t.add_row("collection metadata", str(info["config"].get("metadata")))
t.add_row("payload indexes", ", ".join(info.get("payload_schema", {}).keys()) or "none")
console.print(t)
explain([
    "Always check after loading instead of trusting the code: what you sent must equal what is stored.",
    "chunks sent = points in the collection: nothing was lost. 'count exact' asks Qdrant for a precise count "
    "(an approximate one is faster but can lag).",
    "status green = the collection is ready: all background work (indexing) is done. Yellow = still optimizing.",
    "dense, sparse, metadata, payload indexes: the settings read back from Qdrant, so you can confirm they match 5.1 "
    "and 5.2.",
])

stored = qdrant("POST", f"/collections/{COLLECTION}/points", {"ids": [c0.id], "with_payload": True, "with_vector": True})
p = stored["result"][0]
sp = p["vector"]["bm25"]
console.print(f"\n[bold]One point as Qdrant stores it[/bold] (dense truncated; sparse \"bm25\": {len(sp['indices'])} "
              f"non-zero dimensions out of 2^32 possible)")
console.print(Syntax(short_json(p, max_floats=5), "json", theme="ansi_dark", word_wrap=True))
explain([
    "This is the point read back from Qdrant, not what we sent: the stored form.",
    "\"\": the dense vector, 1536 numbers, almost all of them non-zero.",
    f"'bm25': the text we sent has become a sparse vector. 'indices' = numbers that stand for words (a hash of each "
    f"word, so no vocabulary has to be stored); 'values' = the word's weight in this chunk, which grows with how often "
    f"the word occurs (with saturation, as in step 1). Only {len(sp['indices'])} words are stored instead of "
    "billions of zeros; IDF is applied at query time (modifier idf).",
    "'payload': the text and metadata, returned with every search result.",
    "The same point is visible in the Dashboard (link below): Collections → lumen_demo → Points.",
], title="How to read the stored point")
console.print(f"\nDashboard: [link]{QDRANT_URL}/dashboard#/collections/{COLLECTION}[/link]  (make dashboard)")
