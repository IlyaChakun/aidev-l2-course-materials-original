-- Schema for the pgvector side of the demo. Recreated by `make load`.
CREATE EXTENSION IF NOT EXISTS vector;

DROP TABLE IF EXISTS chunks CASCADE;
DROP TABLE IF EXISTS chunks_big CASCADE;
DROP TABLE IF EXISTS docs_access CASCADE;
DROP TABLE IF EXISTS docs CASCADE;

-- Business table: one row per source document (metadata lives next to the vectors).
CREATE TABLE docs (
    source      text PRIMARY KEY,
    title       text NOT NULL,
    version     int  NOT NULL DEFAULT 1,
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Business table: which plan may see which document (one row per source and plan).
CREATE TABLE docs_access (
    source  text NOT NULL REFERENCES docs(source),
    plan    text NOT NULL CHECK (plan IN ('starter', 'team', 'business')),
    PRIMARY KEY (source, plan)
);

-- Chunks of the real corpus: text, metadata, dense vector and a full-text vector in one row.
CREATE TABLE chunks (
    id          uuid PRIMARY KEY,
    source      text NOT NULL REFERENCES docs(source),
    section     text NOT NULL,
    content     text NOT NULL,
    tenant      text NOT NULL DEFAULT 'lumen',
    updated_at  timestamptz NOT NULL DEFAULT now(),
    embedding   vector(1536) NOT NULL,
    tsv         tsvector GENERATED ALWAYS AS (
                    setweight(to_tsvector('english', section), 'A') ||
                    setweight(to_tsvector('english', content), 'B')
                ) STORED
);

-- Synthetic table for step 4: real chunks copied for many tenants with a little noise.
-- No FK and no tsv: it exists only to show the filtered-search pitfall at 20K rows.
CREATE TABLE chunks_big (
    id          uuid PRIMARY KEY,
    source      text NOT NULL,
    section     text NOT NULL,
    content     text NOT NULL,
    tenant      text NOT NULL,
    embedding   vector(1536) NOT NULL
);
