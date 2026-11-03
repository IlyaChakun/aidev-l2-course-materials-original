# Module 2 reference

Six self-contained documents on production RAG: you can read them in any order and keep them
open while you work on your own project. Everything was collected on 10-21.08.2026; figures and tool
statuses go stale fast, so check any figure against the primary source before you make a decision.

| File | What it covers |
|---|---|
| [checklist-design-and-launch.md](checklist-design-and-launch.md) | A design and launch checklist in six stages, from "do you need RAG at all" to security and compliance. The order of items is not arbitrary: the upper ones are cheaper and prevent rework of the lower ones |
| [failure-modes-catalog.md](failure-modes-catalog.md) | Twenty-six failure modes, grouped by layer: data, retrieval, operations, security, quality and cost, organization. A pre-launch review checklist and a frame for incident analysis |
| [principles.md](principles.md) | Twelve principles that recur among independent practitioners. A frame for decisions, not a list to tick off |
| [tools-catalog.md](tools-catalog.md) | The tool landscape: orchestration frameworks, low-code platforms, managed services, observability and evaluation, ready-made open-source platforms. A map of "why people pick it and where it hits limits" |
| [russian-layer.md](russian-layer.md) | Adjustments for a Russian-language corpus: embedders and rerankers, model prefixes, cross-lingual search, working local stacks |
| [vector-db-lifecycle-and-code-indexing.md](vector-db-lifecycle-and-code-indexing.md) | The life of a database after the first load: six maturity levels of update and deletion, ready-made record managers and their limits, a checklist for making your own decision. Part two: code indexing - AST chunking, the "grep vs index" debate, tools and models |

If you have no time to read everything, start here: `principles.md` sets the frame in five minutes,
`checklist-design-and-launch.md` gives the order of work on your own project, and you open the other three
as needed.
