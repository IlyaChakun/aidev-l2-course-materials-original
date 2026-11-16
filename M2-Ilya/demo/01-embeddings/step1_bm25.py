"""Step 1. How search worked before embeddings: inverted index + BM25 on 3 tiny docs.

DEMO_EXPLAIN=1 adds a "how to read this" note after every table, with the numbers worked out.
"""
import re

from rich.table import Table

from lib import BM25, EXPLAIN, STOPWORDS, console, explain, header, tokenize

DOCS = [
    "In Lumen, reset your password from the sign-in page. The reset link is valid for 60 minutes.",
    "Lumen error E-4031 means the card currency is not supported. Try another card or contact your bank.",
    "Export a Lumen report as CSV from the Reports page. Viewers cannot export reports. Export, export, export!",
]

header("Step 1. Search before embeddings: inverted index and BM25",
       "Pure Python, three tiny documents, no models.")

docs_tokens = [tokenize(d) for d in DOCS]
bm = BM25(docs_tokens)

t = Table(title="Documents and their tokens (lowercase, stop words removed)", show_lines=True)
t.add_column("id", justify="right")
t.add_column("text")
t.add_column("tokens")
t.add_column("length", justify="right")
for i, (d, toks) in enumerate(zip(DOCS, docs_tokens)):
    t.add_row(f"d{i}", d, " ".join(toks), str(len(toks)))
console.print(t)
console.print(f"Average document length avgdl = {bm.avgdl:.2f} tokens. The tokenizer keeps codes like E-4031 as a single word.\n")
dropped = [[w for w in re.findall(r"[a-z]+-\d+|\w+", d.lower()) if w in STOPWORDS] for d in DOCS]
explain([
    "tokenize() turns text into a list of words: lowercase, split on anything that is not a letter or digit "
    "(codes like e-4031 stay one word), then drop stop words.",
    *[f"Stop words dropped from d{i}: {' '.join(ws)}" for i, ws in enumerate(dropped)],
    "Stop words occur in every text, so they cannot tell documents apart. Side effect: 'sign-in' became 'sign', "
    "because 'in' is a stop word.",
    f"length = tokens left. avgdl = ({' + '.join(str(len(t)) for t in docs_tokens)}) / {len(DOCS)} = {bm.avgdl:.2f}; "
    "BM25 uses it later to compare each document with an average one.",
])

# Inverted index: term -> posting list. Show the interesting part.
t = Table(title="Inverted index: word → which documents (tf) and its IDF")
t.add_column("term")
t.add_column("posting list (document:tf)")
t.add_column("df", justify="right")
t.add_column("IDF", justify="right")
for term in sorted(bm.index, key=lambda x: (-len(bm.index[x]), x)):
    postings = bm.index[term]
    if term in {"reset", "password", "export", "e-4031", "card"} or len(postings) > 1:
        t.add_row(term, ", ".join(f"d{d}:{tf}" for d, tf in postings.items()), str(len(postings)), f"{bm.idf(term):.3f}")
console.print(t)
console.print("IDF = ln(1 + (N - df + 0.5) / (df + 0.5)). A word present in all documents weighs almost nothing, "
              "a rare word weighs a lot.\n", style="dim")
explain([
    "An inverted index stores 'word → documents' instead of 'document → words'. A query looks up only its own "
    "words and never reads the texts, which is why search stays fast on millions of documents.",
    "posting list: the documents that contain the word; the number after the colon is tf (term frequency), "
    "how many times the word occurs there. df (document frequency): in how many documents it occurs.",
    f"IDF is the weight of a word: the rarer, the heavier. Worked out with N = {bm.N} documents:",
    *[f"  df = {df} ('{term}'): ln(1 + ({bm.N} - {df} + 0.5) / ({df} + 0.5)) = "
      f"ln({1 + (bm.N - df + 0.5) / (df + 0.5):.3f}) = {bm.idf(term):.3f}"
      for term in ["lumen", "page", "export"] for df in [len(bm.index[term])]],
    "A word found in every document ('lumen') says almost nothing about which one you need; "
    "a word found in one document points straight at it.",
])

# Term saturation: TF-IDF grows linearly with tf, BM25 saturates at idf * (k1 + 1).
idf = bm.idf("export")
t = Table(title=f"Saturation: contribution of the word 'export' (IDF={idf:.3f}) at tf = 1..10, average-length document")
t.add_column("tf", justify="right")
t.add_column("TF-IDF (tf * idf)", justify="right")
t.add_column("BM25, k1=1.2", justify="right")
t.add_column("BM25, k1=2.0", justify="right")
for tf in [1, 2, 3, 5, 10]:
    t.add_row(str(tf), f"{tf * idf:.3f}",
              f"{BM25(docs_tokens, k1=1.2).term_score(tf, bm.avgdl, idf):.3f}",
              f"{BM25(docs_tokens, k1=2.0).term_score(tf, bm.avgdl, idf):.3f}")
console.print(t)
console.print(f"BM25 ceiling = IDF * (k1 + 1) = {idf * 2.2:.3f} at k1=1.2: the tenth occurrence of a word adds almost nothing. "
              "The parameter b=0.75 penalizes long documents.\n", style="dim")
explain([
    "The question: a query word occurs tf times in a document. How many points should the document get for it? "
    "Each row is one tf, each column is one way to count.",
    "TF-IDF = tf × IDF: 10 occurrences give 10 times the points. A document that repeats a word wins unfairly "
    "(keyword stuffing; d2 repeats 'export' on purpose).",
    "BM25 = IDF × tf × (k1 + 1) / (tf + k1) for a document of average length. "
    "Read tf / (tf + k1) as 'the share of the maximum already collected'. With k1 = 1.2:",
    *[f"  tf = {tf:>2}: {tf} / ({tf} + 1.2) = {tf / (tf + 1.2):.1%} of the maximum {idf * 2.2:.3f} "
      f"→ {idf * 2.2 * tf / (tf + 1.2):.3f}" for tf in [1, 2, 3, 5, 10]],
    f"The share never reaches 1, so the score never passes IDF × (k1 + 1) = {idf:.3f} × 2.2 = {idf * 2.2:.3f}: "
    "the first occurrence says 'this document is about export', the tenth adds nothing new.",
    f"k1 is a knob for how fast saturation comes: at 1.2 three occurrences already give "
    f"{3 / 4.2:.0%} of the maximum, at 2.0 the ceiling is higher ({idf * 3:.3f}) and repeats count a bit longer. "
    "1.2 is the Elasticsearch / Lucene default and the value used in the next table.",
])

QUERIES = [
    ("reset password link", "exact words → finds d0"),
    ("What does E-4031 mean?", "error code → finds d1"),
    ("Lumen export", "'lumen' is everywhere and weighs almost nothing"),
    ("can't log in", "no words in common → zero everywhere"),
    ("сбросить пароль", "another language → zero everywhere"),
]
t = Table(title="Queries → BM25 document scores")
t.add_column("query")
t.add_column("query tokens")
for i in range(len(DOCS)):
    t.add_column(f"d{i}", justify="right")
t.add_column("takeaway")
for q, note in QUERIES:
    s = bm.scores(q)
    t.add_row(q, " ".join(tokenize(q)), *[f"{x:.3f}" if x else "0" for x in s], note)
console.print(t)
explain([
    "Each row is one query; d0, d1, d2 are the document scores. The highest score wins, 0 means 'not found at all'.",
    "A document's score is the sum over the query words: a word missing from the document adds 0, "
    "a word present adds IDF × tf × (k1 + 1) / (tf + norm), as in the saturation table.",
    f"New here: the document length. norm = k1 × (1 - b + b × length / avgdl), b = {bm.b}. "
    "A longer document gets a bigger norm and a smaller score for the same word: one mention in a short text means more.",
    "The breakdown below shows where every number in the table comes from.",
])

if EXPLAIN:
    t = Table(title="Breakdown: the points each query word brings to each document (k1 = 1.2, b = 0.75)")
    t.add_column("query")
    t.add_column("word")
    t.add_column("IDF", justify="right")
    for i in range(len(DOCS)):
        t.add_column(f"d{i} (length {len(docs_tokens[i])})", justify="right")
    for q, _ in QUERIES:
        for n, term in enumerate(tokenize(q)):
            postings = bm.index.get(term, {})
            if not postings:
                cells = ["not in the index"] + [""] * (len(DOCS) - 1)
                t.add_row(q if n == 0 else "", term, "", *cells)
                continue
            idf_t = bm.idf(term)
            cells = [f"tf={postings[i]} → {bm.term_score(postings[i], len(docs_tokens[i]), idf_t):.3f}"
                     if i in postings else "-" for i in range(len(DOCS))]
            t.add_row(q if n == 0 else "", term, f"{idf_t:.3f}", *cells)
        t.add_section()
    console.print(t)
    explain([
        "reset password link: all three words are only in d0. 'reset' occurs twice yet brings less than double "
        "'password': that is saturation.",
        "What does E-4031 mean?: 'what' and 'does' are stop words. 'mean' is not in the index, because d1 says 'means' "
        "and this tokenizer does no stemming (it does not reduce words to a common root); Elasticsearch analyzers do. "
        "The code alone is enough to find d1.",
        "Lumen export: 'lumen' is in every document and brings crumbs, a bit more to the shorter d0 than to the longer d2 "
        "(the length penalty b). 'export' decides: five occurrences bring about 1.7, not 4.9 as TF-IDF would give.",
        "can't log in: 'can', 't' and 'in' are stop words, only 'log' is left, and no document contains it. "
        "By meaning d0 (reset password) is the answer, but BM25 sees words, not meaning.",
        "сбросить пароль: Russian words, English documents, no word in common.",
    ], title="What the breakdown shows")

console.print("\nTakeaway: BM25 matches words. It reliably finds an error code, but not a paraphrase or another language.")
