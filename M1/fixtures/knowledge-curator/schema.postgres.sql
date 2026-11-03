-- Knowledge curator. Key entity: knowledge source.
-- Dialect: PostgreSQL.
--
-- The status domain and transition rules are intentionally NOT fixed here:
-- defining the lifecycle invariants is part of the assignment.

DROP TABLE IF EXISTS sources;

CREATE TABLE sources (
    id            integer     PRIMARY KEY,
    title         text        NOT NULL,
    url           text        NOT NULL,
    kind          text        NOT NULL,
    topic         text        NOT NULL,
    summary       text,
    status        text        NOT NULL,
    score         integer     NOT NULL CHECK (score BETWEEN 0 AND 100),
    last_modified timestamptz NOT NULL
);

CREATE INDEX idx_sources_status ON sources (status);
