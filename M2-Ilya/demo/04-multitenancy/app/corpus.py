"""Build per-tenant corpora from the shared Lumen docs and split them into chunks."""
import json
import re
import shutil
import uuid

from app import settings

POINT_NS = uuid.UUID("6f1c2a52-5b7e-4d3a-9a47-0e5d6b8c1f04")


def load_tenants():
    data = json.loads((settings.TENANTS_DIR / "tenants.json").read_text())
    return {k: v for k, v in data.items() if not k.startswith("_")}


def _add_groups(md: str, groups: str) -> str:
    # Insert 'groups:' into the YAML front matter of a shared doc.
    return md.replace("\n---\n", f"\ngroups: {groups}\n---\n", 1)


def build():
    """Write corpus/<tenant>/*.md. Returns {tenant: [paths]}."""
    tenants = load_tenants()
    if settings.CORPUS_DIR.exists():
        shutil.rmtree(settings.CORPUS_DIR)
    out = {}
    for tenant, cfg in tenants.items():
        tdir = settings.CORPUS_DIR / tenant
        tdir.mkdir(parents=True)
        paths = []
        for name in cfg["base_docs"]:
            md = (settings.SHARED_CORPUS / f"{name}.md").read_text()
            for old, new in cfg["replace"]:
                md = md.replace(old, new)
            md = _add_groups(md, "all")
            p = tdir / f"{name}.md"
            p.write_text(md)
            paths.append(p)
        for src in sorted((settings.TENANTS_DIR / tenant).glob("*.md")):
            p = tdir / src.name
            shutil.copy(src, p)
            paths.append(p)
        out[tenant] = paths
    return out


_FM = re.compile(r"^---\n(.*?)\n---\n", re.S)


def parse_doc(path):
    text = path.read_text()
    m = _FM.match(text)
    meta = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        meta[k.strip()] = v.strip()
    body = text[m.end():]
    return meta, body


def chunk_doc(tenant, product, path):
    """Split by H2. The H1 intro becomes its own chunk. Each chunk gets a short
    contextual header (product | title | section) so it is self-describing."""
    meta, body = parse_doc(path)
    groups = [g.strip() for g in meta.get("groups", "all").split(",")]
    doc_id = path.stem
    parts = re.split(r"^## ", body, flags=re.M)
    sections = [("Introduction", re.sub(r"^# .*\n", "", parts[0]).strip())]
    for p in parts[1:]:
        head, _, rest = p.partition("\n")
        sections.append((head.strip(), rest.strip()))
    chunks = []
    for i, (sec, txt) in enumerate(s for s in sections if s[1]):
        chunks.append({
            "id": str(uuid.uuid5(POINT_NS, f"{tenant}/{doc_id}/{i}")),
            "tenant_id": tenant,
            "groups": groups,
            "doc_id": doc_id,
            "title": meta["title"],
            "section": sec,
            "chunk": i,
            "text": f"{product} | {meta['title']} | {sec}\n\n{txt}",
        })
    return chunks


def all_chunks():
    tenants = load_tenants()
    chunks = []
    for tenant, cfg in tenants.items():
        for path in sorted((settings.CORPUS_DIR / tenant).glob("*.md")):
            chunks.extend(chunk_doc(tenant, cfg["product"], path))
    return chunks
