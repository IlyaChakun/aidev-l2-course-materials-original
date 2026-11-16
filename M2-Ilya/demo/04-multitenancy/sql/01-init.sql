-- pgvector + Row Level Security. Runs once on first container start (docker-entrypoint-initdb.d).
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE chunks (
    id         uuid PRIMARY KEY,
    tenant_id  text   NOT NULL,
    groups     text[] NOT NULL,
    doc_id     text   NOT NULL,
    title      text   NOT NULL,
    section    text   NOT NULL,
    text       text   NOT NULL,
    embedding  vector(1536) NOT NULL
);
CREATE INDEX chunks_tenant_idx ON chunks (tenant_id);
CREATE INDEX chunks_embedding_hnsw ON chunks USING hnsw (embedding vector_cosine_ops);

-- RLS: every query from the app role sees only rows of the tenant set in app.tenant.
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
-- FORCE makes the table owner subject to RLS too. Superusers and BYPASSRLS roles still bypass it.
ALTER TABLE chunks FORCE ROW LEVEL SECURITY;

-- current_setting(..., true) returns NULL when unset -> comparison is NULL -> no rows (fail closed).
CREATE POLICY tenant_isolation ON chunks
    USING      (tenant_id = current_setting('app.tenant', true))
    WITH CHECK (tenant_id = current_setting('app.tenant', true));

-- Document ACL inside a tenant. RESTRICTIVE = ANDed with the tenant policy, not ORed.
CREATE POLICY acl_groups ON chunks AS RESTRICTIVE FOR SELECT
    USING (groups && string_to_array(current_setting('app.groups', true), ','));

-- The application role: not a superuser, not the owner, NOBYPASSRLS.
CREATE ROLE app_user LOGIN PASSWORD 'app_pass' NOSUPERUSER NOBYPASSRLS;
GRANT SELECT, INSERT, UPDATE, DELETE ON chunks TO app_user;
