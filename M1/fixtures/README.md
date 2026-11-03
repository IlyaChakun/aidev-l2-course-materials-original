# Starter fixtures for the four tracks

Ready-made data so you do not spend time inventing records. Each folder has one table and exactly 20 records, distributed across all lifecycle statuses.

Using a fixture is not required. Your own domain instead of the suggested one is also fine: if you already have an entity with statuses, work with it and look at these files as a sample of the shape.

## Tracks

| Folder | Project | Entity | Table | Statuses |
|---|---|---|---|---|
| `ai-editorial/` | AI editorial | article | `articles` | `draft` → `checked` → `published` |
| `smart-support/` | Smart support | ticket | `tickets` | `new` → `answered` → `escalated` |
| `devtools-assistant/` | DevTools assistant | review task | `review_tasks` | `queued` → `reviewed` → `tested` |
| `knowledge-curator/` | Knowledge curator | knowledge source | `sources` | `collected` → `rated` → `summarized` |

Fields common to all four tables: `id`, `status`, `score` (a numeric rating 0-100), `last_modified`. The other fields are specific to each domain. The meaning of `score` depends on the track: for an article it is the editorial score, for a ticket the urgency, for a review task the risk of the change, for a source the usefulness.

## Files in each folder

| File | What |
|---|---|
| `schema.sqlite.sql` | DDL for SQLite |
| `schema.postgres.sql` | DDL for PostgreSQL |
| `seed.sql` | 20 records, the same file for both databases |

**Why two DDL files instead of one portable one.** A portable version is possible, but it requires storing time as text, because SQLite has no separate date type. For SQLite that is the norm, but for PostgreSQL it is a poor schema to build the whole homework on. The two files differ only in the DDL: there are just two differences, the time type (`TEXT` vs `timestamptz`) and the case of the type names. The data is shared: there is one `seed.sql` for both databases, because PostgreSQL parses time literals in the `YYYY-MM-DD HH:MM:SS` format on its own.

A side effect of this decision: the time literals are written without an offset, and PostgreSQL fills it in from the session time zone. On machines in different time zones the same record gets a different absolute moment. This does not affect the assignment: comparisons and sorting within a single database work as expected. If you want identical values everywhere, add an offset to the literals or set `SET timezone = 'UTC'` before loading.

## Loading

SQLite, in one command:

```bash
cd ai-editorial
sqlite3 app.db ".read schema.sqlite.sql" ".read seed.sql"
```

PostgreSQL, in one command (the database is already created):

```bash
cd ai-editorial
psql -v ON_ERROR_STOP=1 -d app -f schema.postgres.sql -f seed.sql
```

If the database does not exist yet, run `createdb app` first.

Check that the load worked:

```bash
sqlite3 app.db "SELECT status, COUNT(*) FROM articles GROUP BY status;"
psql -d app -c "SELECT status, COUNT(*) FROM articles GROUP BY status;"
```

You can reload as many times as you like, but **only as a schema + seed pair**: `DROP TABLE IF EXISTS` is in the schema files, not in `seed.sql`. Running `seed.sql` alone on top of already loaded data will not work, it fails with `UNIQUE constraint failed: articles.id`. This is not a broken fixture but a guard against accidental duplication: to start over, run the schema and the data together.

## What is built into the data

Records are distributed across all three statuses rather than piled into one. This is so there is something to check both a successful pass through the lifecycle and a rejection of an invalid transition against.

Distribution and edge cases:

| Track | Distribution | Edge-case scores |
|---|---|---|
| `ai-editorial` | 7 / 7 / 6 | `id 7` = 0, `id 19` = 100 |
| `smart-support` | 8 / 7 / 5 | `id 6` = 0, `id 17` = 100 |
| `devtools-assistant` | 7 / 7 / 6 | `id 5` = 0, `id 15` = 100 |
| `knowledge-curator` | 7 / 7 / 6 | `id 6` = 0, `id 15` = 100 |

In three of the tracks there is a field that is not filled in right away (`answer`, `review_note`, `summary`): for records in the first status it is empty. This is also material for checks.

## What is intentionally not done here

**The schema has neither a table of allowed transitions nor a status check.** This is not an oversight. Fixing the lifecycle invariants is part of the assignment, and the server must not let the agent make an invalid transition. If ready-made rules were put into the fixture, the assignment would lose its point.

Of the constraints, only those that describe the shape of the data, not its lifecycle, are kept: the primary key, `NOT NULL`, and the range `score BETWEEN 0 AND 100`.

## What you can change

Everything. This is starter data, not a contract: add fields, rename things, add records, create related tables. The only thing worth keeping is the presence of a status and that all lifecycle stages are populated, otherwise there will be nothing to check a rejection of an invalid transition against.
