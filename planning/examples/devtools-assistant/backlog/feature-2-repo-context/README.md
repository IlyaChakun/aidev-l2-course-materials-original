# 2 · Repository context

**Status:** `in-build` · **Waits for:** none · **Blocks:** 3

## What it does

Assembles knowledge about the repository into a searchable corpus: conventions, architectural
decisions and past review discussions. The input is the path of a changed file and the gist of
the change, the output is what is already known about that place, with the source indicated.

## Why

Without this the Reviewer issues general-form comments that are valid for any project and useless
for this one. A link to a convention turns "better to extract into a separate function" into
"rule 3.1 forbids functions longer than forty lines".

## Input and output

| | |
|---|---|
| **Input** | 12 convention documents, an export of 210 pull request discussions |
| **Output** | The `context/` module: indexing, search. `find_context(path, summary, k)` returns rules and past discussions, each with a source, a type and a similarity score |

Discussions are marked with a separate type: a discussion is a precedent, not a rule, and in a
comment they are presented differently.

## Boundaries

- Indexing the repository source code: out of scope. We index documents and discussions, not
  code.
- Automatic reindexing on commit: out of scope, manual launch.
- Several repositories: out of scope.
- Generating comments: out of scope, that is feature 3.

## Done when

- [x] Indexing starts with one command, the number of fragments is printed to the console
- [x] A fragment has a source, a type (convention or discussion) and a section
- [ ] On 12 test changes the right convention lands in the top three results
- [ ] A change in a file about which nothing is known gives an empty result
- [ ] Discussions and conventions are distinguishable in the output
- [ ] Reindexing does not duplicate fragments

## Read before starting

- `docs/conventions/README.md`: the structure of the conventions
- `../../roadmap.md`, block 2
- `spec.md` next to this file

## Open questions

- **Discussions without context.** In the export a discussion often looks like "fix this here"
  with no indication of what exactly. Such ones are useless. Filter by length or label by hand,
  not decided.
- **Search by file path.** Text similarity works badly when the query is a path. We need either
  a separate search by path or metadata with paths. We are trying the second.
- Twelve test changes is few, but there is nowhere to get more for now.
