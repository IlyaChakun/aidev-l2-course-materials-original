"""Step 4. Chunking by headings with a ~400 token target (tiktoken cl100k_base).

DEMO_EXPLAIN=1 adds a "how to read this" note after every table.
"""
from collections import Counter

import numpy as np
from rich.panel import Panel
from rich.table import Table

from lib import _blocks, _sections, chunk_corpus, console, explain, header, load_corpus, n_tokens

header("Step 4. Chunking by headings",
       "Split by H2, target ~400 tokens (range 300-500), tables and code are never broken, "
       "each chunk gets a \"Title > Heading\" prefix.")

docs = load_corpus()
chunks = chunk_corpus(docs)
doc_tokens = [n_tokens(d.body) for d in docs]
lens = np.array([c.tokens for c in chunks])

t = Table(title="Corpus before and after chunking")
t.add_column("what", style="bold")
t.add_column("how many", justify="right")
t.add_row("documents", str(len(docs)))
t.add_row("tokens in the corpus", f"{sum(doc_tokens):,}".replace(",", " "))
t.add_row("tokens per document: min / avg / max", f"{min(doc_tokens)} / {np.mean(doc_tokens):.0f} / {max(doc_tokens)}")
t.add_row("chunks", str(len(chunks)))
t.add_row("tokens per chunk: min / avg / max", f"{lens.min()} / {lens.mean():.0f} / {lens.max()}")
t.add_row("chunks in the 300-500 range", f"{((lens >= 300) & (lens <= 500)).sum()} of {len(chunks)}")
t.add_row("chunks shorter than 300", str((lens < 300).sum()))
t.add_row("chunks longer than 500", str((lens > 500).sum()))
console.print(t)
explain([
    "Why cut at all: one vector per whole document (about 2,000 tokens here) averages every topic in it, "
    "so a question about one detail matches the document only weakly. A chunk of one topic gives a sharp vector, "
    "and the model later gets a small, relevant piece of text instead of the whole document.",
    "tokens: units of the tokenizer cl100k_base (tiktoken), not words. On this corpus one word is about 1.2 tokens "
    "on average, so 400 tokens is roughly 320 words, about one section of a help page.",
    "The chunker in lib.py (chunk_doc) works in three passes: (1) one H2 section (a '## ' heading) = one candidate "
    "chunk, H3 stays inside it; (2) a section over 500 tokens is split at paragraph, table or code-block borders, "
    "never inside a table or code block, and a short last block is repeated at the start of the next piece (overlap); "
    "(3) neighbouring small sections (under 300) are merged while the result stays within 500.",
    f"Read the table as 'config versus fact': the config says 300-500, the fact is {((lens >= 300) & (lens <= 500)).sum()} "
    f"of {len(chunks)} chunks in range, {(lens < 300).sum()} shorter and {(lens > 500).sum()} longer. "
    "The maximum is never exceeded; the minimum is a wish, not a guarantee.",
])

# Histogram in text: the config says 300-500, the fact is what we print.
bins = [0, 200, 250, 300, 350, 400, 450, 500, 10_000]
labels = ["< 200", "200-249", "250-299", "300-349", "350-399", "400-449", "450-500", "> 500"]
counts = Counter(np.digitize(lens, bins[1:-1], right=False))
t = Table(title="Chunk length distribution (tokens)")
t.add_column("range")
t.add_column("chunks", justify="right")
t.add_column("")
for i, lab in enumerate(labels):
    n = counts.get(i, 0)
    t.add_row(lab, str(n), "#" * n)
console.print(t)
explain([
    "A text histogram: each '#' is one chunk. Most chunks land near the 400 target; nothing passes 500.",
    "The left tail (under 300) comes from short sections that could not be merged. Those chunks carry less context, "
    "so it is worth seeing them, not assuming the config holds.",
])

# Homework checks: how much overlap there really is, and that no table or code block was cut.
atomic = {"tables": [], "code blocks": []}
long_sections = 0
for d in docs:
    for _, text in _sections(d.body):
        long_sections += n_tokens(text) > 484
        for block in _blocks(text):
            kind = "code blocks" if block.lstrip().startswith("```") else "tables" if block.lstrip().startswith("|") else None
            if kind:
                atomic[kind].append((d.source, block))
overlapped = [c for c in chunks if c.overlap]
t = Table(title="Overlap and blocks that must stay whole (homework requirements)")
t.add_column("check", style="bold")
t.add_column("fact", justify="right")
t.add_row("sections longer than 500, split into pieces", str(long_sections))
t.add_row("chunks that start with overlap", "; ".join(f"{c.heading} ({c.overlap} tok)" for c in overlapped) or "none")
t.add_row("overlap share of all chunk tokens", f"{sum(c.overlap for c in chunks) / lens.sum():.2%}")
for kind, blocks in atomic.items():
    whole = sum(any(c.source == src and block in c.text for c in chunks) for src, block in blocks)
    t.add_row(f"{kind} kept whole in one chunk", f"{whole} of {len(blocks)}")
console.print(t)
explain([
    "The homework asks for 10-15% overlap and for tables and code that are never split. This table checks both "
    "on the real chunks instead of trusting the config.",
    f"Overlap here fires only where one long section is cut into pieces: {long_sections} sections, so "
    f"{len(overlapped)} chunks. Elsewhere a chunk border is a heading, and a new heading starts a new topic: "
    "repeating the end of the previous topic would add noise, not context. So the overall share is close to zero.",
    "In the homework report write what you actually have, for example 'overlap ~12% on split sections, none at "
    "heading borders'. Step 9 measures a 12% overlap on 300-token chunks, where splits are frequent.",
    "Tables and code: every one of them sits whole inside one chunk. A table cut in half loses its header row, "
    "and the second half no longer says what its numbers mean.",
])

short = [c for c in chunks if c.tokens < 250]
if short:
    t = Table(title="Shortest chunks: why the config is not the fact")
    t.add_column("chunk")
    t.add_column("tokens", justify="right")
    for c in sorted(short, key=lambda c: c.tokens):
        t.add_row(c.label, str(c.tokens))
    console.print(t)
    console.print("A short section did not merge with its neighbor: together they would exceed 500. "
                  "That is fine, but you need to see it, not assume it.\n", style="dim")
    explain([
        "The merge rule (pass 3) joins two neighbouring sections only if one of them is under 300 and the joined text "
        "stays within 500. A 155-token FAQ next to a 400-token section would make 555, so it stays alone.",
        "Note the FAQ chunks here: 'Frequently asked questions' is a heading that says nothing about the topic. "
        "The 'Title > Heading' prefix shown next fixes that.",
    ])

# One chunk in full: the prefix is what makes "Frequently asked questions" findable.
sample = next(c for c in chunks if c.source == "account-and-login.md" and c.heading == "Forgot password")
console.print(Panel(sample.text, title=f"{sample.label}  ·  {sample.tokens} tokens  ·  chunk #{sample.index}",
                    subtitle="the first line is the \"Title > Heading\" prefix, it also goes into the embedding", width=110))
explain([
    f"This is one chunk exactly as it is embedded and stored: {sample.tokens} tokens, chunk #{sample.index} of its "
    "document. The answer to 'how long is the reset link valid' (60 minutes) is inside.",
    f"First line: '{sample.text.splitlines()[0]}'. The chunker adds it to every chunk: document title + section "
    "heading. Without it a chunk would not say which product page it comes from; with it both the vector and BM25 "
    "see the words 'Account', 'Login', 'Forgot password'.",
    "The chunker reserves 16 tokens for this prefix, so the final chunk still fits within 500.",
])

t = Table(title="Chunks of one document: account-and-login.md")
t.add_column("#", justify="right")
t.add_column("heading (first H2 in the chunk)")
t.add_column("tokens", justify="right")
for c in chunks:
    if c.source == "account-and-login.md":
        t.add_row(str(c.index), c.heading, str(c.tokens))
console.print(t)
own = [c for c in chunks if c.source == "account-and-login.md"]
merged_own = ", ".join(f"#{c.index} '{c.heading}' (+{c.text.count(chr(10) + '## ')} section)"
                       for c in own if "\n## " in c.text)
explain([
    f"One document, {len(own)} chunks. 'heading' is the first H2 in the chunk; 'Intro' is the text before the first "
    "H2. Most sections are 300-500 tokens on their own and became one chunk each. "
    + (f"Merged by pass 3: {merged_own}: a short piece was joined with its neighbour, the second heading stays "
       "inside the text." if merged_own else "Nothing had to be merged."),
    "# is the chunk number inside the document, counted from 0. Together with the file name it gives a stable "
    f"identity: '{own[0].source}#{own[0].index}'. Step 5 turns it into the point id, so loading the same chunk again "
    "overwrites it instead of adding a copy.",
    f"Remember chunk #{own[-1].index} ('{own[-1].heading}'): step 7 deletes this section from the document and shows "
    "what happens to the database.",
])
console.print("The chunk number within the document will be needed in step 5: id = uuid5(source#index).")
