-- DevTools assistant. Key entity: review task.
-- Dialect: PostgreSQL.
--
-- The status domain and transition rules are intentionally NOT fixed here:
-- defining the lifecycle invariants is part of the assignment.

DROP TABLE IF EXISTS review_tasks;

CREATE TABLE review_tasks (
    id            integer     PRIMARY KEY,
    repository    text        NOT NULL,
    pull_request  integer     NOT NULL,
    title         text        NOT NULL,
    author        text        NOT NULL,
    diff_summary  text        NOT NULL,
    review_note   text,
    status        text        NOT NULL,
    score         integer     NOT NULL CHECK (score BETWEEN 0 AND 100),
    last_modified timestamptz NOT NULL
);

CREATE INDEX idx_review_tasks_status ON review_tasks (status);
