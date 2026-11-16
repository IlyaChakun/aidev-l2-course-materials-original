"""Same tenant (acme), same question, two users: support (groups=all) vs finance (all+finance)."""
import re

import httpx

from app import settings

Q = "What is the floor price for the Business plan and is there a partner discount code?"
CODE = re.compile(r"\b(?:ACME|GLOBEX|INITECH)-[A-Z]+-\d{4}\b")

for token in ("tok-acme-support", "tok-acme-finance"):
    d = httpx.get(f"{settings.API_URL}/search", params={"q": Q, "k": 3},
                  headers={"Authorization": f"Bearer {token}"}, timeout=60).json()
    print(f"{token}: groups={d['principal']['groups']}")
    print(f"  filter: {d['qdrant_filter']}")
    for h in d["hits"]:
        codes = sorted(set(CODE.findall(h["text"])))
        print(f"  - {h['tenant_id']} {h['doc_id']} / {h['section']} groups={h['groups']}"
              + (f" CODE: {', '.join(codes)}" if codes else ""))
    print()
