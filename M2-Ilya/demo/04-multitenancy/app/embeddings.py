"""OpenAI embeddings with a file cache (one JSON file per text) and retry on 429/5xx.

Reruns are free and offline once every text has been embedded once.
The API key is read from the environment only and never logged.
"""
import hashlib
import json
import os
import random
import time

import httpx

from app import settings

BATCH = 64


def _key(text: str) -> str:
    return hashlib.sha256(f"{settings.EMBED_MODEL}\n{text}".encode()).hexdigest()


def _path(key: str):
    d = settings.CACHE_DIR / "embeddings" / key[:2]
    d.mkdir(parents=True, exist_ok=True)
    return d / f"{key}.json"


def _load(key: str):
    p = _path(key)
    if p.exists():
        return json.loads(p.read_text())
    return None


def _save(key: str, vec):
    p = _path(key)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(vec))
    tmp.replace(p)


def _call_openai(texts):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is not set and some texts are not in data/cache. "
            "Export the key once (see .env.example) to fill the cache."
        )
    delay = 2.0
    for attempt in range(8):
        r = httpx.post(
            f"{settings.OPENAI_BASE_URL}/embeddings",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": settings.EMBED_MODEL, "input": texts},
            timeout=60,
        )
        if r.status_code == 200:
            data = sorted(r.json()["data"], key=lambda d: d["index"])
            return [d["embedding"] for d in data]
        if r.status_code == 429 or r.status_code >= 500:
            wait = float(r.headers.get("retry-after", delay))
            time.sleep(wait + random.random())
            delay = min(delay * 2, 60)
            continue
        raise RuntimeError(f"OpenAI embeddings error {r.status_code}: {r.text[:300]}")
    raise RuntimeError("OpenAI embeddings: too many retries")


def embed_texts(texts):
    """Return one vector per text, using the cache first."""
    keys = [_key(t) for t in texts]
    out = [_load(k) for k in keys]
    missing = [i for i, v in enumerate(out) if v is None]
    for start in range(0, len(missing), BATCH):
        idx = missing[start:start + BATCH]
        vecs = _call_openai([texts[i] for i in idx])
        for i, v in zip(idx, vecs):
            _save(keys[i], v)
            out[i] = v
    return out


def embed_query(text: str):
    return embed_texts([text])[0]
