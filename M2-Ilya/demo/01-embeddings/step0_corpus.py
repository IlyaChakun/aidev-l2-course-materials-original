"""Step 0. The corpus and the golden set: what search works over, and the answer key it is measured against.

No Qdrant and no API: only the files in ../_shared. DEMO_EXPLAIN=1 adds a "how to read this" note after every table.
"""
from collections import Counter

from rich.table import Table

from lib import (CORPUS_DIR, GOLDEN_FILE, STEP0_FACTS, TRAP_TOPICS, console, explain, header, load_corpus, load_golden,
                 n_tokens)

header("Step 0. The corpus and the golden set",
       "Before any search: the documents the agent can know, and the questions with marked answers we will measure "
       "it on. Steps 1-4 do not need Qdrant either.")

docs = load_corpus()
tokens = {d.source: n_tokens(d.body) for d in docs}

# 0.1 What the corpus is made of
console.print(f"[bold]0.1 The corpus[/bold]  [cyan]{CORPUS_DIR.parent.name}/{CORPUS_DIR.name}/*.md[/cyan]")
t = Table(title="Documents by section (the 'section' key of the front matter)")
t.add_column("section")
t.add_column("documents", justify="right")
t.add_column("tokens", justify="right")
t.add_column("for example")
by_section = Counter(d.section for d in docs)
for section, n in by_section.most_common():
    own = [d for d in docs if d.section == section]
    t.add_row(section, str(n), f"{sum(tokens[d.source] for d in own):,}".replace(",", " "),
              ", ".join(d.source.removesuffix(".md") for d in own[:2]) + (", ..." if n > 2 else ""))
t.add_section()
t.add_row("total", str(len(docs)), f"{sum(tokens.values()):,}".replace(",", " "), "", style="bold")
console.print(t)
sample = docs[0]
front = (CORPUS_DIR / sample.source).read_text(encoding="utf-8").split("\n---\n", 1)[0] + "\n---"
console.print(f"Front matter of {sample.source} (the file name becomes 'source'):", style="dim")
console.print(front, markup=False, highlight=False)
console.print()
explain([
    "The corpus is everything the agent can know. If a fact is not in these files, a correct answer is "
    "'not covered', no matter how good the search is.",
    f"Here: {len(docs)} English documents of a fictional SaaS help center, {sum(tokens.values()):,} tokens, written "
    "for one role, the first-line support operator. The homework asks for about 15 documents and 50-100 thousand "
    "tokens, assembled for the role in your project that needs search.",
    "Every document starts with front matter: title, section, date. Together with the file name (source) they become "
    "the payload of every chunk in step 5, and 'source' is what recall counts in step 8.",
])

# 0.2 The two rules that make the corpus measurable
console.print("[bold]0.2 Two corpus rules[/bold] from ../_shared/corpus_spec.md, checked on the files")
texts = {d.source: d.body.lower() for d in docs}
homes = {}
t = Table(title="Rule 1: one fact lives in one document")
t.add_column("fact")
t.add_column("text searched")
t.add_column("documents that contain it")
for fact, needle in STEP0_FACTS:
    found = [s for s, body in texts.items() if needle.lower() in body]
    homes[fact] = found
    t.add_row(fact, needle, ", ".join(s.removesuffix(".md") for s in found) or "none",
              style="" if len(found) == 1 else "red")
console.print(t)
single = sum(len(f) == 1 for f in homes.values())
console.print(f"{single} of {len(homes)} facts sit in exactly one document.\n", style="dim")
mentions = {}
t = Table(title="Rule 2: some topics are kept out of the corpus on purpose, for the trap questions")
t.add_column("topic")
t.add_column("documents that mention it", justify="right")
for topic in TRAP_TOPICS:
    n = sum(topic.lower() in body for body in texts.values())
    mentions[topic] = n
    t.add_row(topic, str(n), style="" if n == 0 else "red")
console.print(t)
console.print(f"{sum(n == 0 for n in mentions.values())} of {len(mentions)} trap topics appear in no document.\n",
              style="dim")
seat_fact, seat_needle = STEP0_FACTS[1]
explain([
    f"Rule 1 is what makes a single right document possible: the {seat_fact} ('{seat_needle}') is only in "
    f"{', '.join(homes[seat_fact])}, so a question about it has one answer document and recall is unambiguous. "
    "If five documents repeat the same number, the golden set cannot say which one is 'right'.",
    f"Rule 2 makes the traps honest: {TRAP_TOPICS[0]} and {TRAP_TOPICS[1]} appear nowhere, so 'not covered' is the only "
    "correct answer to the trap questions, and a search that returns five chunks anyway (step 6) shows why "
    "the refusal has to come from the agent (step 10).",
    "In your own corpus nobody wrote such a spec; check the same two things by hand for the facts your golden "
    "questions ask about.",
])

# 0.3 The golden set: the answer key, written before the pipeline
golden = load_golden()
console.print(f"[bold]0.3 The golden set[/bold]  [cyan]{GOLDEN_FILE.parent.name}/{GOLDEN_FILE.name}[/cyan]")
t = Table(title="What is in it")
t.add_column("kind")
t.add_column("questions", justify="right")
t.add_column("example")
t.add_column("marked answer")
for kind in ("core", "multi", "trap"):
    qs = [q for q in golden if q["kind"] == kind]
    ex = qs[0]
    t.add_row(kind, str(len(qs)), ex["question"], ", ".join(ex["answer_docs"]) or "none: the agent must refuse")
console.print(t)
covered = {d for q in golden for d in q["answer_docs"]}
console.print(f"The marked answers cover {len(covered)} of {len(docs)} documents. "
              f"Origin of the questions: {golden[0]['origin']}.\n", style="dim")
explain([
    "A golden set is the answer key: questions with the right document marked by a person in advance. Steps 8-10 "
    "measure search and answers against it.",
    "Write it before building the search, otherwise the questions drift towards what the search already finds. "
    "Phrase questions the way users write ('the reset email never showed up'), not like headings ('Forgot password').",
    "core: one answer document; multi: the answer needs two documents (homework block A); trap: no answer in the "
    "corpus, used to test the refusal. Traps never count in recall: there is no right document to find.",
    "These questions were drafted by a model from the corpus; the homework asks to mark such questions and read "
    "them by eye. They tend to repeat the documents' words, so they are easier than real ones (step 8 shows it).",
])
console.print("Takeaway: the corpus is everything the agent can know, the golden set is the answer key; "
              "both are fixed before the first chunk is loaded.")
