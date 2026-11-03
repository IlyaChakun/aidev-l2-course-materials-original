-- AI editorial. Key entity: article.
-- Dialect: PostgreSQL.
--
-- The status domain and transition rules are intentionally NOT fixed here:
-- defining the lifecycle invariants is part of the assignment.

DROP TABLE IF EXISTS articles;

CREATE TABLE articles (
    id            integer     PRIMARY KEY,
    title         text        NOT NULL,
    author        text        NOT NULL,
    section       text        NOT NULL,
    body          text        NOT NULL,
    status        text        NOT NULL,
    score         integer     NOT NULL CHECK (score BETWEEN 0 AND 100),
    last_modified timestamptz NOT NULL
);

CREATE INDEX idx_articles_status ON articles (status);
