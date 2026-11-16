"""Shared helpers for the M2 embeddings demo.

Everything the steps need lives here: corpus loading, a tiny BM25, the
heading-based chunker, a cached OpenAI embedding client and a thin Qdrant
REST wrapper. Kept in one file so the teacher can open it during the lecture.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sys
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from rich.console import Console
from rich.panel import Panel

ROOT = Path(__file__).resolve().parent
CORPUS_DIR = (ROOT / ".." / "_shared" / "corpus").resolve()
CACHE_DIR = ROOT / "data" / "cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
# tiktoken downloads cl100k_base once; keep it next to the demo so the steps work offline.
os.environ.setdefault("TIKTOKEN_CACHE_DIR", str(CACHE_DIR / "tiktoken"))

EMBED_MODEL = "text-embedding-3-small"
EMBED_DIM = 1536
# Demo-specific variable names on purpose: a generic QDRANT_URL from a project .env
# (often localhost:6333) must not redirect the demo to someone else's Qdrant.
QDRANT_URL = os.environ.get("DEMO_QDRANT_URL", "http://localhost:6341").rstrip("/")
COLLECTION = os.environ.get("DEMO_COLLECTION", "lumen_demo")
# Fixed namespace so chunk ids are stable across runs and machines.
ID_NAMESPACE = uuid.uuid5(uuid.NAMESPACE_URL, "https://lumen.example/m2-demo")

console = Console(width=int(os.environ.get("DEMO_WIDTH", "140")))
# DEMO_EXPLAIN=1 adds "how to read this" notes after the tables: for self-study, off in the lecture.
EXPLAIN = os.environ.get("DEMO_EXPLAIN", "") not in ("", "0")


def header(title: str, subtitle: str = "") -> None:
    console.rule(f"[bold]{title}")
    if subtitle:
        console.print(subtitle, style="dim")
    console.print()


def explain(lines: list[str], title: str = "How to read this") -> None:
    if EXPLAIN:
        console.print(Panel("\n".join(f"- {line}" for line in lines), title=title, title_align="left",
                            border_style="cyan"))
        console.print()


# --------------------------------------------------------------------------
# Corpus
# --------------------------------------------------------------------------

@dataclass
class Doc:
    source: str          # file name, e.g. account-and-login.md
    title: str
    section: str         # front matter category: Account | Billing | ...
    date: str
    body: str            # Markdown without front matter


def parse_doc(source: str, text: str) -> Doc:
    meta: dict[str, str] = {}
    body = text
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        body = text[m.end():]
    return Doc(source, meta.get("title", source), meta.get("section", ""), meta.get("date", ""), body.strip())


def load_corpus() -> list[Doc]:
    return [parse_doc(p.name, p.read_text(encoding="utf-8")) for p in sorted(CORPUS_DIR.glob("*.md"))]


# --------------------------------------------------------------------------
# Tokens
# --------------------------------------------------------------------------

_enc = None


def n_tokens(text: str) -> int:
    global _enc
    if _enc is None:
        import tiktoken
        _enc = tiktoken.get_encoding("cl100k_base")
    return len(_enc.encode(text))


# --------------------------------------------------------------------------
# BM25 (pure Python, the classic Okapi formula with Lucene-style IDF)
# --------------------------------------------------------------------------

STOPWORDS = set(
    "a an and are as at be by can do does for from how i if in is it its me my not of on or "
    "the this to was what when why with you your t s m d ll re ve".split()
)


def tokenize(text: str) -> list[str]:
    # Lowercase, split on anything that is not a letter or digit, but keep error codes
    # like "E-4031" as one token: for a support corpus the code is the most specific word.
    return [t for t in re.findall(r"[a-z]+-\d+|\w+", text.lower()) if t not in STOPWORDS]


@dataclass
class BM25:
    docs: list[list[str]]
    k1: float = 1.2
    b: float = 0.75
    index: dict[str, dict[int, int]] = field(default_factory=dict)  # term -> {doc_id: tf}

    def __post_init__(self) -> None:
        for i, toks in enumerate(self.docs):
            for term, tf in Counter(toks).items():
                self.index.setdefault(term, {})[i] = tf
        self.N = len(self.docs)
        self.avgdl = sum(len(d) for d in self.docs) / max(self.N, 1)

    def idf(self, term: str) -> float:
        df = len(self.index.get(term, {}))
        return math.log(1 + (self.N - df + 0.5) / (df + 0.5))

    def term_score(self, tf: int, dl: int, idf: float) -> float:
        norm = self.k1 * (1 - self.b + self.b * dl / self.avgdl)
        return idf * tf * (self.k1 + 1) / (tf + norm)

    def scores(self, query: str) -> np.ndarray:
        out = np.zeros(self.N)
        for term in tokenize(query):
            postings = self.index.get(term)
            if not postings:
                continue
            idf = self.idf(term)
            for i, tf in postings.items():
                out[i] += self.term_score(tf, len(self.docs[i]), idf)
        return out


# --------------------------------------------------------------------------
# Chunking: by headings, target ~400 tokens, never inside code fences or tables
# --------------------------------------------------------------------------

@dataclass
class Chunk:
    source: str
    index: int
    heading: str
    text: str            # "Title > Heading\n\n<body>" -- this is what we embed and store
    tokens: int
    doc: Doc
    overlap: int = 0     # tokens repeated from the end of the previous chunk (0 = none)

    @property
    def id(self) -> str:
        return str(uuid.uuid5(ID_NAMESPACE, f"{self.source}#{self.index}"))

    @property
    def label(self) -> str:
        return f"{self.source.removesuffix('.md')} > {self.heading}"

    def payload(self) -> dict:
        d = self.doc
        return {
            "content": self.text,
            "metadata": {"source": d.source, "title": d.title, "section": d.section, "date": d.date},
        }


def _tail(blocks: list[str], max_tokens: int) -> str:
    """The end of the previous piece that fits into max_tokens, cut at sentence or line borders so the
    overlap reads cleanly. Stops at a table or code block: those are never repeated."""
    out: list[str] = []
    for block in reversed(blocks):
        if block.lstrip().startswith(("|", "```")):
            break
        for unit in reversed(re.split(r"(?<=[.!?])[ \t]+|\n", block)):
            if n_tokens("\n".join([unit] + out)) > max_tokens:
                return "\n".join(out)
            out.insert(0, unit)
    return "\n".join(out)


def _blocks(text: str) -> list[str]:
    """Split Markdown into blocks at blank lines, keeping fenced code blocks whole."""
    blocks, cur, in_code = [], [], False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        if not line.strip() and not in_code:
            if cur:
                blocks.append("\n".join(cur))
                cur = []
            continue
        cur.append(line)
    if cur:
        blocks.append("\n".join(cur))
    return blocks


def _sections(body: str) -> list[tuple[str, str]]:
    """Split a document into (H2 heading, text) pairs. H3 stays inside its H2."""
    out: list[tuple[str, list[str]]] = []
    heading, buf = "Intro", []
    in_code = False
    for line in body.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
        if not in_code and line.startswith("# "):
            continue  # the H1 equals the title, it goes into the prefix
        if not in_code and line.startswith("## "):
            if "".join(buf).strip():
                out.append((heading, buf))
            heading, buf = line[3:].strip(), []
            continue
        buf.append(line)
    if "".join(buf).strip():
        out.append((heading, buf))
    return [(h, "\n".join(b).strip()) for h, b in out]


def chunk_doc(doc: Doc, target: int = 400, max_tokens: int = 500, min_tokens: int = 300,
              overlap_tokens: int = 60, overlap_share: float = 0.0) -> list[Chunk]:
    """Heading-based chunker.

    1. One H2 section = one candidate chunk.
    2. A section longer than max_tokens is split at block boundaries (paragraph,
       table, code block) into pieces close to `target`; the last block of the
       previous piece is repeated at the start of the next one if it is short
       (<= overlap_tokens). With overlap_share > 0 (step 9) the next piece instead starts
       with the last sentences of the previous one, up to target × overlap_share tokens.
    3. Neighbouring small sections (< min_tokens) are merged while the result
       stays under max_tokens.
    Each chunk text starts with "Title > Heading" so the chunk carries its context.
    """
    # Reserve room for the "Title > Heading" prefix so the final chunk stays within max_tokens.
    reserve = 16
    share_tokens = round(target * overlap_share)
    target, max_tokens, min_tokens = target - reserve, max_tokens - reserve, min_tokens - reserve
    pieces: list[tuple[str, str, int]] = []      # (heading, text, overlap tokens)
    for heading, text in _sections(doc.body):
        if n_tokens(text) <= max_tokens:
            pieces.append((heading, text, 0))
            continue
        cur: list[str] = []
        carried = 0
        for block in _blocks(text):
            if cur and n_tokens("\n\n".join(cur + [block])) > target:
                pieces.append((heading, "\n\n".join(cur), carried))
                tail = cur[-1]
                atomic = tail.lstrip().startswith(("|", "```"))     # never repeat a table or code block
                if share_tokens:
                    tail = _tail(cur, share_tokens)
                    cur = [tail] if tail else []
                else:
                    cur = [tail] if n_tokens(tail) <= overlap_tokens and not atomic else []
                carried = n_tokens(tail) if cur else 0
            cur.append(block)
        if cur:
            pieces.append((heading, "\n\n".join(cur), carried))

    merged: list[tuple[str, str, int]] = []
    for heading, text, carried in pieces:
        if merged:
            ph, pt, pc = merged[-1]
            joined = f"{pt}\n\n## {heading}\n\n{text}"
            if (n_tokens(pt) < min_tokens or n_tokens(text) < min_tokens) and n_tokens(joined) <= max_tokens and ph != heading:
                merged[-1] = (ph, joined, pc)
                continue
        merged.append((heading, text, carried))

    chunks = []
    for i, (heading, text, carried) in enumerate(merged):
        full = f"{doc.title} > {heading}\n\n{text}"
        chunks.append(Chunk(doc.source, i, heading, full, n_tokens(full), doc, carried))
    return chunks


def chunk_corpus(docs: list[Doc], target: int = 400, overlap_share: float = 0.0) -> list[Chunk]:
    """All chunks of the corpus. The default (400) is the lecture chunking; step 9 tries other targets,
    keeping the same proportions: range = target × 0.75 ... target × 1.25."""
    if target == 400:
        bounds = {"max_tokens": 500, "min_tokens": 300}
    else:
        bounds = {"max_tokens": round(target * 1.25), "min_tokens": round(target * 0.75)}
    return [c for d in docs for c in chunk_doc(d, target=target, overlap_share=overlap_share, **bounds)]


# --------------------------------------------------------------------------
# Embeddings with a local cache (model + text hash -> vector)
# --------------------------------------------------------------------------

# One cache file per model; the key is sha256 of the model name and the text.
_caches: dict[str, dict[str, np.ndarray]] = {}
STATS = {"api_calls": 0, "api_texts": 0, "cache_hits": 0}


def _key(text: str, model: str = EMBED_MODEL) -> str:
    return hashlib.sha256(f"{model}\n{text}".encode()).hexdigest()


def _cache_file(model: str) -> Path:
    return CACHE_DIR / f"embeddings-{re.sub(r'[^A-Za-z0-9.-]+', '_', model)}.npz"


def _load_cache(model: str = EMBED_MODEL) -> dict[str, np.ndarray]:
    if model not in _caches:
        _caches[model] = {}
        if _cache_file(model).exists():
            z = np.load(_cache_file(model))
            _caches[model] = dict(zip(z["keys"].tolist(), z["vectors"]))
    return _caches[model]


def _save_cache(model: str = EMBED_MODEL) -> None:
    cache = _load_cache(model)
    keys = np.array(list(cache.keys()))
    vecs = np.stack(list(cache.values())).astype(np.float32)
    tmp = _cache_file(model).with_suffix(".tmp.npz")
    np.savez_compressed(tmp, keys=keys, vectors=vecs)
    tmp.replace(_cache_file(model))


def _openai_client(missing: str = "some texts are not in the cache", fix: str = "run `make warm`"):
    if not os.environ.get("OPENAI_API_KEY"):
        console.print(f"[red]No OPENAI_API_KEY in the environment, and {missing}.[/red] "
                      f"Export the key (see .env.example) and {fix}.")
        sys.exit(2)
    if not os.environ.get("OPENAI_BASE_URL"):
        # An empty OPENAI_BASE_URL (common in copied .env files) breaks the client.
        os.environ.pop("OPENAI_BASE_URL", None)
    from openai import OpenAI
    return OpenAI(max_retries=0, timeout=60)


def _with_retries(call):
    for attempt in range(8):
        try:
            return call()
        except Exception as e:  # rate limits are shared with other demos: back off
            status = getattr(e, "status_code", None)
            if status in (429, 500, 502, 503) or "Connection" in type(e).__name__:
                wait = min(2 ** attempt, 30)
                console.print(f"[yellow]OpenAI {status or type(e).__name__}, retrying in {wait} s[/yellow]")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError("OpenAI: retries exhausted")


def _openai_embed(texts: list[str]) -> list[np.ndarray]:
    resp = _with_retries(lambda: _openai_client().embeddings.create(model=EMBED_MODEL, input=texts))
    return [np.asarray(d.embedding, dtype=np.float32) for d in resp.data]


def _cached_embed(model: str, texts: list[str], fetch, batch_size: int = 100) -> np.ndarray:
    """Vectors from the model's cache; `fetch` is called only for the texts that are missing."""
    cache = _load_cache(model)
    missing = list(dict.fromkeys(t for t in texts if _key(t, model) not in cache))
    STATS["cache_hits"] += len(texts) - len(missing)
    if missing:
        for start in range(0, len(missing), batch_size):
            batch = missing[start:start + batch_size]
            for t, v in zip(batch, fetch(batch)):
                cache[_key(t, model)] = np.asarray(v, dtype=np.float32)
            STATS["api_calls"] += 1
            STATS["api_texts"] += len(batch)
        _save_cache(model)
    return np.stack([cache[_key(t, model)] for t in texts])


def embed(texts: list[str], batch_size: int = 100) -> np.ndarray:
    """Return an (n, 1536) float32 matrix. Hits the API only for texts not in the cache."""
    return _cached_embed(EMBED_MODEL, texts, _openai_embed, batch_size)


def embed_one(text: str) -> np.ndarray:
    return embed([text])[0]


# --------------------------------------------------------------------------
# Other embedding models (step 11): cached the same way, so step 11 runs offline after `make warm`
# --------------------------------------------------------------------------

OLLAMA_URL = os.environ.get("DEMO_OLLAMA_URL", "http://localhost:11434").rstrip("/")
# short name -> (model id: cache key and collection metadata, vector size, where it runs)
OTHER_MODELS = {
    "bge-m3": ("bge-m3", 1024, "Ollama, a local server"),
    "bge-small-en-v1.5": ("BAAI/bge-small-en-v1.5", 384, "FastEmbed, ONNX inside this process"),
}


class ModelUnavailable(RuntimeError):
    """The model is not in the cache and cannot be run on this machine."""


def _ollama_embed(texts: list[str]) -> list:
    import httpx
    try:
        r = httpx.post(f"{OLLAMA_URL}/api/embed", json={"model": "bge-m3", "input": texts}, timeout=300)
    except httpx.ConnectError:
        raise ModelUnavailable(f"Ollama is not reachable at {OLLAMA_URL}: `ollama serve`, then `ollama pull bge-m3`")
    if r.status_code >= 400:
        raise ModelUnavailable(f"Ollama answered {r.status_code}: {r.text[:120]} (`ollama pull bge-m3`)")
    return r.json()["embeddings"]


_fastembed = None


def _fastembed_embed(texts: list[str]) -> list:
    global _fastembed
    try:
        from fastembed import TextEmbedding
    except ImportError:
        raise ModelUnavailable("FastEmbed is not installed: `make setup` (it is pinned in requirements.txt)")
    if _fastembed is None:
        _fastembed = TextEmbedding(OTHER_MODELS["bge-small-en-v1.5"][0])   # downloads ~70 MB once
    return list(_fastembed.embed(texts))


def embed_other(name: str, texts: list[str]) -> np.ndarray:
    """Like embed(), for the models of step 11. Raises ModelUnavailable on a cache miss it cannot serve."""
    fetch = _ollama_embed if name == "bge-m3" else _fastembed_embed
    return _cached_embed(OTHER_MODELS[name][0], texts, fetch, batch_size=32)


# --------------------------------------------------------------------------
# Chat model (step 10): answers are cached by the full request, like the embeddings
# --------------------------------------------------------------------------

CHAT_MODEL = os.environ.get("DEMO_CHAT_MODEL", "gpt-4o-mini")
_ANSWERS_FILE = CACHE_DIR / "answers.json"
CHAT_STATS = {"calls": 0, "hits": 0}


def chat(messages: list[dict]) -> str:
    request = {"model": CHAT_MODEL, "temperature": 0, "messages": messages}
    key = hashlib.sha256(json.dumps(request, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    cache = json.loads(_ANSWERS_FILE.read_text(encoding="utf-8")) if _ANSWERS_FILE.exists() else {}
    if key in cache:
        CHAT_STATS["hits"] += 1
        return cache[key]
    client = _openai_client("this answer is not in the cache", "run `make step10` once")
    resp = _with_retries(lambda: client.chat.completions.create(**request))
    cache[key] = resp.choices[0].message.content
    _ANSWERS_FILE.write_text(json.dumps(cache, ensure_ascii=False, indent=1), encoding="utf-8")
    CHAT_STATS["calls"] += 1
    return cache[key]


def cache_note() -> str:
    return (f"embeddings: from cache {STATS['cache_hits']}, API requests {STATS['api_calls']} "
            f"({STATS['api_texts']} texts)")


# --------------------------------------------------------------------------
# Qdrant REST (plain HTTP so the JSON on screen is exactly what goes over the wire)
# --------------------------------------------------------------------------

def qdrant(method: str, path: str, body: dict | None = None) -> dict:
    import httpx
    try:
        r = httpx.request(method, f"{QDRANT_URL}{path}", json=body, timeout=60)
    except httpx.ConnectError:
        console.print(f"[red]Qdrant is not reachable at {QDRANT_URL}.[/red] Run `make up`.")
        sys.exit(2)
    if r.status_code == 404 and "doesn't exist" in r.text:
        console.print(f"[red]Collection \"{COLLECTION}\" does not exist.[/red] Run `make step5` first.")
        sys.exit(2)
    if r.status_code >= 400:
        console.print(f"[red]{method} {path} -> {r.status_code}[/red] {r.text[:500]}")
        r.raise_for_status()
    return r.json()


def check_collection(collection: str = COLLECTION, model: str = EMBED_MODEL, size: int = EMBED_DIM) -> None:
    """Stop if the collection was built with another embedding model or dimension than this code uses.
    A model mismatch gives no error at search time, only meaningless results, so it is checked before every run."""
    cfg = qdrant("GET", f"/collections/{collection}")["result"]["config"]
    built_by = (cfg.get("metadata") or {}).get("embedding_model")
    built_size = cfg["params"]["vectors"].get("size")
    if built_by != model or built_size != size:
        console.print(f"[red]Collection \"{collection}\" was built with {built_by} ({built_size} dims), this code embeds "
                      f"questions with {model} ({size}).[/red] Search would return nonsense without an error. "
                      "Rebuild it: `make step5`.")
        sys.exit(2)
    console.print(f"Collection check ({collection}): {built_by}, {built_size} dims, the same model as in the code.\n",
                  style="dim")


def points_count(exact: bool = True) -> int:
    return qdrant("POST", f"/collections/{COLLECTION}/points/count", {"exact": exact})["result"]["count"]


def short_json(obj, max_floats: int = 6, max_str: int = 160) -> str:
    """JSON dump for the screen: long float lists (vectors) and long strings are truncated,
    short arrays are printed on one line."""
    def trim(o):
        if isinstance(o, list) and len(o) > max_floats and all(isinstance(x, (int, float)) for x in o):
            return [round(x, 4) if isinstance(x, float) else x for x in o[:max_floats]] + [f"... {len(o) - max_floats} more"]
        if isinstance(o, dict):
            return {k: trim(v) for k, v in o.items()}
        if isinstance(o, list):
            return [trim(x) for x in o]
        if isinstance(o, float):
            return round(o, 4)
        if isinstance(o, str) and len(o) > max_str:
            return o[:max_str] + f"... (+{len(o) - max_str} chars)"
        return o
    text = json.dumps(trim(obj), ensure_ascii=False, indent=2)
    # Collapse arrays without nested objects onto one line.
    return re.sub(r"\[\s*([^\[\]{}]*?)\s*\]", lambda m: "[" + " ".join(m.group(1).split()) + "]", text)


# Queries used in steps 3 and 6: (kind, question, answer document, regex that marks the answer chunk).
QUERIES = [
    ("Error code", "What does E-4031 mean?", "payment-errors-reference.md", r"> E-4031 "),
    ("Paraphrase", "I'm a viewer on my company's workspace. Why is the export button missing for me?",
     "team-and-roles.md", r"(?i)viewers? cannot export"),
    ("Russian question", "Ссылка для сброса пароля перестала работать. Сколько она вообще действует?",
     "account-and-login.md", r"reset link is valid for"),
]


def is_answer(chunk_text: str, source: str, expected_source: str, pattern: str) -> bool:
    return source == expected_source and re.search(pattern, chunk_text) is not None
TRAP_QUERY = "How do I connect Lumen to Salesforce?"

STEP2_ANCHOR = "I can't log in to my account"
STEP2_PHRASES = [
    "How do I reset my password?",
    "Не могу войти в аккаунт",
    "Where can I download my invoice for the last payment?",
    "The weather in Lisbon is sunny today",
]
# Step 0: facts that must live in exactly one document, and topics kept out of the corpus for the traps.
STEP0_FACTS = [("reset link lifetime", "60 minutes"), ("extra seat price", "$5 per seat"),
               ("Team export limit", "100,000"), ("Business plan price", "$149"), ("error code", "E-4012")]
TRAP_TOPICS = ["Salesforce", "dark mode", "on-premise", "self-hosted", "phone support"]
# Step 10: an easy question, a trap, a number to compare with a limit, two intents in one question.
STEP10_IDS = ["q02", "t01", "m01", "m03"]
# Step 11: one question embedded by three models.
STEP11_PHRASE = "How long is the password reset link valid?"
STEP7_QUERIES = [
    "How long is the password reset link valid?",
    "How do I change the email address of my account?",
]


# --------------------------------------------------------------------------
# Golden set and retrieval metrics (steps 8 and 9)
# --------------------------------------------------------------------------

GOLDEN_FILE = (ROOT / ".." / "_shared" / "golden.json").resolve()
SEARCH_MODES = ("dense", "bm25", "hybrid")


def load_golden() -> list[dict]:
    """17 questions: 10 'core' (one answer document), 5 'multi' (two documents), 2 'trap' (no answer)."""
    return json.loads(GOLDEN_FILE.read_text(encoding="utf-8"))["questions"]


def search_body(mode: str, text: str, vec: list[float], limit: int = 10, fusion: dict | None = None) -> dict:
    """The /points/query body for one search mode; `fusion` replaces {"fusion": "rrf"} in the hybrid."""
    sparse = {"text": text, "model": "Qdrant/bm25"}
    if mode == "dense":
        return {"query": vec, "limit": limit, "with_payload": True}
    if mode == "bm25":
        return {"query": sparse, "using": "bm25", "limit": limit, "with_payload": True}
    return {"prefetch": [{"query": vec, "limit": 20}, {"query": sparse, "using": "bm25", "limit": 20}],
            "query": fusion or {"fusion": "rrf"}, "limit": limit, "with_payload": True}


def search(mode: str, text: str, vec: list[float], collection: str = COLLECTION, limit: int = 10,
           fusion: dict | None = None) -> list[dict]:
    # Equal scores (common in RRF) come back in any order; ask for a few more and break ties by id,
    # so the metrics and the step 10 prompts are the same on every run.
    body = search_body(mode, text, vec, limit + 10, fusion)
    points = qdrant("POST", f"/collections/{collection}/points/query", body)["result"]["points"]
    return sorted(points, key=lambda p: (-p["score"], str(p["id"])))[:limit]


def sources_of(points: list[dict]) -> list[str]:
    return [p["payload"]["metadata"]["source"] for p in points]


def doc_ranks(sources: list[str], answer_docs: list[str]) -> list[int | None]:
    """Position (from 1) of the first chunk of each answer document, None if it is not in the list."""
    return [sources.index(d) + 1 if d in sources else None for d in answer_docs]


def recall_at(sources: list[str], answer_docs: list[str], k: int) -> int:
    """1 if every answer document is in the first k results, else 0."""
    return int(all(d in sources[:k] for d in answer_docs))


def ndcg_at(sources: list[str], answer_docs: list[str], k: int) -> float:
    """rel = 1 at the first position of each answer document (later chunks of the same document add nothing),
    DCG = sum of rel / log2(position + 1), IDCG = the same with the answer documents on top."""
    dcg, seen = 0.0, set()
    for pos, s in enumerate(sources[:k], start=1):
        if s in answer_docs and s not in seen:
            seen.add(s)
            dcg += 1 / math.log2(pos + 1)
    idcg = sum(1 / math.log2(pos + 1) for pos in range(1, min(len(answer_docs), k) + 1))
    return dcg / idcg


def collection_body(chunker: str, model: str = EMBED_MODEL, size: int = EMBED_DIM) -> dict:
    """The collection schema of step 5 (unnamed dense + named sparse bm25 with IDF)."""
    return {
        "vectors": {"size": size, "distance": "Cosine"},
        "sparse_vectors": {"bm25": {"modifier": "idf"}},
        "metadata": {"embedding_model": model, "sparse_model": "Qdrant/bm25", "chunker": chunker},
    }


# --------------------------------------------------------------------------
# Helpers for step 7 (re-ingest of one changed document)
# --------------------------------------------------------------------------

CHANGED_SOURCE = "account-and-login.md"


def changed_doc(docs: list[Doc]) -> Doc:
    """New version of account-and-login.md: reset link now valid 30 minutes and the last
    section ("Changing the account email address") was removed. The shared corpus is not touched."""
    d = next(x for x in docs if x.source == CHANGED_SOURCE)
    body = d.body.replace("valid for **60 minutes**", "valid for **30 minutes**")
    body = body.split("\n## Changing the account email address", 1)[0].rstrip()
    return Doc(d.source, d.title, d.section, "2026-11-01", body)


def to_points(chunks: list[Chunk], vectors: np.ndarray, ids: list[str] | None = None) -> list[dict]:
    return [{
        "id": ids[i] if ids else c.id,
        "vector": {"": v.tolist(), "bm25": {"text": c.text, "model": "Qdrant/bm25"}},
        "payload": c.payload(),
    } for i, (c, v) in enumerate(zip(chunks, vectors))]


def source_filter(source: str) -> dict:
    return {"must": [{"key": "metadata.source", "match": {"value": source}}]}


def ids_for_source(source: str) -> list[str]:
    res = qdrant("POST", f"/collections/{COLLECTION}/points/scroll",
                 {"filter": source_filter(source), "limit": 1000, "with_payload": False})
    return [p["id"] for p in res["result"]["points"]]
