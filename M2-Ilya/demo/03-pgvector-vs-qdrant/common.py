"""Shared helpers: config, chunking, cached embeddings, Postgres and Qdrant clients."""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

import httpx
import numpy as np
import psycopg
import tiktoken
from pgvector.psycopg import register_vector
from rich.console import Console

console = Console()

ROOT = Path(__file__).resolve().parent
SHARED = Path(os.environ.get("SHARED_DIR", "/shared" if Path("/shared").exists() else ROOT.parent / "_shared"))
CORPUS_DIR = SHARED / "corpus"
GOLDEN_PATH = SHARED / "golden.json"
CACHE_DIR = ROOT / "data" / "cache"
EMB_CACHE = CACHE_DIR / "embeddings.json"

PG_DSN = os.environ.get("PG_DSN", "postgresql://demo:demo@localhost:5441/lumen")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://localhost:6361")

EMBED_MODEL = "text-embedding-3-small"
DIM = 1536
CHUNK_TOKENS = 400

COLL = "lumen"          # real corpus: dense + bm25
COLL_BIG = "lumen_big"  # synthetic 20K rows for the filtered-search step

N_TENANTS = 60          # synthetic copies of the corpus for step 4 (~21K rows)
FILTER_TENANTS = ["tenant-007", "tenant-023", "tenant-041"]  # 3 of 60 = 5% of rows

UUID_NS = uuid.UUID("8f6a3c2e-4b1d-4e8a-9c3f-2d7b5e1a0c94")
_enc = tiktoken.get_encoding("cl100k_base")


def ntokens(text: str) -> int:
    return len(_enc.encode(text))


# ---------------------------------------------------------------- corpus ----

@dataclass
class Chunk:
    id: str
    source: str
    title: str
    section: str
    content: str

    @property
    def embed_text(self) -> str:
        # Same string goes to the embedding model for both databases.
        return f"{self.title} / {self.section}\n\n{self.content}"


def read_doc(path: Path) -> tuple[str, str]:
    """Return (title, body) with YAML front matter stripped."""
    text = path.read_text(encoding="utf-8")
    title = path.stem
    if text.startswith("---"):
        _, fm, text = text.split("---", 2)
        m = re.search(r"^title:\s*(.+)$", fm, re.M)
        if m:
            title = m.group(1).strip()
    return title, text.strip()


def chunk_doc(source: str, title: str, body: str) -> list[Chunk]:
    """Split by headings, then pack paragraphs so a chunk stays near CHUNK_TOKENS."""
    sections: list[tuple[str, list[str]]] = []
    current, paras, buf = "Overview", [], []
    for line in body.splitlines():
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            if buf:
                paras.append("\n".join(buf).strip())
                buf = []
            if any(p for p in paras):
                sections.append((current, [p for p in paras if p]))
            paras = []
            current = title if len(m.group(1)) == 1 else m.group(2).strip()
            continue
        if line.strip() == "":
            if buf:
                paras.append("\n".join(buf).strip())
                buf = []
        else:
            buf.append(line)
    if buf:
        paras.append("\n".join(buf).strip())
    if any(p for p in paras):
        sections.append((current, [p for p in paras if p]))

    chunks: list[Chunk] = []
    for section, ps in sections:
        packed: list[str] = []
        cur: list[str] = []
        for p in ps:
            if cur and ntokens("\n\n".join(cur + [p])) > CHUNK_TOKENS:
                packed.append("\n\n".join(cur))
                cur = []
            cur.append(p)
        if cur:
            packed.append("\n\n".join(cur))
        for text in packed:
            idx = len(chunks)
            cid = str(uuid.uuid5(UUID_NS, f"{source}#{idx}"))
            chunks.append(Chunk(cid, source, title, section, text))
    return chunks


def load_corpus(override: dict[str, str] | None = None) -> tuple[list[Chunk], dict[str, str]]:
    """Chunk all corpus files. `override` maps source -> replacement body (step 3)."""
    chunks, titles = [], {}
    for path in sorted(CORPUS_DIR.glob("*.md")):
        title, body = read_doc(path)
        if override and path.name in override:
            body = override[path.name]
        titles[path.name] = title
        chunks.extend(chunk_doc(path.name, title, body))
    return chunks, titles


def golden(kind: str | None = None) -> list[dict]:
    qs = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))["questions"]
    return [q for q in qs if kind is None or q["kind"] == kind]


# ------------------------------------------------------------ embeddings ----

def _key(text: str) -> str:
    return hashlib.sha256(f"{EMBED_MODEL}\n{text}".encode()).hexdigest()


def _load_cache() -> dict[str, list[float]]:
    if EMB_CACHE.exists():
        return json.loads(EMB_CACHE.read_text())
    return {}


def _save_cache(cache: dict[str, list[float]]) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    tmp = EMB_CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache))
    tmp.replace(EMB_CACHE)


def embed(texts: list[str], batch: int = 96) -> np.ndarray:
    """Embed with a disk cache; only missing texts go to OpenAI, in batches, with retry."""
    cache = _load_cache()
    missing = list(dict.fromkeys(t for t in texts if _key(t) not in cache))
    if missing:
        if not os.environ.get("OPENAI_API_KEY"):
            raise SystemExit(
                f"{len(missing)} texts are not in the data/cache/ cache and OPENAI_API_KEY is not set. "
                "Export the key or put it in .env (see .env.example)."
            )
        from openai import APIConnectionError, APIStatusError, OpenAI, RateLimitError

        client = OpenAI()
        for i in range(0, len(missing), batch):
            part = missing[i : i + batch]
            for attempt in range(8):
                try:
                    resp = client.embeddings.create(model=EMBED_MODEL, input=part)
                    break
                except (RateLimitError, APIConnectionError) as e:
                    wait = min(60, 2 ** attempt) + random.random()
                    console.print(f"[yellow]OpenAI {type(e).__name__}, retrying in {wait:.1f} s[/]")
                    time.sleep(wait)
                except APIStatusError as e:
                    if e.status_code >= 500:
                        time.sleep(min(60, 2 ** attempt) + random.random())
                        continue
                    raise
            else:
                raise SystemExit("OpenAI did not respond after 8 attempts")
            for t, d in zip(part, resp.data):
                cache[_key(t)] = d.embedding
            _save_cache(cache)
        console.print(f"[dim]embeddings: {len(missing)} new ones requested from OpenAI, the rest from the cache[/]")
    return np.array([cache[_key(t)] for t in texts], dtype=np.float32)


def embed_one(text: str) -> np.ndarray:
    return embed([text])[0]


# --------------------------------------------------------------- clients ----

def pg() -> psycopg.Connection:
    # prepare_threshold=None: no server-side prepared statements. Otherwise a cached plan
    # survives SET enable_seqscan / hnsw.* changes and step 4 compares the wrong plans.
    conn = psycopg.connect(PG_DSN, autocommit=True, prepare_threshold=None)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")  # register_vector needs the type to exist
    register_vector(conn)
    return conn


class Qdrant:
    """Thin REST client: the JSON bodies are the same ones you would send with curl."""

    def __init__(self, url: str = QDRANT_URL):
        self.http = httpx.Client(base_url=url, timeout=120)

    def req(self, method: str, path: str, body: dict | None = None) -> dict:
        r = self.http.request(method, path, json=body)
        if r.status_code >= 400:
            raise RuntimeError(f"Qdrant {method} {path}: {r.status_code} {r.text[:500]}")
        return r.json()

    def query(self, coll: str, body: dict) -> list[dict]:
        return self.req("POST", f"/collections/{coll}/points/query", body)["result"]["points"]

    def wait_green(self, coll: str, timeout: float = 300) -> dict:
        t0 = time.time()
        while time.time() - t0 < timeout:
            info = self.req("GET", f"/collections/{coll}")["result"]
            if info["status"] == "green":
                return info
            time.sleep(1)
        raise RuntimeError(f"collection {coll} is not green after {timeout}s")


def vec_literal(v: np.ndarray) -> str:
    return "[" + ",".join(f"{x:.7f}" for x in v) + "]"


def short(text: str, n: int = 60) -> str:
    text = " ".join(text.split())
    return text if len(text) <= n else text[: n - 1] + "…"
