-- Knowledge curator. Key entity: knowledge source.
-- Dialect: SQLite.
--
-- The status domain and transition rules are intentionally NOT fixed here:
-- defining the lifecycle invariants is part of the assignment.

DROP TABLE IF EXISTS sources;

CREATE TABLE sources (
    id            INTEGER PRIMARY KEY,
    title         TEXT    NOT NULL,
    url           TEXT    NOT NULL,
    kind          TEXT    NOT NULL,
    topic         TEXT    NOT NULL,
    summary       TEXT,
    status        TEXT    NOT NULL,
    score         INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    last_modified TEXT    NOT NULL
);

CREATE INDEX idx_sources_status ON sources (status);
