PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS document_file_sources (
    document_file_source_id TEXT PRIMARY KEY,
    document_file_id TEXT NOT NULL REFERENCES document_files(document_file_id),
    external_source_id TEXT NOT NULL REFERENCES external_sources(external_source_id),
    source_context_path TEXT,
    associated_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (document_file_id, external_source_id)
);

CREATE INDEX IF NOT EXISTS idx_document_file_sources_external
ON document_file_sources(external_source_id);

INSERT OR IGNORE INTO document_file_sources(
    document_file_source_id,
    document_file_id,
    external_source_id,
    source_context_path,
    associated_at,
    metadata_json
)
SELECT
    'FILESRC-' || lower(hex(randomblob(16))),
    document_file_id,
    external_source_id,
    json_extract(metadata_json, '$.drive_path'),
    imported_at,
    metadata_json
FROM document_files
WHERE external_source_id IS NOT NULL;
