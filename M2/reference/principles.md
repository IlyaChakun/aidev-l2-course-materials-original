# Twelve RAG principles · Module 2 handout · date 10.08.2026

Twelve statements that recur among independent practitioners and researchers and that are worth
keeping in mind as a frame, rather than checking against them as a list.

**How to use it.** This is not a checklist and not a sequence of actions: it is what to remember when you
make a decision about a specific system. If a decision contradicts one of the points, that is
not a prohibition, but it requires a stated reason.

---

1. **The decision is made per feature, not once per product.** Whether retrieval, a long context,
   an SQL query or an agent with tools is needed here is determined by the task and the query class of
   that specific feature.

2. **Parsing matters more than algorithms.** A third or half of the work, and it sets the ceiling: nothing upstream
   will rise above the quality of text extraction.

3. **Hybrid is mandatory.** Pure vector fails silently, and exactly where the data is exact:
   part numbers, error codes, API names.

4. **Metadata is not decoration but a second retrieval mechanism.** And the only legitimate mechanism
   for access control.

5. **Retrieval is an authorization decision.** What got into the context, the user has already seen,
   so permissions are applied in retrieval, not in the interface on top of it.

6. **An embedding is a copy of the data.** A meaningful part of the source text can be recovered from a vector,
   so vectors fall inside the same protection perimeter as the documents.

7. **An index is a living system, not a build artifact.** It drifts, and the drift must be caught.

8. **Measure before you optimize.** Otherwise improving one query class breaks another,
   and it will be noticed by users, not by you.

9. **Green metrics do not equal satisfied users.** A mismatch almost always means
   that what is measured is not what matters in this domain.

10. **Saving tokens does not equal saving money.** What is saved on input is regularly eaten
    by growth in output tokens.

11. **A ceiling of around 80-85%.** Discuss it with the business up front, not at acceptance.

12. **A simple solution the team can operate beats a complex correct one.**

> On item 11: this is practitioners' observation on their own evaluation sets, not the result of a
> controlled study, and nobody has measured a universal ceiling. As a guideline and as an
> argument in a conversation with the client the figure is useful; it must not be presented as a measured fact.
