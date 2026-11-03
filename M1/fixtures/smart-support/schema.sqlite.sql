-- Smart support. Key entity: ticket.
-- Dialect: SQLite.
--
-- The status domain and transition rules are intentionally NOT fixed here:
-- defining the lifecycle invariants is part of the assignment.

DROP TABLE IF EXISTS tickets;

CREATE TABLE tickets (
    id            INTEGER PRIMARY KEY,
    subject       TEXT    NOT NULL,
    customer      TEXT    NOT NULL,
    channel       TEXT    NOT NULL,
    body          TEXT    NOT NULL,
    answer        TEXT,
    status        TEXT    NOT NULL,
    score         INTEGER NOT NULL CHECK (score BETWEEN 0 AND 100),
    last_modified TEXT    NOT NULL
);

CREATE INDEX idx_tickets_status ON tickets (status);
