"""Ask the same question as an acme support user through a given endpoint and show
whose data came back. Usage: leak_demo.py --path /debug/search_unsafe|/search"""
import argparse
import re

import httpx

from app import settings

CODE = re.compile(r"\b(?:ACME|GLOBEX|INITECH)-[A-Z]+-\d{4}\b")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default="/search")
    ap.add_argument("--token", default="tok-acme-support")
    ap.add_argument("--q", default="Is there a discount code I can give a customer who asks for a discount?")
    ap.add_argument("-k", type=int, default=8)
    a = ap.parse_args()

    r = httpx.get(f"{settings.API_URL}{a.path}", params={"q": a.q, "k": a.k},
                  headers={"Authorization": f"Bearer {a.token}"}, timeout=60)
    r.raise_for_status()
    data = r.json()
    me = data["principal"]
    print(f"endpoint : {a.path}")
    print(f"caller   : tenant={me['tenant']} groups={me['groups']}")
    print(f"question : {a.q}")
    print(f"filter   : {data['qdrant_filter']}")
    print()
    foreign = 0
    for i, h in enumerate(data["hits"], 1):
        own = h["tenant_id"] == me["tenant"]
        allowed = bool(set(h["groups"]) & set(me["groups"]))
        mark = "own" if own and allowed else ("FOREIGN TENANT" if not own else "NO ACCESS (group)")
        foreign += not (own and allowed)
        codes = sorted(set(CODE.findall(h["text"])))
        print(f"{i}. [{mark:14}] {h['tenant_id']:8} {h['doc_id']} / {h['section']}  score={h['score']}"
              f"  groups={h['groups']}" + (f"  CODE: {', '.join(codes)}" if codes else ""))
    print()
    print(f"result   : {foreign} of {len(data['hits'])} hits are not allowed for this user"
          + ("  -> LEAK" if foreign else "  -> isolated"))


if __name__ == "__main__":
    main()
