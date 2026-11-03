-- AI editorial. Key entity: article.
-- Dialect: SQLite.
--
-- The status domain and transition rules are intentionally NOT fixed here:
-- defining the lifecycle invariants is part of the assignment.

DROP TABLE IF EXISTS articles;

CREATE TABLE articles (
    id            INTEGER PRIMARY KEY,
    title         TEXT    NOT NULL,
    author        TEXT    NOT NULL,
    section       TEXT    NOT NULL,
    body          TEXT    NOT NULL,
    status        TEXT    NOT NULL,
    score         INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    last_modified TEXT    NOT NULL
);

CREATE INDEX idx_articles_status ON articles (status);
