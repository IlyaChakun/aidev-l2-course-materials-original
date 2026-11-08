-- DB schema of "Smart Support" (SQLite). Schema version: 1.
-- Invariants are enforced both in the DB (CHECK, trigger) and in mcp_server/domain; a test checks that they match.
-- IMPORTANT: SQLite enables foreign keys per connection: PRAGMA foreign_keys = ON (the repository does this).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS tickets (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    subject           TEXT    NOT NULL CHECK (length(subject) BETWEEN 1 AND 300),
    body              TEXT    NOT NULL DEFAULT '',
    customer_ref      TEXT    NOT NULL,
    status            TEXT    NOT NULL DEFAULT 'new'
                              CHECK (status IN ('new', 'answered', 'escalated')),
    category          TEXT    CHECK (category IS NULL OR category IN
                              ('billing', 'technical', 'account', 'how_to', 'complaint', 'other')),
    priority          TEXT    CHECK (priority IS NULL OR priority IN
                              ('low', 'normal', 'high', 'urgent')),
    score             INTEGER CHECK (score IS NULL OR (score BETWEEN 0 AND 100)),
    answer            TEXT,
    escalation_reason TEXT,
    created_at        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    last_modified     TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
    -- Consistency invariants between fields and status
    CHECK (status <> 'answered'  OR (answer IS NOT NULL AND length(trim(answer)) > 0)),
    CHECK (status <> 'escalated' OR (escalation_reason IS NOT NULL AND length(trim(escalation_reason)) > 0)),
    CHECK (status <> 'new'       OR (answer IS NULL AND escalation_reason IS NULL))
);

CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets (status);
CREATE INDEX IF NOT EXISTS idx_tickets_customer ON tickets (customer_ref);

-- Status graph at the DB level (second line of defense). The first line: mcp_server/domain.
-- Allowed: new -> answered, new -> escalated, answered -> escalated. escalated is terminal.
CREATE TRIGGER IF NOT EXISTS trg_tickets_status_transition
BEFORE UPDATE OF status ON tickets
WHEN NEW.status <> OLD.status
 AND NOT (
        (OLD.status = 'new'      AND NEW.status IN ('answered', 'escalated'))
     OR (OLD.status = 'answered' AND NEW.status = 'escalated')
 )
BEGIN
    SELECT RAISE(ABORT, 'invalid status transition');
END;

-- Agent trace: every step on a ticket, including rejected attempts.
CREATE TABLE IF NOT EXISTS agent_trace (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ticket_id   INTEGER NOT NULL REFERENCES tickets (id) ON DELETE CASCADE,
    agent       TEXT    NOT NULL CHECK (length(agent) BETWEEN 1 AND 64),
    input_json  TEXT    CHECK (input_json  IS NULL OR json_valid(input_json)),
    output_json TEXT    CHECK (output_json IS NULL OR json_valid(output_json)),
    status_from TEXT    CHECK (status_from IS NULL OR status_from IN ('new', 'answered', 'escalated')),
    status_to   TEXT    CHECK (status_to   IS NULL OR status_to   IN ('new', 'answered', 'escalated')),
    outcome     TEXT    NOT NULL DEFAULT 'ok' CHECK (outcome IN ('ok', 'rejected', 'error')),
    error_code  TEXT,
    created_at  TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_agent_trace_ticket ON agent_trace (ticket_id);
