-- Smart support. Key entity: ticket.
-- Dialect: PostgreSQL.
--
-- The status domain and transition rules are intentionally NOT fixed here:
-- defining the lifecycle invariants is part of the assignment.

DROP TABLE IF EXISTS tickets;

CREATE TABLE tickets (
    id            integer     PRIMARY KEY,
    subject       text        NOT NULL,
    customer      text        NOT NULL,
    channel       text        NOT NULL,
    body          text        NOT NULL,
    answer        text,
    status        text        NOT NULL,
    score         integer     NOT NULL CHECK (score BETWEEN 0 AND 100),
    last_modified timestamptz NOT NULL
);

CREATE INDEX idx_tickets_status ON tickets (status);
