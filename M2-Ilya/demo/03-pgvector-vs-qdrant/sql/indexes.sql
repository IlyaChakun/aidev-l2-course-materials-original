-- Indexes are built after the bulk load: building HNSW on a filled table is faster
-- than maintaining it row by row. Defaults written out to make them visible.
CREATE INDEX chunks_embedding_hnsw ON chunks
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);
CREATE INDEX chunks_tsv_gin ON chunks USING gin (tsv);

CREATE INDEX chunks_big_embedding_hnsw ON chunks_big
    USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64);

ANALYZE docs;
ANALYZE docs_access;
ANALYZE chunks;
ANALYZE chunks_big;
