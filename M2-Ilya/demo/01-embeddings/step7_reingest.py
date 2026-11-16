"""Step 7. Idempotent re-ingest of one changed document: delete by source, then upsert.

DEMO_EXPLAIN=1 adds a "how to read this" note after every sub-step.
"""
import json
import re
import uuid

from rich.syntax import Syntax
from rich.table import Table

from lib import (CHANGED_SOURCE, COLLECTION, cache_note, changed_doc, check_collection, chunk_doc, console, embed, explain,
                 header, ids_for_source, load_corpus, points_count, qdrant, source_filter, to_points, STEP7_QUERIES)

header("Step 7. The document changed: how to re-ingest without piling up garbage",
       f"We change {CHANGED_SOURCE}: the reset link now lives 30 minutes, the last section (email change) is removed. "
       "The shared corpus on disk is not touched, the new version is built in memory.")
check_collection()

docs = load_corpus()
old_doc = next(d for d in docs if d.source == CHANGED_SOURCE)
old_chunks = chunk_doc(old_doc)
new_chunks = chunk_doc(changed_doc(docs))
old_vecs = embed([c.text for c in old_chunks])
new_vecs = embed([c.text for c in new_chunks])

log: list[tuple[str, int, str]] = []


def upsert(points: list[dict]) -> None:
    qdrant("PUT", f"/collections/{COLLECTION}/points?wait=true", {"points": points})


def delete_source(source: str) -> None:
    body = {"filter": source_filter(source)}
    console.print(f"  [cyan]POST /collections/{COLLECTION}/points/delete?wait=true[/cyan]  {json.dumps(body)}")
    qdrant("POST", f"/collections/{COLLECTION}/points/delete?wait=true", body)


def record(step: str, version: str, ids: str, delete_first: str, note: str) -> None:
    n = points_count()
    minutes = reset_minutes()
    email = "yes" if EMAIL_SECTION in email_hits() else "no"
    log.append((step, version, ids, delete_first, n, minutes, email, note))
    console.print(f"  points in the collection: [bold]{n}[/bold], of which from {CHANGED_SOURCE}: {len(ids_for_source(CHANGED_SOURCE))}")
    console.print(f"  search says the reset link is valid for: [bold]{minutes}[/bold] · "
                  f"removed section in the top 3 for the email question: [bold]{email}[/bold]\n")


EMAIL_SECTION = "Changing the account email address"


def reset_minutes() -> str:
    """What the collection now says about the reset link: the minutes in the top hit for the reset question."""
    q = embed([STEP7_QUERIES[0]])[0].tolist()
    pts = qdrant("POST", f"/collections/{COLLECTION}/points/query",
                 {"query": q, "limit": 1, "with_payload": True})["result"]["points"]
    m = re.search(r"valid for \**(\d+) minutes", pts[0]["payload"]["content"]) if pts else None
    return f"{m.group(1)} min" if m else "not found"


def email_hits() -> str:
    """Does the collection still answer about the section we deleted?"""
    q = embed([STEP7_QUERIES[1]])[0].tolist()
    pts = qdrant("POST", f"/collections/{COLLECTION}/points/query",
                 {"query": q, "limit": 3, "with_payload": True})["result"]["points"]
    return ", ".join(p["payload"]["content"].split("\n", 1)[0].split(" > ", 1)[-1] for p in pts)


console.print(f"Old version: {len(old_chunks)} chunks, new: {len(new_chunks)} chunks. {cache_note()}\n")

changes = Table(title=f"What changed in {CHANGED_SOURCE}: chunk by chunk, old version → new version")
changes.add_column("chunk = id")
changes.add_column("section")
changes.add_column("old → new")
for i in range(max(len(old_chunks), len(new_chunks))):
    old = old_chunks[i] if i < len(old_chunks) else None
    new = new_chunks[i] if i < len(new_chunks) else None
    if old and not new:
        status = "[red]removed: no chunk with this number in the new version[/red]"
    elif new and not old:
        status = "[green]added[/green]"
    elif old.text == new.text:
        status = "[dim]same text[/dim]"
    elif "60 minutes" in old.text and "30 minutes" in new.text:
        status = "[yellow]changed: reset link 60 → 30 minutes[/yellow]"
    else:
        status = "[yellow]text changed[/yellow]"
    changes.add_row(f"{CHANGED_SOURCE}#{i}", (old or new).heading, status)
console.print(changes)
console.print("  The id is uuid5 of “file#number”, so a chunk keeps its id when its number stays the same. "
              f"An upsert of the new version overwrites #0–#{len(new_chunks) - 1}; "
              f"#{len(old_chunks) - 1} has no new chunk to overwrite it, so only a delete removes it.\n")
explain([
    "Real documents change. When one changes, its chunks in the database must be replaced, and the replacement must "
    "leave no copies and no leftovers. This step tries the wrong ways and the right one on one document.",
    f"The change: in {CHANGED_SOURCE} the reset link now lives 30 minutes instead of 60, and the last section "
    f"('Changing the account email address') is removed. So the new version has {len(new_chunks)} chunks, "
    f"the old one {len(old_chunks)}.",
    "After each sub-step the script prints the number of points (in the whole collection and from this document) "
    "and what search now says: the reset-link minutes in the top hit (60 = old text, 30 = new) and whether the "
    "removed email section still comes back. The last sub-step restores the original, so steps 6 and 7 can be rerun.",
])

console.print("[bold]7.1 Initial state[/bold] (after step 5)")
baseline = points_count()
record("7.1 initial", "old", "stable", "–", "after step 5")

console.print("[bold]7.2 Repeated upsert of the same document with the same ids[/bold] (uuid5 of source#index)")
upsert(to_points(old_chunks, old_vecs))
record("7.2 same ids again", "old", "stable", "no", "idempotent: overwritten")
explain([
    "7.2 loads the same 7 chunks again with the same ids (uuid5 of 'file#number', step 5). Upsert finds each id "
    "and overwrites the point, so the count does not change.",
    "This property is called idempotent: running the load twice gives the same result as running it once. "
    "A pipeline that is rerun after a crash or on a schedule needs it.",
])

console.print("[bold]7.3 And if the ids were random[/bold] (uuid4 on every run)")
upsert(to_points(old_chunks, old_vecs, ids=[str(uuid.uuid4()) for _ in old_chunks]))
record("7.3 random ids", "old", "random", "no", f"+{len(old_chunks)} duplicates")
q = embed([STEP7_QUERIES[0]])[0].tolist()
pts = qdrant("POST", f"/collections/{COLLECTION}/points/query", {"query": q, "limit": 3, "with_payload": True})["result"]["points"]
console.print(f"  top-3 for \"{STEP7_QUERIES[0]}\": "
              + " | ".join(f"{p['payload']['content'].split(chr(10), 1)[0].split(' > ', 1)[-1]} ({p['score']:.4f})" for p in pts))
console.print("  [dim]The same chunk twice: fewer distinct facts are left in the top-5 for the model.[/dim]")
console.print("  Fixing it: delete everything by the source filter and load again.")
delete_source(CHANGED_SOURCE)
upsert(to_points(old_chunks, old_vecs))
record("7.3 fix: delete + upsert", "old", "stable", "yes", "duplicates gone")
explain([
    f"7.3 loads the same chunks with random ids (uuid4). Qdrant does not know they are the same text: new ids = "
    f"new points, +{len(old_chunks)}.",
    "The search shows the harm: the same chunk comes back twice with the same score. The model gets two copies of "
    "one fact and one fact fewer in its top results.",
    "The fix: the delete request with a filter on metadata.source removes every chunk of this document in one call "
    "(it uses the payload index from step 5.2); then the chunks are loaded again with stable ids.",
])

console.print(f"[bold]7.4 New version of the document, upsert WITHOUT deletion[/bold] ({len(new_chunks)} chunks on top of {len(old_chunks)})")
upsert(to_points(new_chunks, new_vecs))
record("7.4 new, no delete", "new", "stable", "no", "orphan inside")
expected = {c.id for c in new_chunks}
orphans = [i for i in ids_for_source(CHANGED_SOURCE) if i not in expected]
for oid in orphans:
    p = qdrant("POST", f"/collections/{COLLECTION}/points", {"ids": [oid], "with_payload": True})["result"][0]
    console.print(f"  [red]orphan[/red] {oid}: \"{p['payload']['content'].split(chr(10), 1)[0]}\" — this section no longer exists in the document")
console.print(f"  top-3 for \"{STEP7_QUERIES[1]}\": {email_hits()}")
console.print("  [dim]The number of points did not change, so the problem is invisible by count. The agent will quote the deleted section.[/dim]\n")
explain([
    f"7.4 loads the new version ({len(new_chunks)} chunks) over the old one ({len(old_chunks)}) without deleting "
    f"first. Chunks #0-#{len(new_chunks) - 1} keep their ids and are overwritten with the new text (30 minutes). "
    f"Old chunk #{len(old_chunks) - 1} has no new counterpart, so nothing overwrites it: it stays in the database.",
    "Such a point is called an orphan: its section no longer exists in the document, but search still finds it. "
    "The question about changing the email still returns the deleted section first.",
    f"The count is still {baseline}, the same as before: you cannot see this bug by counting points. "
    "It shows only when you compare the ids in the database with the ids the current document should produce.",
])

console.print("[bold]7.5 The right way: delete by source, then upsert the new version[/bold]")
delete_source(CHANGED_SOURCE)
upsert(to_points(new_chunks, new_vecs))
record("7.5 new, delete + upsert", "new", "stable", "yes", "equals the new document")
console.print(f"  top-3 for \"{STEP7_QUERIES[1]}\": {email_hits()}\n")
explain([
    "7.5 is the right recipe: delete every chunk of the document by the source filter, then upsert the new version. "
    f"Now the document has {len(new_chunks)} chunks and the collection {baseline - len(old_chunks) + len(new_chunks)} "
    "points: one fewer, as it should be.",
    "The email question no longer finds the deleted section: the top-3 are the nearest remaining chunks. "
    "With no answer in the base, the agent should now refuse instead of quoting an outdated text.",
    "Between the delete and the upsert the document is briefly missing from search. For one document that is "
    "fine; switching a whole collection without a gap is a production topic (blue-green, in the lecture).",
])

console.print("[bold]7.6 Restoring the original version[/bold] so that step 6 matches the RUNBOOK again")
delete_source(CHANGED_SOURCE)
upsert(to_points(old_chunks, old_vecs))
record("7.6 rollback", "old", "stable", "yes", "as after step 5")

t = Table(title="Summary: what each way of reloading leaves in the collection")
t.add_column("step")
t.add_column("document")
t.add_column("ids")
t.add_column("delete first")
t.add_column("points", justify="right")
t.add_column("diff", justify="right")
t.add_column("reset link")
t.add_column("email section found")
t.add_column("what happened")
for step, version, ids, delete_first, n, minutes, email, note in log:
    t.add_row(step, version, ids, delete_first, str(n), f"{n - baseline:+d}", minutes, email, note)
console.print(t)
explain([
    "One row per sub-step: which version was loaded, with which ids, whether the document's points were deleted "
    "first; then the point count, its difference from the start, and what search answers.",
    "The new version is right only in the row where all three agree: 30 minutes, no email section, 146 points.",
    "Only two rows change the count: random ids (+duplicates) and the correct new version (-1, the removed section). "
    "The dangerous row is 'new version without delete': +0, looks perfect, holds an orphan.",
    "7.6 put the original document back, so the collection is again as after step 5 and the RUNBOOK numbers match.",
])
console.print("Rule for the homework: id = uuid5(source#index) makes upsert idempotent, and delete by source before "
              "upsert removes the leftovers when a document got shorter.")
console.print(Syntax(json.dumps({"filter": source_filter(CHANGED_SOURCE)}), "json", theme="ansi_dark"))
