PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS actors (
    actor_id TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    role TEXT NOT NULL CHECK (
        role IN (
            'administrator',
            'editor',
            'methodological_reviewer',
            'editorial_reviewer',
            'auditor',
            'contributor',
            'viewer',
            'agent'
        )
    ),
    external_identity TEXT,
    created_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS editions (
    edition_id TEXT PRIMARY KEY,
    canonical_title TEXT NOT NULL,
    summary TEXT,
    status TEXT NOT NULL,
    editorial_meaning TEXT NOT NULL,
    meaning_confidence REAL NOT NULL DEFAULT 0.0 CHECK (
        meaning_confidence >= 0.0 AND meaning_confidence <= 1.0
    ),
    job_id TEXT UNIQUE,
    source_path TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    confirmed_by TEXT REFERENCES actors(actor_id),
    confirmed_at TEXT,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS taxonomy_terms (
    term_id TEXT PRIMARY KEY,
    vocabulary TEXT NOT NULL,
    label TEXT NOT NULL,
    parent_id TEXT REFERENCES taxonomy_terms(term_id),
    description TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0, 1)),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (vocabulary, label)
);

CREATE TABLE IF NOT EXISTS external_sources (
    external_source_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    original_url TEXT,
    original_name TEXT NOT NULL,
    mime_type TEXT,
    full_path TEXT,
    parent_ids_json TEXT NOT NULL DEFAULT '[]',
    created_time TEXT,
    modified_time TEXT,
    owner_json TEXT,
    permissions_json TEXT,
    drive_revision_id TEXT,
    imported_at TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    deleted_at TEXT,
    UNIQUE (provider, external_id)
);

CREATE TABLE IF NOT EXISTS documents (
    document_id TEXT PRIMARY KEY,
    edition_id TEXT REFERENCES editions(edition_id),
    external_key TEXT UNIQUE,
    canonical_title TEXT NOT NULL,
    original_name TEXT NOT NULL,
    document_type_id TEXT REFERENCES taxonomy_terms(term_id),
    document_subtype_id TEXT REFERENCES taxonomy_terms(term_id),
    editorial_function_id TEXT REFERENCES taxonomy_terms(term_id),
    stage_id TEXT REFERENCES taxonomy_terms(term_id),
    status_id TEXT REFERENCES taxonomy_terms(term_id),
    editorial_meaning TEXT NOT NULL,
    meaning_confidence REAL NOT NULL DEFAULT 0.0 CHECK (
        meaning_confidence >= 0.0 AND meaning_confidence <= 1.0
    ),
    classification_confidence REAL NOT NULL DEFAULT 0.0 CHECK (
        classification_confidence >= 0.0 AND classification_confidence <= 1.0
    ),
    classification_confirmed INTEGER NOT NULL DEFAULT 0 CHECK (
        classification_confirmed IN (0, 1)
    ),
    classification_confirmed_by TEXT REFERENCES actors(actor_id),
    classification_confirmed_at TEXT,
    revision_required INTEGER NOT NULL DEFAULT 1 CHECK (revision_required IN (0, 1)),
    reusable INTEGER NOT NULL DEFAULT 0 CHECK (reusable IN (0, 1)),
    validated_memory_eligible INTEGER NOT NULL DEFAULT 0 CHECK (
        validated_memory_eligible IN (0, 1)
    ),
    known_errors INTEGER NOT NULL DEFAULT 0 CHECK (known_errors IN (0, 1)),
    unverified_data INTEGER NOT NULL DEFAULT 1 CHECK (unverified_data IN (0, 1)),
    notes TEXT,
    profession TEXT,
    specialty TEXT,
    subarea TEXT,
    study_design TEXT,
    evidence_type TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS document_versions (
    version_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    version_number INTEGER NOT NULL CHECK (version_number >= 1),
    previous_version_id TEXT REFERENCES document_versions(version_id),
    restored_from_version_id TEXT REFERENCES document_versions(version_id),
    author_actor_id TEXT REFERENCES actors(actor_id),
    agent_id TEXT REFERENCES actors(actor_id),
    created_at TEXT NOT NULL,
    reason TEXT NOT NULL,
    change_summary TEXT NOT NULL,
    status_id TEXT REFERENCES taxonomy_terms(term_id),
    editorial_meaning TEXT NOT NULL,
    meaning_confidence REAL NOT NULL DEFAULT 0.0 CHECK (
        meaning_confidence >= 0.0 AND meaning_confidence <= 1.0
    ),
    content_text TEXT,
    content_path TEXT,
    content_hash TEXT NOT NULL,
    source_kind TEXT NOT NULL,
    approval_status TEXT NOT NULL DEFAULT 'not_submitted',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (document_id, version_number),
    UNIQUE (document_id, content_hash)
);

CREATE TABLE IF NOT EXISTS document_files (
    document_file_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    external_source_id TEXT REFERENCES external_sources(external_source_id),
    storage_path TEXT NOT NULL,
    normalized_text_path TEXT,
    original_filename TEXT NOT NULL,
    mime_type TEXT,
    extension TEXT,
    size_bytes INTEGER,
    content_hash TEXT NOT NULL,
    imported_at TEXT NOT NULL,
    private INTEGER NOT NULL DEFAULT 1 CHECK (private IN (0, 1)),
    metadata_json TEXT NOT NULL DEFAULT '{}',
    UNIQUE (version_id, storage_path)
);

CREATE TABLE IF NOT EXISTS document_relationships (
    relationship_id TEXT PRIMARY KEY,
    relationship_type TEXT NOT NULL,
    source_document_id TEXT REFERENCES documents(document_id),
    source_version_id TEXT REFERENCES document_versions(version_id),
    target_document_id TEXT REFERENCES documents(document_id),
    target_version_id TEXT REFERENCES document_versions(version_id),
    confidence REAL NOT NULL DEFAULT 1.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    confirmed INTEGER NOT NULL DEFAULT 0 CHECK (confirmed IN (0, 1)),
    rationale TEXT NOT NULL,
    created_by TEXT REFERENCES actors(actor_id),
    created_at TEXT NOT NULL,
    deleted_at TEXT,
    CHECK (
        (source_document_id IS NOT NULL OR source_version_id IS NOT NULL)
        AND (target_document_id IS NOT NULL OR target_version_id IS NOT NULL)
    )
);

CREATE TABLE IF NOT EXISTS editorial_events (
    event_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    edition_id TEXT REFERENCES editions(edition_id),
    document_id TEXT REFERENCES documents(document_id),
    version_id TEXT REFERENCES document_versions(version_id),
    event_type TEXT NOT NULL,
    actor_id TEXT REFERENCES actors(actor_id),
    agent_id TEXT REFERENCES actors(actor_id),
    occurred_at TEXT NOT NULL,
    before_json TEXT,
    after_json TEXT,
    justification TEXT NOT NULL,
    origin TEXT NOT NULL,
    correlation_id TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS review_rounds (
    review_round_id TEXT PRIMARY KEY,
    edition_id TEXT NOT NULL REFERENCES editions(edition_id),
    document_id TEXT REFERENCES documents(document_id),
    version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    review_type TEXT NOT NULL,
    status TEXT NOT NULL,
    reviewer_actor_id TEXT REFERENCES actors(actor_id),
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT NOT NULL,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS review_comments (
    review_comment_id TEXT PRIMARY KEY,
    review_round_id TEXT REFERENCES review_rounds(review_round_id),
    version_id TEXT REFERENCES document_versions(version_id),
    external_comment_id TEXT,
    author_actor_id TEXT REFERENCES actors(actor_id),
    content TEXT NOT NULL,
    quoted_text TEXT,
    resolved INTEGER NOT NULL DEFAULT 0 CHECK (resolved IN (0, 1)),
    created_at TEXT NOT NULL,
    resolved_at TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS change_requests (
    change_request_id TEXT PRIMARY KEY,
    edition_id TEXT NOT NULL REFERENCES editions(edition_id),
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    source_version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    implemented_in_version_id TEXT REFERENCES document_versions(version_id),
    review_comment_id TEXT REFERENCES review_comments(review_comment_id),
    category TEXT NOT NULL,
    description TEXT NOT NULL,
    rationale TEXT NOT NULL,
    status TEXT NOT NULL,
    requested_by TEXT REFERENCES actors(actor_id),
    requested_at TEXT NOT NULL,
    decided_by TEXT REFERENCES actors(actor_id),
    decided_at TEXT,
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS version_diffs (
    version_diff_id TEXT PRIMARY KEY,
    from_version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    to_version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    literal_diff_json TEXT NOT NULL,
    semantic_diff_json TEXT NOT NULL,
    numeric_changes_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    created_by TEXT REFERENCES actors(actor_id),
    UNIQUE (from_version_id, to_version_id)
);

CREATE TABLE IF NOT EXISTS approvals (
    approval_id TEXT PRIMARY KEY,
    edition_id TEXT REFERENCES editions(edition_id),
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    approval_type TEXT NOT NULL,
    decision TEXT NOT NULL,
    actor_id TEXT NOT NULL REFERENCES actors(actor_id),
    rationale TEXT NOT NULL,
    created_at TEXT NOT NULL,
    revoked_by_approval_id TEXT REFERENCES approvals(approval_id)
);

CREATE TABLE IF NOT EXISTS publication_records (
    publication_id TEXT PRIMARY KEY,
    edition_id TEXT NOT NULL REFERENCES editions(edition_id),
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    approval_id TEXT NOT NULL REFERENCES approvals(approval_id),
    published_by TEXT NOT NULL REFERENCES actors(actor_id),
    published_at TEXT NOT NULL,
    destination TEXT,
    external_url TEXT,
    correction_of_publication_id TEXT REFERENCES publication_records(publication_id),
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS editorial_lessons (
    lesson_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    lesson_type TEXT NOT NULL,
    status TEXT NOT NULL,
    scope TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    proposed_by TEXT REFERENCES actors(actor_id),
    approved_by TEXT REFERENCES actors(actor_id),
    proposed_at TEXT NOT NULL,
    approved_at TEXT,
    rationale TEXT NOT NULL,
    exceptions TEXT,
    revoked_at TEXT,
    revoked_by TEXT REFERENCES actors(actor_id),
    superseded_by TEXT REFERENCES editorial_lessons(lesson_id),
    deleted_at TEXT
);

CREATE TABLE IF NOT EXISTS memory_items (
    memory_item_id TEXT PRIMARY KEY,
    memory_tier TEXT NOT NULL CHECK (memory_tier IN ('historical', 'validated')),
    category TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL,
    scope TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 0.0 CHECK (confidence >= 0.0 AND confidence <= 1.0),
    normative INTEGER NOT NULL DEFAULT 0 CHECK (normative IN (0, 1)),
    approved_by TEXT REFERENCES actors(actor_id),
    approved_at TEXT,
    justification TEXT NOT NULL,
    positive_examples_json TEXT NOT NULL DEFAULT '[]',
    counterexamples_json TEXT NOT NULL DEFAULT '[]',
    not_applicable_when TEXT,
    revoked_at TEXT,
    revoked_by TEXT REFERENCES actors(actor_id),
    created_at TEXT NOT NULL,
    deleted_at TEXT,
    CHECK (
        memory_tier = 'historical'
        OR (
            normative = 1
            AND approved_by IS NOT NULL
            AND approved_at IS NOT NULL
        )
    )
);

CREATE TABLE IF NOT EXISTS memory_item_sources (
    memory_item_source_id TEXT PRIMARY KEY,
    memory_item_id TEXT NOT NULL REFERENCES memory_items(memory_item_id),
    edition_id TEXT REFERENCES editions(edition_id),
    document_id TEXT REFERENCES documents(document_id),
    version_id TEXT REFERENCES document_versions(version_id),
    lesson_id TEXT REFERENCES editorial_lessons(lesson_id),
    relationship TEXT NOT NULL,
    relevance_reason TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS drive_import_jobs (
    import_job_id TEXT PRIMARY KEY,
    source_root_id TEXT NOT NULL,
    source_root_url TEXT NOT NULL,
    snapshot_path TEXT NOT NULL,
    status TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    actor_id TEXT REFERENCES actors(actor_id),
    totals_json TEXT NOT NULL DEFAULT '{}',
    errors_json TEXT NOT NULL DEFAULT '[]',
    resume_of_job_id TEXT REFERENCES drive_import_jobs(import_job_id)
);

CREATE TABLE IF NOT EXISTS drive_import_items (
    import_item_id TEXT PRIMARY KEY,
    import_job_id TEXT NOT NULL REFERENCES drive_import_jobs(import_job_id),
    external_source_id TEXT REFERENCES external_sources(external_source_id),
    external_id TEXT NOT NULL,
    full_path TEXT NOT NULL,
    item_kind TEXT NOT NULL,
    result TEXT NOT NULL,
    error TEXT,
    content_hash TEXT,
    document_id TEXT REFERENCES documents(document_id),
    version_id TEXT REFERENCES document_versions(version_id),
    classification_status TEXT,
    processed_at TEXT NOT NULL,
    UNIQUE (import_job_id, external_id)
);

CREATE TABLE IF NOT EXISTS drive_revisions (
    drive_revision_id TEXT PRIMARY KEY,
    external_source_id TEXT NOT NULL REFERENCES external_sources(external_source_id),
    provider_revision_id TEXT NOT NULL,
    modified_time TEXT,
    author_json TEXT,
    content_path TEXT,
    content_hash TEXT,
    limitation TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    imported_at TEXT NOT NULL,
    UNIQUE (external_source_id, provider_revision_id)
);

CREATE TABLE IF NOT EXISTS drive_comments (
    drive_comment_id TEXT PRIMARY KEY,
    external_source_id TEXT NOT NULL REFERENCES external_sources(external_source_id),
    provider_comment_id TEXT NOT NULL,
    author_json TEXT,
    content TEXT,
    quoted_text TEXT,
    resolved INTEGER CHECK (resolved IN (0, 1)),
    created_time TEXT,
    modified_time TEXT,
    replies_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    imported_at TEXT NOT NULL,
    UNIQUE (external_source_id, provider_comment_id)
);

CREATE TABLE IF NOT EXISTS classification_suggestions (
    classification_suggestion_id TEXT PRIMARY KEY,
    document_id TEXT REFERENCES documents(document_id),
    external_source_id TEXT REFERENCES external_sources(external_source_id),
    suggested_document_type_id TEXT REFERENCES taxonomy_terms(term_id),
    suggested_function_id TEXT REFERENCES taxonomy_terms(term_id),
    suggested_stage_id TEXT REFERENCES taxonomy_terms(term_id),
    suggested_status_id TEXT REFERENCES taxonomy_terms(term_id),
    suggested_edition_title TEXT,
    suggested_meaning TEXT NOT NULL,
    confidence REAL NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    rationale TEXT NOT NULL,
    evidence_json TEXT NOT NULL,
    alternatives_json TEXT NOT NULL DEFAULT '[]',
    status TEXT NOT NULL DEFAULT 'pending',
    reviewed_by TEXT REFERENCES actors(actor_id),
    reviewed_at TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS edition_tags (
    edition_id TEXT NOT NULL REFERENCES editions(edition_id),
    term_id TEXT NOT NULL REFERENCES taxonomy_terms(term_id),
    PRIMARY KEY (edition_id, term_id)
);

CREATE TABLE IF NOT EXISTS document_tags (
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    term_id TEXT NOT NULL REFERENCES taxonomy_terms(term_id),
    PRIMARY KEY (document_id, term_id)
);

CREATE TABLE IF NOT EXISTS agent_runs (
    agent_run_id TEXT PRIMARY KEY,
    edition_id TEXT REFERENCES editions(edition_id),
    actor_id TEXT REFERENCES actors(actor_id),
    agent_name TEXT NOT NULL,
    model TEXT,
    purpose TEXT NOT NULL,
    prompt TEXT NOT NULL,
    context_json TEXT NOT NULL,
    configuration_json TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    evaluation_json TEXT
);

CREATE TABLE IF NOT EXISTS generated_outputs (
    generated_output_id TEXT PRIMARY KEY,
    agent_run_id TEXT REFERENCES agent_runs(agent_run_id),
    edition_id TEXT REFERENCES editions(edition_id),
    document_id TEXT NOT NULL REFERENCES documents(document_id),
    version_id TEXT NOT NULL REFERENCES document_versions(version_id),
    output_type TEXT NOT NULL,
    purpose TEXT NOT NULL,
    result_hash TEXT NOT NULL,
    created_at TEXT NOT NULL,
    discarded INTEGER NOT NULL DEFAULT 0 CHECK (discarded IN (0, 1)),
    final_derived_version_id TEXT REFERENCES document_versions(version_id)
);

CREATE TABLE IF NOT EXISTS access_logs (
    access_log_id TEXT PRIMARY KEY,
    actor_id TEXT REFERENCES actors(actor_id),
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    outcome TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS editorial_search (
    search_row_id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    edition_id TEXT,
    document_id TEXT,
    version_id TEXT,
    memory_tier TEXT,
    status TEXT,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE (entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_documents_edition ON documents(edition_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status_id);
CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(document_type_id);
CREATE INDEX IF NOT EXISTS idx_versions_document ON document_versions(document_id, version_number);
CREATE INDEX IF NOT EXISTS idx_events_edition_time ON editorial_events(edition_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_document_time ON editorial_events(document_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_relationships_source_doc ON document_relationships(source_document_id);
CREATE INDEX IF NOT EXISTS idx_relationships_target_doc ON document_relationships(target_document_id);
CREATE INDEX IF NOT EXISTS idx_memory_tier_status ON memory_items(memory_tier, status);
CREATE INDEX IF NOT EXISTS idx_import_items_result ON drive_import_items(import_job_id, result);
CREATE INDEX IF NOT EXISTS idx_search_filters ON editorial_search(memory_tier, status, entity_type);

CREATE TRIGGER IF NOT EXISTS document_versions_no_update
BEFORE UPDATE ON document_versions
BEGIN
    SELECT RAISE(ABORT, 'document_versions is immutable');
END;

CREATE TRIGGER IF NOT EXISTS document_versions_no_delete
BEFORE DELETE ON document_versions
BEGIN
    SELECT RAISE(ABORT, 'document_versions is immutable');
END;

CREATE TRIGGER IF NOT EXISTS editorial_events_no_update
BEFORE UPDATE ON editorial_events
BEGIN
    SELECT RAISE(ABORT, 'editorial_events is append-only');
END;

CREATE TRIGGER IF NOT EXISTS editorial_events_no_delete
BEFORE DELETE ON editorial_events
BEGIN
    SELECT RAISE(ABORT, 'editorial_events is append-only');
END;

CREATE TRIGGER IF NOT EXISTS approvals_no_update
BEFORE UPDATE ON approvals
BEGIN
    SELECT RAISE(ABORT, 'approvals is append-only; revoke with a new approval');
END;

CREATE TRIGGER IF NOT EXISTS approvals_no_delete
BEFORE DELETE ON approvals
BEGIN
    SELECT RAISE(ABORT, 'approvals is append-only');
END;
