"""Client-side BM25 term weights for a Qdrant sparse vector with modifier=idf.

We compute only the term-frequency part of BM25 (saturation k1, length norm b).
Qdrant multiplies it by IDF at query time; IDF statistics live on the server,
which is exactly what the per-tenant IDF demo is about.
"""
import re
import zlib
from collections import Counter

K1 = 1.2
B = 0.75
AVG_LEN = 250.0  # fixed average length in tokens; fine for a demo

STOP = set(
    "a an and are as at be by can for from has have if in into is it its of on or "
    "that the their them there these this to was were will with not no do does you your "
    "we our they he she i".split()
)
_TOKEN = re.compile(r"[a-z0-9]+")


def tokenize(text: str):
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOP and len(t) > 1]


def term_index(term: str) -> int:
    return zlib.crc32(term.encode()) & 0x7FFFFFFF


def doc_vector(text: str):
    toks = tokenize(text)
    tf = Counter(toks)
    dl = len(toks) or 1
    idx, val = [], []
    for term, f in tf.items():
        w = f * (K1 + 1) / (f + K1 * (1 - B + B * dl / AVG_LEN))
        idx.append(term_index(term))
        val.append(round(w, 6))
    return {"indices": idx, "values": val}


def query_vector(text: str):
    terms = sorted(set(tokenize(text)))
    return {"indices": [term_index(t) for t in terms], "values": [1.0] * len(terms)}
