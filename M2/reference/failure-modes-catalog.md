# RAG failure modes catalog · Module 2 handout · date 10.08.2026

Twenty-six ways a search system over your own data breaks in production. Grouped by the layer where the
failure originates: data, retrieval, operations, security, quality and cost, organization.

**How to use it.** Two scenarios. First: a pre-launch review checklist - go through the list and, for
each item, answer "this will not happen to us, because...". Second: a frame for incident analysis -
when the system "answers wrongly", start by classifying the failure against this list rather than
by fiddling with the prompt. Most items fail **silently**: the system returns a confident answer,
and without a separate check nothing will be visible.

---

## Data and preparation

1. Bad parsing: every embedding downstream is poisoned.
2. A table is cut by the chunker: the wrong row ends up in the context.
3. Exact numbers and codes are not found: embeddings do not encode them.
4. Loss of links between chunks: results made of unrelated pieces.

## Retrieval

5. A multi-hop question: static RAG fundamentally cannot handle it.
6. Semantic collapse on a homogeneous corpus from ~10 thousand documents.
7. Pure vector without lexical: silent misses on part numbers, error codes, API names.
8. Post-filter instead of pre-filter: an empty result that looks like "there is no data in the base".
9. The filter is applied only to the vector branch of the hybrid: the lexical branch drags in other tenants' documents.

## Operations

10. A stale chunk ranks higher than the current one.
11. A deleted document keeps being retrieved.
12. Near-duplicates after re-running a job: contradictory evidence.
13. Changing the embedder without reindexing: incompatible spaces in one index.
14. The preloaded-context cache is not invalidated after a document edit.

## Security

15. Cross-tenant leakage due to missing permissions in retrieval.
16. Injection through a retrieved document.
17. Knowledge base poisoning with a few documents.
18. Vectors outside the protection perimeter of the source data.

## Quality and cost

19. Green metrics while users leave: the wrong thing is being measured.
20. Judge model drift when the LLM is updated.
21. Out-of-domain questions that no golden set covers.
22. Correct, but too slow.
23. Correct, but too expensive: input token savings are eaten by growth in output.
24. Unstable output format: "every other time the answer is a table anyway".

## Organization

25. Nobody owns the knowledge base, documents go stale.
26. Business expectations of "100% accuracy" against a real ceiling of around 80-85%.

> On item 26: the 80-85% figure is practitioners' observation on their own evaluation sets,
> not the result of a controlled study. It works as an argument in a conversation with the business;
> it must not be presented as a measured fact.
