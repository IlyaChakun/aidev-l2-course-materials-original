# 2 · Editorial policy corpus

**Status:** `in-build` · **Waits for:** none · **Blocks:** 3

## What it does

Assembles the editorial policy and tone-of-voice requirements into a searchable corpus. The input
is a paragraph of a draft, the output is the rules that apply to it, with the document and
section indicated. The Fact checker then writes the comment not as "doesn't sound like us" but as
"section 4.2 forbids evaluative adjectives in news".

## Why

A 90-page editorial policy does not fit in a prompt, and without it the Fact checker verifies only
facts. A link to a specific document is also needed by the author: a comment without a source is
perceived as a matter of taste and causes an argument instead of a fix.

## Input and output

| | |
|---|---|
| **Input** | 34 editorial policy documents in Markdown, folder `corpus/style/` |
| **Output** | The `retrieval/` module: corpus loading, search. The function `find_rules(text, k)` returns a list of rules, each with the text, document, section and a similarity score |

## Boundaries

- SEO rules: out of scope, they are short and go straight into the SEO specialist's prompt.
- Automatic corpus update when documents are edited: out of scope, manual reload with one
  command.
- Filtering by publication section: out of scope, there is one corpus for everything.
- Checking facts against external sources: out of scope, that is part of feature 3.

## Done when

- [x] The corpus loads with one command, the number of fragments is printed to the console
- [x] Each fragment has the document name and the section heading in its metadata
- [ ] On ten test paragraphs, search returns the correct rule in the top three results
- [ ] A paragraph with no applicable rules gives an empty result, not a random rule
- [ ] Reloading the corpus does not duplicate fragments

## Read before starting

- `corpus/style/README.md`: where the documents were collected from and what has already been fixed in them
- `../../roadmap.md`, block 2
- The chunking note: `spec.md` next to this file

## Open questions

- **Chunking.** The editorial policy documents are short and structured, so chunking by section
  looks more logical than chunking by size. Being checked on ten test paragraphs, the result is
  not decided yet.
- **Embedding model.** The first suitable one was taken. We did not compare, we will come back if
  the search quality fails the check.
- The ten test paragraphs were picked by hand and that is few. Expand them when we get to the
  quality evaluation block.
