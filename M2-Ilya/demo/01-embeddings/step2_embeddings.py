"""Step 2. Text -> embedding with OpenAI text-embedding-3-small; cosine vs dot.

DEMO_EXPLAIN=1 adds a "how to read this" note after every table, with the numbers worked out.
"""
import numpy as np
from rich.table import Table

from lib import EMBED_MODEL, STEP2_ANCHOR, STEP2_PHRASES, cache_note, console, embed, explain, header, tokenize

header("Step 2. Text → embedding",
       f"Model {EMBED_MODEL}: a text becomes an array of 1536 numbers. Texts with similar meaning lie close together.")

ANCHOR, PHRASES = STEP2_ANCHOR, STEP2_PHRASES
vecs = embed([ANCHOR] + PHRASES)
a = vecs[0]

t = Table(title="What the model returns")
t.add_column("text")
t.add_column("length", justify="right")
t.add_column("first 8 numbers")
t.add_column("norm ||v||", justify="right")
t.add_row(ANCHOR, str(len(a)), " ".join(f"{x:+.4f}" for x in a[:8]), f"{np.linalg.norm(a):.4f}")
console.print(t)
console.print("Norm = 1.0: OpenAI returns normalized vectors. The numbers mean nothing on their own, "
              "the meaning is only in the distances.\n", style="dim")
explain([
    f"An embedding model reads a text and returns a fixed list of numbers: {len(a)} for {EMBED_MODEL}, whatever the "
    "length of the text. Think of it as coordinates of a point in a space with that many axes.",
    "The model was trained so that texts with similar meaning get nearby points. No single axis means "
    "'about passwords' or 'about billing': one number on its own says nothing, like one coordinate does not tell you "
    "which city it is.",
    f"length = how many numbers (the dimension, {len(a)}). It is not the length of the text and not the model's "
    "input limit; every text, short or long, becomes exactly this many numbers.",
    f"norm ||v|| = sqrt(sum of the squares of all {len(a)} numbers) = sqrt({float(a @ a):.4f}) = {np.linalg.norm(a):.4f}. "
    "OpenAI scales every vector to length 1, so only its direction carries meaning.",
    "The texts were embedded once with the API key and stored in data/cache/, so this step runs offline.",
])


def cosine(x: np.ndarray, y: np.ndarray) -> float:
    return float(x @ y / (np.linalg.norm(x) * np.linalg.norm(y)))


t = Table(title=f"Closeness to the phrase \"{ANCHOR}\"")
t.add_column("phrase")
t.add_column("shared words", justify="right")
t.add_column("cosine", justify="right")
t.add_column("dot", justify="right")
t.add_column("euclid", justify="right")
anchor_words = set(tokenize(ANCHOR))
rows = []
for p, v in zip(PHRASES, vecs[1:]):
    rows.append((p, len(anchor_words & set(tokenize(p))), cosine(a, v), float(a @ v), float(np.linalg.norm(a - v))))
for p, shared, cos, dot, euc in sorted(rows, key=lambda r: -r[2]):
    t.add_row(p, str(shared), f"{cos:.4f}", f"{dot:.4f}", f"{euc:.4f}")
console.print(t)

max_diff = max(abs(r[2] - r[3]) for r in rows)
console.print(f"cosine and dot match (the difference is at most {max_diff:.4f}, float rounding): for vectors of length 1 "
              "cosine = dot, and euclid = sqrt(2 - 2 * cosine), the order is the same.", style="dim")
console.print("The absolute values of this model are compressed (rarely above 0.7): look at the order, not at the number.\n", style="dim")
top = max(rows, key=lambda r: r[2])
explain([
    f"Each row compares one phrase with \"{ANCHOR}\". Rows are sorted from the closest to the farthest.",
    "shared words: how many words the two phrases have in common after the step 1 tokenizer. It is 0 everywhere, "
    "so BM25 from step 1 would score every row 0 and could not rank them at all.",
    "cosine: the cosine of the angle between the two arrows. 1 = same direction (same meaning), 0 = unrelated, "
    "below 0 = opposite. Bigger is closer. This is the main measure for text embeddings.",
    "dot: multiply the numbers pairwise and add them up. For vectors of length 1 it equals the cosine; "
    "databases often use it because it is cheaper (no division by the lengths).",
    f"euclid: the straight-line distance between the two points. Smaller is closer. For length-1 vectors "
    f"euclid = sqrt(2 - 2 × cosine): for the top row sqrt(2 - 2 × {top[2]:.4f}) = {np.sqrt(2 - 2 * top[2]):.4f}, "
    f"as in the table ({top[4]:.4f}). So all three columns give the same order.",
    "A toy example with 2 numbers instead of 1536: q = (0.6, 0.8), d1 = (0.8, 0.6), d2 = (-0.8, 0.6). "
    "cos(q, d1) = 0.6×0.8 + 0.8×0.6 = 0.96 (almost the same direction); cos(q, d2) = -0.48 + 0.48 = 0.00 (unrelated).",
    "Read the order, not the value: this model rarely gives more than 0.7 even for near-synonyms, "
    "so 0.47 already means 'close' and 0.05 means 'unrelated'.",
    "The Russian phrase is the closest of all: the model was trained on many languages and maps the same meaning "
    "to nearby points regardless of language. That is exactly where BM25 failed in step 1.",
])

console.print("Takeaway: \"can't log in\" and \"reset password\" share no words, yet lie close together. "
              "BM25 from step 1 would give zero. The Russian phrase is next to the English one: the model is multilingual.")
console.print(cache_note(), style="dim")
