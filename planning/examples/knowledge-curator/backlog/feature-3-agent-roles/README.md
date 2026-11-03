# 3 · Three roles

**Status:** `spec` · **Waiting for:** 1, 2 · **Blocks:** 4

## What it does

Describes and debugs three agents: the Collector, the Rater and the Summarizer. Each has its
own system prompt, its own input and its own output format. For now the roles are launched
separately, feature 4 connects them.

## Why

Here the split saves money, not just structure. Summarizing is expensive, and only seven items
out of sixty reach it. The Rater works on the short description, the Summarizer on the full
text, and mixing them into one role means paying for the summary of everything in a row.

## Input and output

| | |
|---|---|
| **Input** | The MCP server from feature 1, search over the archive from feature 2, descriptions of the seven topics of interest |
| **Output** | Three system prompts in `prompts/`, each with a JSON schema for its output. A script that runs any role on a sample of items |

Contracts between the roles:

| Role | Input | Output |
|---|---|---|
| Collector | A list of feeds and channels, the mark of the last collection | New items in the `collected` status, duplicates by link dropped |
| Rater | An item, the topics of interest, similar items from the archive | A usefulness rating 0-100, a reason, a duplicate flag |
| Summarizer | Items that passed the filter | A summary for each and the overall text of the digest |

## Boundaries

- Launch schedule: not included, that is feature 4.
- Sending the digest: not included, that is feature 4.
- Accounting for the reader's reactions: not included, that is feature 5.
- Downloading full text around a paywall: we do not do it, a decision from the roadmap.

## Done when

- [ ] The Collector goes through all 24 feeds and 9 channels and does not crash on an unavailable source
- [ ] A repeated Collector run on the same day does not create duplicates by link
- [ ] The output of each role passes validation against the JSON schema
- [ ] Every Rater rating has a reason, and it refers to a specific topic of interest
- [ ] The Rater flags a duplicate when the item was already in the archive
- [ ] The Summarizer does not add to the summary anything that is not in the source text
- [ ] No role goes to the database directly, only through the MCP server

## Read before starting

- `../feature-1-mcp-sources/README.md`: the set of tools and the conflict on `url`
- `../feature-2-archive-search/README.md`: what search over the archive returns
- `config/topics.md`: descriptions of the seven topics of interest
- `../../roadmap.md`, blocks 3 and 5

## Open questions

- **Topic descriptions are vague.** The Rater gives ratings based on them that are hard to
  contest and hard to defend. Either rewrite the descriptions in more detail, or give
  examples of items that definitely fit and definitely do not.
- **Items behind a paywall.** The feed gives three paragraphs. Rating on them is possible,
  summarizing is dishonest. Mark such items separately or skip them, not decided.
- **Digest length.** Ten items of three lines or seven of five. The Summarizer's prompt
  depends on this.
