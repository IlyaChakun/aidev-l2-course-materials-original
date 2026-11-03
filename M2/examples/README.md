# n8n workflow examples for module 2

Five working builds used to go through the session's patterns: how documents get into the vector
database, how the database is updated, how search is arranged and how an agent chooses a tool for
the type of question.

These are **examples for reading and analysis, not a ready solution to the homework**. None of the
files will run right after import: neither credentials, nor addresses, nor folder identifiers are
deliberately left in them. Each such place is marked with a `YOUR_...` placeholder, and what exactly
to substitute is written on the yellow note inside the workflow itself.

## What is where

| File | What it shows | Nodes and credentials | Size |
|---|---|---|---|
| [`m2-qdrant-ingest-gdrive.json`](m2-qdrant-ingest-gdrive.json) | The shortest honest answer to the question "how does a collection even appear": creating a collection in Qdrant, cleaning, a list of files in a Google Drive folder, splitting into chunks, writing | `httpRequest` (PUT and POST to Qdrant), `googleDrive`, `vectorStoreQdrant` insert, loader + chunker + embeddings.<br>Credentials: Qdrant, Google Drive, OpenAI | 13 nodes |
| [`m2-hybrid-search-record-manager.json`](m2-hybrid-search-record-manager.json) | Two things at once: incremental loading with change detection by hash and hybrid search with a reranker | `googleDriveTrigger`, `crypto` SHA256, `supabase` (the record manager table), `switch` into three branches, `postgres` with an SQL fusion function, `httpRequest` to Cohere.<br>Credentials: Google Drive, Supabase, Postgres, OpenAI, Cohere | 28 nodes |
| [`m2-agentic-rag-4-tools.json`](m2-agentic-rag-4-tools.json) | One agent, one database, four different tools for four types of question. Plus a quality evaluation branch on n8n's native evals | `agent`, `vectorStorePGVector` retrieve-as-tool with a reranker, three `postgresTool`, `evaluationTrigger` + `evaluation`.<br>Credentials: OpenAI, Postgres, Cohere, Google Sheets | 20 nodes |
| [`m2-rag-full-lifecycle-pgvector.json`](m2-rag-full-lifecycle-pgvector.json) | A grown-up ingest in full: two triggers on a folder, parsing five file types, text into vectors, tables separately as rows, a separate branch for deletions, an agent on top | `googleDriveTrigger` ×2, `switch` by file type, `extractFromFile` ×3, `vectorStorePGVector`, `postgres` (including DDL), `scheduleTrigger`, `agent` with four tools.<br>Credentials: Google Drive, Postgres, OpenAI, Cohere | 54 nodes |
| [`m2-corpus-cleanup-cron.json`](m2-corpus-cleanup-cron.json) | The same story about deletions, but in minimal form: cross-checking the list of files against the list of documents once a day | `scheduleTrigger`, `googleDrive` list, `code`, `supabase` delete.<br>Credentials: Google Drive, Supabase | 7 nodes |

## How to import

1. In n8n: **Workflows → the top menu "..." → Import from File**, choose the `.json` you need.
2. Open every node with a red triangle and choose your own credentials instead of
   `YOUR_..._CREDENTIAL`. The list of what you will need is in the table above and on the note
   inside the workflow.
3. Find the remaining placeholders and substitute your own values. The quickest way is to search
   for the text `YOUR_` right in the file, before importing:
   - `YOUR_FOLDER_ID` — the Google Drive folder identifier (visible in the folder's address bar);
   - `YOUR_SHEET_ID` — the identifier of the Google Sheets table with the evaluation dataset;
   - `YOUR_QDRANT_HOST:6333` — the address of your Qdrant;
   - `YOUR_WORKFLOW_ID` — the identifier of the workflow itself, it is filled in after the first
     save (in the hybrid search example, search is called as a sub-workflow).
4. Check that the needed tables and functions exist in the database. They are not part of the n8n
   export: `hybrid_documents`, `record_manager_hybrid`, the SQL fusion function, `documents_pg`,
   `document_metadata`, `document_rows` — this is your schema, you have to create it yourself.
   The exception: in the full-cycle example there are nodes with DDL, marked with a separate note.

## Reading order

If you look at all five in a row, the logic is this:

**The first** answers the question of where a collection comes from, and at the same time shows an
antipattern: before every load the collection is cleaned out entirely. This is a full index
rebuild. On twenty documents it is unnoticeable, on twenty thousand it no longer is.

**The second** does the same thing in a grown-up way. The content hash is compared with the saved
one, and the file is reloaded only if the text has actually changed. It also shows how the fusion
of results is arranged: an SQL function returns the vector score, the keyword score, both ranks
and the total as separate columns, so the search decision can be looked at with your eyes rather
than taken on faith.

**The third** is about choosing a tool. The question "what does it say about delivery" and the
question "what is the sales total for March" are solved in fundamentally different ways: the second
answer is in no chunk, it has to be computed. So the tabular data lies in the database without
embeddings at all, and the agent gets its schema and writes the SQL itself.

**The fourth** puts it all together and adds what is most often forgotten: deletion. No file
trigger reports that a document was removed, so a separate scheduled branch is set up for
deletions. **The fifth** is the same idea in seven nodes, if you do not feel like reading all
fifty-four.

## Where this comes from

The first three and the fifth are worked-out teaching builds brought to a neutral form: names,
credentials, instance addresses and folder identifiers have been removed from them, only the
schemas and node settings remain. The fourth is based on the public Agentic RAG template by Cole
Medin (`youtube.com/@ColeMedin`); the author's note is left inside the workflow, everything else is
likewise replaced with placeholders.

## Caution

- **Do not run the nodes with DDL on a production database.** In the full-cycle example there are
  nodes that create tables in the database the credential points to. Set up a separate database for
  teaching experiments.
- **Check that the credentials point to your instance.** The most expensive mistake when going
  through someone else's workflow is to leave a setting that writes not where you think.
- **The vector dimension when creating a collection is tied to the embedding model.** If you
  changed the model, the collection has to be created anew, you cannot append to the existing one.
