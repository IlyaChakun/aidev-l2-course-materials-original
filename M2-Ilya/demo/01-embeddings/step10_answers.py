"""Step 10. The answer: what the model does with the found chunks, and how to tell a search miss from a prompt miss.

Four golden questions go through the hybrid search and a chat model with a "facts only, cite or refuse" prompt.
Answers are cached like the embeddings. DEMO_EXPLAIN=1 adds a "how to read this" note after every question.
"""
import re

from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from lib import (CHAT_MODEL, CHAT_STATS, COLLECTION, STEP10_IDS, cache_note, chat, check_collection, console, embed,
                 explain, header, load_golden, search, short_json)

REFUSAL = "Not covered by the knowledge base."
SYSTEM = (
    "You answer customers of Lumen for the first-line support team. Use only the facts in the numbered passages. "
    "If the passages answer the question, answer briefly and end with one line 'Sources: <file names you used>'. "
    f"If they do not contain the answer, reply exactly: '{REFUSAL}' "
    "Do not refuse when the facts are there, even if you must compare a number from the question with a limit "
    "in the passages."
)

# What each question shows; printed only with DEMO_EXPLAIN=1, under its answer.
NOTES = {
    "q02": [
        "The easy case: the search returns the answer document first, the model copies the fact and names its source. "
        "This is what most of the golden set looks like (step 8: every core question is found).",
    ],
    "t01": [
        "The trap: Salesforce is nowhere in the corpus (step 0), yet the search still returns five chunks about "
        "connecting other things (step 6). Only the prompt stands between those chunks and a made-up answer.",
        "A refusal here is the prompt working, not the search: the database never says 'nothing relevant'.",
    ],
    "m01": [
        "50,000 rows is not written anywhere: the model has to compare it with the limits in the passages. The last "
        "sentence of the prompt exists because of this question: without it a strict 'only what is written' rule "
        "made the model refuse (Lab 05 shows that first prompt). A refusal rule can fail in both directions.",
    ],
    "m03": [
        "Two intents in one question: how serious is a 503 outage, and how fast support answers on Business. "
        "The outage words win both search branches (step 8: the SLA document is not in the top 10), so the model "
        "cannot cite what it never received.",
        "The fix is not in the prompt: split the question into two searches (query decomposition), an agent step (M3).",
        "Look at the Sources line too: here the model may write a passage number ('[4]') instead of a file name, so a "
        "script that counts cited files sees nothing. The citation format is part of what the run checks.",
    ],
}

header("Step 10. The answer: from found chunks to a cited answer or a refusal",
       f"Hybrid top 5 from \"{COLLECTION}\" → chat model {CHAT_MODEL} (temperature 0) with a 'facts only, cite or refuse' "
       "prompt. The same check as homework part 3, on four questions.")
check_collection()

golden = {q["id"]: q for q in load_golden()}
questions = [golden[i] for i in STEP10_IDS]
vecs = embed([q["question"] for q in questions])

# 10.1 The prompt: the rules the model gets, and the request as it is sent
console.print(f"[bold]10.1 The prompt[/bold]  [cyan]POST https://api.openai.com/v1/chat/completions[/cyan]")
console.print(Panel(SYSTEM, title="system message", title_align="left", width=110))
example = {"model": CHAT_MODEL, "temperature": 0, "messages": [
    {"role": "system", "content": SYSTEM},
    {"role": "user", "content": "Passages:\n\n[1] (source: <file>.md)\n<chunk text>\n...\n\nQuestion: <question>"}]}
console.print(Syntax(short_json(example, max_str=90), "json", theme="ansi_dark", word_wrap=True))
console.print()
explain([
    "The model never sees the database: it gets the chunks pasted into the message as numbered passages with their "
    "source file, then the question. Whatever the search returned is all the model knows.",
    "Three rules: answer only from the passages, end with a Sources line, or reply with the exact refusal phrase. "
    "An exact phrase makes the refusal countable by a script, as the homework's run table needs.",
    "temperature 0 makes the answer repeatable, and the answer is cached by the full request: the second run makes "
    "no API calls, like the embeddings.",
])


def label(p: dict) -> str:
    return f"{p['payload']['metadata']['source'].removesuffix('.md')} > {p['payload']['content'].split(chr(10), 1)[0].split(' > ', 1)[-1]}"


rows = []
for n, (q, vec) in enumerate(zip(questions, vecs), start=2):
    points = search("hybrid", q["question"], vec.tolist(), limit=5)      # ties broken by id: same prompt every run
    passages = "\n\n".join(f"[{i}] (source: {p['payload']['metadata']['source']})\n{p['payload']['content']}"
                           for i, p in enumerate(points, start=1))
    answer = chat([{"role": "system", "content": SYSTEM},
                   {"role": "user", "content": f"Passages:\n\n{passages}\n\nQuestion: {q['question']}"}])
    found = [d for d in q["answer_docs"] if d in [p["payload"]["metadata"]["source"] for p in points]]
    sources_line = next((line for line in answer.splitlines() if line.strip().lower().startswith("sources:")), "")
    cited = re.findall(r"[\w-]+\.md", sources_line)
    refused = REFUSAL.rstrip(".").lower() in answer.lower()
    if not q["answer_docs"]:
        verdict = "correct refusal" if refused else "answered a trap: made up"
    elif refused:
        verdict = "refused although the answer was found" if found else "refused: the search missed"
    elif len(found) < len(q["answer_docs"]):
        verdict = f"partial: the search found {len(found)} of {len(q['answer_docs'])} documents"
    elif not set(q["answer_docs"]) <= set(cited):
        verdict = f"cited {len(set(q['answer_docs']) & set(cited))} of {len(q['answer_docs'])} documents"
    else:
        verdict = "answered with sources"
    rows.append((q, found, cited, refused, verdict))

    console.print(f"[bold]10.{n} {q['id']} ({q['kind']})[/bold]: {q['question']}")
    t = Table(show_header=True, box=None, padding=(0, 1))
    t.add_column("#", justify="right", style="dim")
    t.add_column("hybrid top 5 (what the model receives)")
    for i, p in enumerate(points, start=1):
        hit = p["payload"]["metadata"]["source"] in q["answer_docs"]
        t.add_row(str(i), f"[green]{label(p)}[/green]" if hit else label(p))
    console.print(t)
    console.print(Panel(answer.strip(), title="the model's answer", title_align="left", width=110))
    needed = ", ".join(d.removesuffix(".md") for d in q["answer_docs"]) or "nothing (trap)"
    console.print(f"needed: {needed} · search found {len(found)} of {len(q['answer_docs'])} · "
                  f"cited: {', '.join(c.removesuffix('.md') for c in cited) or '—'} · refused: {'yes' if refused else 'no'} "
                  f"→ {verdict}\n", style="dim")
    explain(NOTES.get(q["id"], []), title="What this question shows")

t = Table(title="The run table of homework part 3, on four questions")
t.add_column("id")
t.add_column("kind")
t.add_column("search found", justify="right")
t.add_column("model cited", justify="right")
t.add_column("refused")
t.add_column("verdict")
for q, found, cited, refused, verdict in rows:
    ok = verdict in ("answered with sources", "correct refusal")
    t.add_row(q["id"], q["kind"], f"{len(found)} of {len(q['answer_docs'])}" if q["answer_docs"] else "—",
              f"{len(set(cited) & set(q['answer_docs']))} of {len(q['answer_docs'])}" if q["answer_docs"] else "—",
              "yes" if refused else "no", f"[green]{verdict}[/green]" if ok else f"[red]{verdict}[/red]")
console.print(t)
verdicts = [r[4] for r in rows]
console.print(f"{verdicts.count('answered with sources')} answered with sources, {verdicts.count('correct refusal')} "
              f"correct refusal, {len(verdicts) - verdicts.count('answered with sources') - verdicts.count('correct refusal')} "
              "with a problem.\n", style="dim")

# The worst question, diagnosed layer by layer: search, chunk, prompt.
bad = [r for r in rows if r[4] not in ("answered with sources", "correct refusal")]
worst = bad[0] if bad else min(rows, key=lambda r: len(r[2]))
q, found, cited, refused, verdict = worst
missing = [d for d in q["answer_docs"] if d not in found]
t = Table(title=f"Worst of the four: {q['id']} ({verdict}). Where did it break?")
t.add_column("layer")
t.add_column("question to ask")
t.add_column("here")
t.add_row("search", "are all needed documents in the top 5?",
          "no, missing: " + ", ".join(missing) if missing else "yes")
t.add_row("chunk", "does the returned chunk hold the fact, whole?",
          "cannot hold what was not returned" if missing else "open the green chunk and check the fact is in it")
t.add_row("prompt / model", "did the model use, cite or refuse correctly?",
          "follows from the search" if missing else ("refused with the facts present" if refused else
                                                     f"cited {len(set(cited) & set(q['answer_docs']))} of {len(q['answer_docs'])}"))
console.print(t)
explain([
    "The homework asks for 2-3 sentences of diagnosis for the worst question: chunk, search or prompt. Go top-down: "
    "a search miss explains everything below it, so check the search first (step 8 shows positions for all 15).",
    "If the search found the documents, open the chunks: an answer split across two chunks or buried in a long one "
    "is a chunking problem. If the chunk holds the fact and the answer is still wrong, it is the prompt or the model.",
    "The verdict column is mechanical (cited files against the golden set, the exact refusal phrase); a person still "
    "reads every answer, as the homework asks: a cited answer can still contain a wrong number.",
])
console.print("Takeaway: the model only knows what the search handed it; a refusal comes from the prompt, and a "
              "missing document cannot be fixed by the prompt.")
console.print(f"{cache_note()} · chat: from cache {CHAT_STATS['hits']}, API requests {CHAT_STATS['calls']}", style="dim")
