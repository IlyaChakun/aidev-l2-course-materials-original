# 2 · Solutions base

**Status:** `in-build` · **Waiting for:** none · **Blocks:** 3

## What it does

Collects policies, instructions and write-ups of past cases into a search corpus. The input is
the text of a request, and the output is the documents that apply to it, with the document and
section named. First-line Support answers with a link to the policy, not from the model's
memory.

## Why

140 pages of policies do not fit into a prompt. The link to the document is needed by the
on-call person too: a draft without a source they will re-check by hand anyway, and the time
gain disappears.

## Input and output

| | |
|---|---|
| **Input** | 61 documents in `corpus/kb/` plus an anonymized export of 480 closed requests |
| **Output** | The `retrieval/` module: corpus loading, search. `findSolutions(text, k)` returns documents and similar closed requests, each with a source and a similarity score |

Closed requests are indexed as a separate type: they have a different value, a precedent, not
a rule, and in the answer they are marked differently.

## Boundaries

- Escalation rules: not included, the document is short and goes straight into the
  Escalator's prompt.
- Automatic reindexing when documents are edited: not included, reload by hand.
- Separation by product: not included, there is one product.
- Answer generation: not included, that is feature 3.

## Done when

- [x] The corpus loads with one command, the number of chunks is printed to the console
- [x] A chunk has in its metadata the source, the type (policy or precedent) and the section
- [ ] On 15 test requests the needed policy is in the first three results
- [ ] A request that is not in the base gives an empty result, not the closest document by meaning
- [ ] Precedents and policies are distinguishable in the results
- [ ] A repeated load does not duplicate chunks

## Read before starting

- `corpus/kb/README.md`: what was collected and how the export was anonymized
- `../../roadmap.md`, block 2
- `spec.md` next to this file

## Open questions

- **Chunking of policies.** Redone twice. By section it comes out too coarse, by paragraph the
  context of the procedure is lost. Right now we are trying a section with overlap, the
  result is not decided.
- **Cutoff threshold.** Without a threshold, search always returns something, and Support
  answers from an irrelevant document. A threshold is needed, the value is not yet tuned.
- Fifteen test requests are too few. Expand when we reach the quality-check block.
