"""Multi-tenant search API.

Tenant and groups come only from the bearer token (see tenancy.py).
/search, /docs (POST, DELETE) and /pg/search are the safe paths.
/debug/search_unsafe reproduces the classic bug (no tenant filter) and is
mounted only when DEMO_UNSAFE_ENABLED=1.
"""
import re

from fastapi.responses import JSONResponse
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from app import corpus, pg, settings, sparse
from app.embeddings import embed_query, embed_texts
from app.tenancy import Principal, TenantScope, principal_from_bearer, unsafe_search

app = FastAPI(title="Multi-tenant KB search (demo 04)")


@app.exception_handler(RuntimeError)
def runtime_error(_, exc: RuntimeError):
    # Typical cause in the demo: a new query that is not in data/cache and no OPENAI_API_KEY.
    return JSONResponse(status_code=503, content={"error": str(exc)})


def current_principal(authorization: str | None = Header(default=None)) -> Principal:
    p = principal_from_bearer(authorization)
    if p is None:
        raise HTTPException(status_code=401, detail="missing or unknown bearer token")
    return p


def _hit(point):
    pl = point["payload"]
    return {
        "score": round(point["score"], 4),
        "tenant_id": pl["tenant_id"],
        "groups": pl["groups"],
        "doc_id": pl["doc_id"],
        "section": pl["section"],
        "text": pl["text"],
    }


@app.get("/health")
def health():
    return {"ok": True, "unsafe_endpoint": settings.DEMO_UNSAFE_ENABLED}


@app.get("/whoami")
def whoami(p: Principal = Depends(current_principal)):
    return {"user": p.user, "tenant": p.tenant, "groups": list(p.groups)}


@app.get("/search")
def search(q: str, k: int = Query(5, ge=1, le=20), p: Principal = Depends(current_principal)):
    # Any ?tenant_id=... in the URL is simply not a parameter here and is ignored.
    points, body = TenantScope(p).search(embed_query(q), k)
    return {"principal": {"tenant": p.tenant, "groups": list(p.groups)},
            "qdrant_filter": body["filter"], "hits": [_hit(x) for x in points]}


class NewDoc(BaseModel):
    # extra="ignore": a 'tenant_id' in the body is dropped, never trusted.
    model_config = ConfigDict(extra="ignore")
    doc_id: str
    title: str
    text: str
    groups: list[str] = ["all"]


@app.post("/docs")
def add_doc(doc: NewDoc, p: Principal = Depends(current_principal)):
    if not re.fullmatch(r"[a-z0-9-]{3,64}", doc.doc_id):
        raise HTTPException(400, "doc_id must be [a-z0-9-]{3,64}")
    if not set(doc.groups) <= set(p.groups):
        raise HTTPException(403, "cannot write a document for a group you are not in")
    chunk = {
        "id": str(corpus.uuid.uuid5(corpus.POINT_NS, f"{p.tenant}/{doc.doc_id}/0")),
        "tenant_id": p.tenant, "groups": doc.groups, "doc_id": doc.doc_id,
        "title": doc.title, "section": "Introduction", "chunk": 0,
        "text": f"{doc.title}\n\n{doc.text}",
    }
    [vec] = embed_texts([chunk["text"]])
    point = {"id": chunk.pop("id"), "payload": chunk,
             "vector": {"dense": vec, "bm25": sparse.doc_vector(chunk["text"])}}
    TenantScope(p).upsert([point])
    return {"upserted": 1, "tenant_id": p.tenant, "doc_id": doc.doc_id}


@app.delete("/docs/{doc_id}")
def delete_doc(doc_id: str, p: Principal = Depends(current_principal)):
    deleted, flt = TenantScope(p).delete_doc(doc_id)
    return {"tenant_id": p.tenant, "doc_id": doc_id, "deleted_points": deleted, "qdrant_filter": flt}


@app.get("/pg/search")
def pg_search(q: str, k: int = Query(5, ge=1, le=20), p: Principal = Depends(current_principal)):
    rows = pg.search(p.tenant, p.groups, embed_query(q), k)
    for r in rows:
        r["score"] = round(float(r["score"]), 4)
    return {"principal": {"tenant": p.tenant, "groups": list(p.groups)}, "hits": rows}


if settings.DEMO_UNSAFE_ENABLED:
    @app.get("/debug/search_unsafe")
    def search_unsafe(q: str, k: int = Query(5, ge=1, le=20),
                      p: Principal = Depends(current_principal)):
        # BUG (on purpose): the user is authenticated, but the tenant is never applied.
        points, body = unsafe_search(embed_query(q), k)
        return {"principal": {"tenant": p.tenant, "groups": list(p.groups)},
                "qdrant_filter": body.get("filter"), "hits": [_hit(x) for x in points]}
