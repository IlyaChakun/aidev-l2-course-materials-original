"""Precompute every embedding the steps need, so the lecture runs from the local cache.

Run once before the lecture with OPENAI_API_KEY set. Afterwards all steps work offline
(Qdrant still needs Docker, but no OpenAI calls are made).
"""
from lib import (OTHER_MODELS, QUERIES, STEP2_ANCHOR, STEP2_PHRASES, STEP7_QUERIES, STEP10_IDS, STEP11_PHRASE, TRAP_QUERY,
                 ModelUnavailable, cache_note, changed_doc, chunk_corpus, chunk_doc, console, embed, embed_other,
                 load_corpus, load_golden)

docs = load_corpus()
texts = [STEP2_ANCHOR, *STEP2_PHRASES]
texts += [c.text for c in chunk_corpus(docs)]
texts += [q[1] for q in QUERIES] + [TRAP_QUERY] + STEP7_QUERIES
texts += [c.text for c in chunk_doc(changed_doc(docs))]
golden = load_golden()
texts += [q["question"] for q in golden if q["kind"] != "trap" or q["id"] in STEP10_IDS]   # steps 8 and 10
for target, share in ((300, 0.0), (300, 0.12), (500, 0.0)):                             # step 9 chunkings
    texts += [c.text for c in chunk_corpus(docs, target=target, overlap_share=share)]
vecs = embed(texts)
console.print(f"Done: {len(texts)} texts, matrix {vecs.shape}. {cache_note()}")

# Step 11: the same corpus and questions through the two local models (Ollama bge-m3, FastEmbed bge-small).
other = [c.text for c in chunk_corpus(docs)] + [q["question"] for q in golden if q["kind"] != "trap"] + [STEP11_PHRASE]
for name, (model_id, dim, where) in OTHER_MODELS.items():
    try:
        console.print(f"{model_id} ({where}): matrix {embed_other(name, other).shape}")
    except ModelUnavailable as e:
        console.print(f"[yellow]{model_id} skipped: {e}. Step 11 will skip it too.[/yellow]")
console.print("Step 10 answers are cached on the first run of `make step10` (it needs the collection of step 5).")
