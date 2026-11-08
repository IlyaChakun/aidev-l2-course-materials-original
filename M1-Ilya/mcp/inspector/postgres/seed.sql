-- Sample database for Postgres MCP Pro: the same tickets as in support-tickets, but in Postgres
-- and with 20,000 rows, so explain_query and analyze_db_health have something to show.
CREATE TABLE tickets (
    id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    subject     text        NOT NULL,
    customer    text        NOT NULL,
    status      text        NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'answered', 'escalated')),
    category    text,
    answer      text,
    created_at  timestamptz NOT NULL DEFAULT now()
);

INSERT INTO tickets (subject, customer, status, category, answer, created_at)
SELECT
    (ARRAY['Cannot reset password', 'Refund not received', 'Export is empty', 'App crashes on start', 'Invoice has wrong VAT'])[1 + i % 5],
    'customer' || (i % 3000) || '@example.com',
    (ARRAY['new', 'answered', 'escalated'])[1 + i % 3],
    (ARRAY['account', 'billing', 'data', 'bug', 'billing'])[1 + i % 5],
    CASE WHEN i % 3 = 1 THEN 'See the help article.' END,
    now() - (i || ' minutes')::interval
FROM generate_series(1, 20000) AS i;

-- There is deliberately no index on customer: a query by customer gives a Seq Scan in explain_query.
CREATE INDEX tickets_status_idx ON tickets (status);
ANALYZE tickets;
