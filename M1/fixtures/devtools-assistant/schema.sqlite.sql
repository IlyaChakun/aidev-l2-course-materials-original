-- DevTools assistant. Key entity: review task.
-- Dialect: SQLite.
--
-- The status domain and transition rules are intentionally NOT fixed here:
-- defining the lifecycle invariants is part of the assignment.

DROP TABLE IF EXISTS review_tasks;

CREATE TABLE review_tasks (
    id            INTEGER PRIMARY KEY,
    repository    TEXT    NOT NULL,
    pull_request  INTEGER NOT NULL,
    title         TEXT    NOT NULL,
    author        TEXT    NOT NULL,
    diff_summary  TEXT    NOT NULL,
    review_note   TEXT,
    status        TEXT    NOT NULL,
    score         INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    last_modified TEXT    NOT NULL
);

CREATE INDEX idx_review_tasks_status ON review_tasks (status);
