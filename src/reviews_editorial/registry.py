"""Registro editorial central: versões, eventos, linhagem e memória institucional."""

from __future__ import annotations

import json
import os
import re
import shutil
import sqlite3
import uuid
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator

from .classification import classify_drive_item
from .documents import DocumentNormalizationError, extract_docx
from .feedback import compare_versions
from .io import load_data, sha256_file
from .jobs import utc_now
from .taxonomy import iter_taxonomy_terms


ROLE_PERMISSIONS = {
    "approve_version": {"administrator", "editor", "auditor"},
    "publish_version": {"administrator", "editor"},
    "promote_memory": {"administrator", "editor"},
    "approve_lesson": {"administrator", "editor"},
    "correct_classification": {"administrator", "editor"},
    "edit_taxonomy": {"administrator"},
    "archive_edition": {"administrator"},
    "write": {
        "administrator",
        "editor",
        "methodological_reviewer",
        "editorial_reviewer",
        "auditor",
        "contributor",
        "agent",
    },
    "read": {
        "administrator",
        "editor",
        "methodological_reviewer",
        "editorial_reviewer",
        "auditor",
        "contributor",
        "viewer",
        "agent",
    },
}

MILESTONE_REASONS_REQUIRED = {
    "sent_for_review",
    "review_started",
    "changes_requested",
    "corrections_completed",
    "audit_started",
    "audit_completed",
    "approved",
    "exported",
    "published",
    "post_publication_correction",
}


class RegistryPermissionError(PermissionError):
    """Ação recusada pelo papel editorial."""


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _stable_id(prefix: str, *parts: object) -> str:
    seed = "|".join(str(part) for part in parts)
    return f"{prefix}-{uuid.uuid5(uuid.NAMESPACE_URL, f'reviews:{seed}')}"


def _new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4()}"


def _safe_name(value: str) -> str:
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", value).strip(" .")
    if len(name) <= 120:
        return name or "document"
    suffix = Path(name).suffix
    stem_limit = max(1, 120 - len(suffix))
    return (name[:stem_limit].rstrip(" .") + suffix) or "document"


def _read_text_best_effort(path: Path) -> tuple[str | None, dict[str, Any]]:
    suffix = path.suffix.casefold()
    if suffix in {".md", ".mdx", ".txt", ".json", ".yml", ".yaml", ".csv", ".html", ".htm"}:
        for encoding in ("utf-8-sig", "utf-8", "cp1252"):
            try:
                return path.read_text(encoding=encoding), {"extraction": "plain-text"}
            except UnicodeDecodeError:
                continue
        return None, {"extraction_error": "codificação textual não reconhecida"}
    if suffix == ".docx":
        try:
            extracted = extract_docx(path)
            return str(extracted.get("text") or ""), {
                "extraction": "docx-xml",
                "pagination": extracted.get("pagination"),
                "review_signals": extracted.get("review_signals"),
            }
        except (OSError, DocumentNormalizationError, ValueError, zipfile.BadZipFile) as exc:
            return None, {"extraction_error": str(exc)}
    return None, {"extraction": "not-attempted-for-format"}


class EditorialRegistry:
    """Serviço transacional do registro local privado."""

    def __init__(
        self,
        database_path: str | Path,
        *,
        storage_root: str | Path | None = None,
        migrations_root: str | Path | None = None,
    ) -> None:
        self.database_path = Path(database_path).resolve()
        self.storage_root = (
            Path(storage_root).resolve()
            if storage_root is not None
            else self.database_path.parent / "storage"
        )
        self.migrations_root = (
            Path(migrations_root).resolve()
            if migrations_root is not None
            else Path(__file__).resolve().parents[2] / "migrations"
        )
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.migrate()
        self.seed_taxonomy()

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def migrate(self) -> list[str]:
        applied: list[str] = []
        scripts = sorted(self.migrations_root.glob("*.sql"))
        if not scripts:
            raise FileNotFoundError(f"Nenhuma migração em {self.migrations_root}")
        with self.connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            known = {
                row["version"]
                for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for script in scripts:
                if script.name in known:
                    continue
                connection.executescript(script.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (script.name, utc_now()),
                )
                applied.append(script.name)
        return applied

    def seed_taxonomy(self) -> None:
        now = utc_now()
        with self.connection() as connection:
            for term in iter_taxonomy_terms():
                connection.execute(
                    """
                    INSERT INTO taxonomy_terms(
                        term_id, vocabulary, label, parent_id, description,
                        active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 1, ?, ?)
                    ON CONFLICT(term_id) DO UPDATE SET
                        vocabulary=excluded.vocabulary,
                        label=excluded.label,
                        parent_id=excluded.parent_id,
                        description=excluded.description,
                        updated_at=excluded.updated_at
                    """,
                    (
                        term["term_id"],
                        term["vocabulary"],
                        term["label"],
                        term["parent_id"],
                        term["description"],
                        now,
                        now,
                    ),
                )

    def ensure_actor(
        self,
        actor_id: str,
        *,
        display_name: str | None = None,
        role: str = "contributor",
        external_identity: str | None = None,
    ) -> str:
        if role not in ROLE_PERMISSIONS["read"]:
            raise ValueError(f"Papel editorial inválido: {role}")
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO actors(
                    actor_id, display_name, role, external_identity, created_at
                ) VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(actor_id) DO UPDATE SET
                    display_name=excluded.display_name,
                    external_identity=COALESCE(excluded.external_identity, actors.external_identity)
                """,
                (actor_id, display_name or actor_id, role, external_identity, utc_now()),
            )
        return actor_id

    def actor_role(self, actor_id: str) -> str:
        with self.connection() as connection:
            row = connection.execute(
                "SELECT role FROM actors WHERE actor_id=? AND deleted_at IS NULL",
                (actor_id,),
            ).fetchone()
        if row is None:
            raise RegistryPermissionError(f"Ator não registrado: {actor_id}")
        return str(row["role"])

    def authorize(self, actor_id: str, action: str) -> None:
        allowed = ROLE_PERMISSIONS.get(action)
        if allowed is None:
            raise ValueError(f"Ação desconhecida: {action}")
        role = self.actor_role(actor_id)
        if role not in allowed:
            self.log_access(
                actor_id=actor_id,
                action=action,
                entity_type="permission",
                entity_id=action,
                outcome="denied",
                metadata={"role": role},
            )
            raise RegistryPermissionError(
                f"O papel {role!r} não pode executar {action!r}"
            )

    def log_access(
        self,
        *,
        actor_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str,
        outcome: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        log_id = _new_id("ACCESS")
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO access_logs(
                    access_log_id, actor_id, action, entity_type, entity_id,
                    occurred_at, outcome, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    log_id,
                    actor_id,
                    action,
                    entity_type,
                    entity_id,
                    utc_now(),
                    outcome,
                    _json(metadata or {}),
                ),
            )
        return log_id

    def append_event(
        self,
        *,
        entity_type: str,
        entity_id: str,
        event_type: str,
        justification: str,
        origin: str,
        actor_id: str | None = None,
        agent_id: str | None = None,
        edition_id: str | None = None,
        document_id: str | None = None,
        version_id: str | None = None,
        before: Any = None,
        after: Any = None,
        correlation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        connection: sqlite3.Connection | None = None,
    ) -> str:
        if not justification.strip():
            raise ValueError("justification é obrigatória em eventos editoriais")
        event_id = _new_id("EVT")
        values = (
            event_id,
            entity_type,
            entity_id,
            edition_id,
            document_id,
            version_id,
            event_type,
            actor_id,
            agent_id,
            utc_now(),
            _json(before) if before is not None else None,
            _json(after) if after is not None else None,
            justification.strip(),
            origin,
            correlation_id,
            _json(metadata or {}),
        )
        sql = """
            INSERT INTO editorial_events(
                event_id, entity_type, entity_id, edition_id, document_id,
                version_id, event_type, actor_id, agent_id, occurred_at,
                before_json, after_json, justification, origin,
                correlation_id, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        if connection is not None:
            connection.execute(sql, values)
        else:
            with self.connection() as owned:
                owned.execute(sql, values)
        return event_id

    def upsert_edition(
        self,
        *,
        edition_id: str,
        canonical_title: str,
        status: str,
        editorial_meaning: str,
        actor_id: str,
        job_id: str | None = None,
        source_path: str | None = None,
        summary: str | None = None,
        meaning_confidence: float = 0.0,
        confirmed: bool = False,
    ) -> str:
        self.authorize(actor_id, "write")
        now = utc_now()
        with self.connection() as connection:
            before = connection.execute(
                "SELECT * FROM editions WHERE edition_id=?", (edition_id,)
            ).fetchone()
            connection.execute(
                """
                INSERT INTO editions(
                    edition_id, canonical_title, summary, status,
                    editorial_meaning, meaning_confidence, job_id, source_path,
                    created_at, updated_at, confirmed_by, confirmed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(edition_id) DO UPDATE SET
                    canonical_title=excluded.canonical_title,
                    summary=COALESCE(excluded.summary, editions.summary),
                    status=excluded.status,
                    editorial_meaning=excluded.editorial_meaning,
                    meaning_confidence=excluded.meaning_confidence,
                    job_id=COALESCE(excluded.job_id, editions.job_id),
                    source_path=COALESCE(excluded.source_path, editions.source_path),
                    updated_at=excluded.updated_at,
                    confirmed_by=COALESCE(excluded.confirmed_by, editions.confirmed_by),
                    confirmed_at=COALESCE(excluded.confirmed_at, editions.confirmed_at)
                """,
                (
                    edition_id,
                    canonical_title.strip(),
                    summary,
                    status,
                    editorial_meaning.strip(),
                    meaning_confidence,
                    job_id,
                    source_path,
                    now,
                    now,
                    actor_id if confirmed else None,
                    now if confirmed else None,
                ),
            )
            self.append_event(
                entity_type="edition",
                entity_id=edition_id,
                edition_id=edition_id,
                event_type="edition_created" if before is None else "edition_updated",
                actor_id=actor_id,
                justification="Edição registrada ou sincronizada com o fluxo editorial.",
                origin="registry",
                before=dict(before) if before else None,
                after={
                    "canonical_title": canonical_title,
                    "status": status,
                    "job_id": job_id,
                },
                connection=connection,
            )
        return edition_id

    def create_document(
        self,
        *,
        external_key: str,
        canonical_title: str,
        original_name: str,
        actor_id: str,
        edition_id: str | None = None,
        document_type_id: str = "type.unknown",
        editorial_function_id: str = "function.unclassified",
        stage_id: str = "stage.awaiting_classification",
        status_id: str = "status.classification_pending",
        editorial_meaning: str,
        confidence: float = 0.0,
        confirmed: bool = False,
        notes: str | None = None,
    ) -> str:
        self.authorize(actor_id, "write")
        document_id = _stable_id("DOC", external_key)
        now = utc_now()
        with self.connection() as connection:
            existing = connection.execute(
                "SELECT document_id FROM documents WHERE external_key=?",
                (external_key,),
            ).fetchone()
            if existing is not None:
                return str(existing["document_id"])
            connection.execute(
                """
                INSERT INTO documents(
                    document_id, edition_id, external_key, canonical_title,
                    original_name, document_type_id, editorial_function_id,
                    stage_id, status_id, editorial_meaning, meaning_confidence,
                    classification_confidence, classification_confirmed,
                    classification_confirmed_by, classification_confirmed_at,
                    revision_required, reusable, validated_memory_eligible,
                    known_errors, unverified_data, notes, created_at, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                    1, 0, 0, 0, 1, ?, ?, ?
                )
                """,
                (
                    document_id,
                    edition_id,
                    external_key,
                    canonical_title,
                    original_name,
                    document_type_id,
                    editorial_function_id,
                    stage_id,
                    status_id,
                    editorial_meaning,
                    confidence,
                    confidence,
                    int(confirmed),
                    actor_id if confirmed else None,
                    now if confirmed else None,
                    notes,
                    now,
                    now,
                ),
            )
            self.append_event(
                entity_type="document",
                entity_id=document_id,
                edition_id=edition_id,
                document_id=document_id,
                event_type="document_created",
                actor_id=actor_id,
                justification="Documento registrado com identidade editorial explícita.",
                origin="registry",
                after={
                    "external_key": external_key,
                    "document_type_id": document_type_id,
                    "status_id": status_id,
                    "classification_confirmed": confirmed,
                },
                connection=connection,
            )
        return document_id

    def create_classification_suggestion(
        self,
        *,
        document_id: str,
        external_source_id: str | None,
        classification: dict[str, Any],
        actor_id: str,
    ) -> str:
        self.authorize(actor_id, "write")
        suggestion_id = _stable_id(
            "CLS",
            document_id,
            classification["document_type_id"],
            classification["stage_id"],
            classification["status_id"],
        )
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO classification_suggestions(
                    classification_suggestion_id, document_id, external_source_id,
                    suggested_document_type_id, suggested_function_id,
                    suggested_stage_id, suggested_status_id, suggested_edition_title,
                    suggested_meaning, confidence, rationale, evidence_json,
                    alternatives_json, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                ON CONFLICT(classification_suggestion_id) DO NOTHING
                """,
                (
                    suggestion_id,
                    document_id,
                    external_source_id,
                    classification["document_type_id"],
                    classification["editorial_function_id"],
                    classification["stage_id"],
                    classification["status_id"],
                    classification.get("suggested_edition_title"),
                    classification["editorial_meaning"],
                    classification["confidence"],
                    classification["rationale"],
                    _json(classification.get("evidence") or []),
                    _json(classification.get("alternatives") or []),
                    utc_now(),
                ),
            )
        return suggestion_id

    def correct_classification(
        self,
        *,
        document_id: str,
        actor_id: str,
        document_type_id: str,
        editorial_function_id: str,
        stage_id: str,
        status_id: str,
        editorial_meaning: str,
        justification: str,
    ) -> None:
        self.authorize(actor_id, "correct_classification")
        with self.connection() as connection:
            before = connection.execute(
                "SELECT * FROM documents WHERE document_id=?", (document_id,)
            ).fetchone()
            if before is None:
                raise KeyError(document_id)
            connection.execute(
                """
                UPDATE documents SET
                    document_type_id=?, editorial_function_id=?, stage_id=?,
                    status_id=?, editorial_meaning=?,
                    classification_confidence=1.0, classification_confirmed=1,
                    classification_confirmed_by=?, classification_confirmed_at=?,
                    updated_at=?
                WHERE document_id=?
                """,
                (
                    document_type_id,
                    editorial_function_id,
                    stage_id,
                    status_id,
                    editorial_meaning,
                    actor_id,
                    utc_now(),
                    utc_now(),
                    document_id,
                ),
            )
            self.append_event(
                entity_type="document",
                entity_id=document_id,
                edition_id=before["edition_id"],
                document_id=document_id,
                event_type="classification_corrected",
                actor_id=actor_id,
                justification=justification,
                origin="human",
                before=dict(before),
                after={
                    "document_type_id": document_type_id,
                    "editorial_function_id": editorial_function_id,
                    "stage_id": stage_id,
                    "status_id": status_id,
                },
                connection=connection,
            )

    def create_version(
        self,
        *,
        document_id: str,
        content_hash: str,
        actor_id: str,
        reason: str,
        change_summary: str,
        status_id: str,
        editorial_meaning: str,
        content_text: str | None = None,
        content_path: str | None = None,
        source_kind: str = "generated",
        meaning_confidence: float = 0.0,
        previous_version_id: str | None = None,
        restored_from_version_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        agent_id: str | None = None,
    ) -> str:
        self.authorize(actor_id, "write")
        if not reason.strip():
            raise ValueError("reason é obrigatório ao criar uma versão")
        with self.connection() as connection:
            document = connection.execute(
                "SELECT edition_id, canonical_title FROM documents WHERE document_id=?",
                (document_id,),
            ).fetchone()
            if document is None:
                raise KeyError(document_id)
            existing = connection.execute(
                "SELECT version_id FROM document_versions WHERE document_id=? AND content_hash=?",
                (document_id, content_hash),
            ).fetchone()
            if existing is not None:
                return str(existing["version_id"])
            last = connection.execute(
                """
                SELECT version_id, version_number FROM document_versions
                WHERE document_id=? ORDER BY version_number DESC LIMIT 1
                """,
                (document_id,),
            ).fetchone()
            version_number = int(last["version_number"]) + 1 if last else 1
            if previous_version_id is None and last is not None:
                previous_version_id = str(last["version_id"])
            version_id = _stable_id("VER", document_id, version_number, content_hash)
            connection.execute(
                """
                INSERT INTO document_versions(
                    version_id, document_id, version_number, previous_version_id,
                    restored_from_version_id, author_actor_id, agent_id,
                    created_at, reason, change_summary, status_id,
                    editorial_meaning, meaning_confidence, content_text,
                    content_path, content_hash, source_kind, approval_status,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'not_submitted', ?)
                """,
                (
                    version_id,
                    document_id,
                    version_number,
                    previous_version_id,
                    restored_from_version_id,
                    actor_id,
                    agent_id,
                    utc_now(),
                    reason.strip(),
                    change_summary.strip(),
                    status_id,
                    editorial_meaning,
                    meaning_confidence,
                    content_text,
                    content_path,
                    content_hash,
                    source_kind,
                    _json(metadata or {}),
                ),
            )
            connection.execute(
                "UPDATE documents SET status_id=?, editorial_meaning=?, updated_at=? "
                "WHERE document_id=?",
                (status_id, editorial_meaning, utc_now(), document_id),
            )
            self.append_event(
                entity_type="document_version",
                entity_id=version_id,
                edition_id=document["edition_id"],
                document_id=document_id,
                version_id=version_id,
                event_type="version_created",
                actor_id=actor_id,
                agent_id=agent_id,
                justification=reason,
                origin=source_kind,
                before={"previous_version_id": previous_version_id},
                after={
                    "version_number": version_number,
                    "content_hash": content_hash,
                    "status_id": status_id,
                },
                connection=connection,
            )
            memory_item_id = _stable_id("MEM", version_id, "historical")
            connection.execute(
                """
                INSERT INTO memory_items(
                    memory_item_id, memory_tier, category, title, content, status,
                    scope, confidence, normative, justification, created_at
                ) VALUES (?, 'historical', 'memory.historical_artifact', ?, ?, ?, ?, ?, 0, ?, ?)
                """,
                (
                    memory_item_id,
                    f"{document['canonical_title']} — versão {version_number}",
                    content_text or editorial_meaning,
                    status_id,
                    "audit_and_traceability_only",
                    meaning_confidence,
                    "Versão preservada automaticamente na memória histórica; sem força normativa.",
                    utc_now(),
                ),
            )
            connection.execute(
                """
                INSERT INTO memory_item_sources(
                    memory_item_source_id, memory_item_id, edition_id,
                    document_id, version_id, relationship, relevance_reason
                ) VALUES (?, ?, ?, ?, ?, 'origin', ?)
                """,
                (
                    _stable_id("MEMSRC", memory_item_id, version_id),
                    memory_item_id,
                    document["edition_id"],
                    document_id,
                    version_id,
                    "A versão é a fonte integral deste item histórico.",
                ),
            )
            self._upsert_search(
                connection,
                entity_type="version",
                entity_id=version_id,
                edition_id=document["edition_id"],
                document_id=document_id,
                version_id=version_id,
                memory_tier="historical",
                status=status_id,
                title=f"{document['canonical_title']} — versão {version_number}",
                body=content_text or editorial_meaning,
                provenance={
                    "edition_id": document["edition_id"],
                    "document_id": document_id,
                    "version_id": version_id,
                },
            )
        return version_id

    def _upsert_search(
        self,
        connection: sqlite3.Connection,
        *,
        entity_type: str,
        entity_id: str,
        edition_id: str | None,
        document_id: str | None,
        version_id: str | None,
        memory_tier: str | None,
        status: str | None,
        title: str,
        body: str,
        provenance: dict[str, Any],
    ) -> None:
        connection.execute(
            """
            INSERT INTO editorial_search(
                search_row_id, entity_type, entity_id, edition_id, document_id,
                version_id, memory_tier, status, title, body,
                provenance_json, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(entity_type, entity_id) DO UPDATE SET
                edition_id=excluded.edition_id,
                document_id=excluded.document_id,
                version_id=excluded.version_id,
                memory_tier=excluded.memory_tier,
                status=excluded.status,
                title=excluded.title,
                body=excluded.body,
                provenance_json=excluded.provenance_json,
                updated_at=excluded.updated_at
            """,
            (
                _stable_id("SEARCH", entity_type, entity_id),
                entity_type,
                entity_id,
                edition_id,
                document_id,
                version_id,
                memory_tier,
                status,
                title,
                body,
                _json(provenance),
                utc_now(),
            ),
        )

    def preserve_file(
        self,
        source_path: str | Path,
        *,
        document_id: str,
        version_id: str,
        external_source_id: str | None = None,
        original_filename: str | None = None,
        mime_type: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        source = Path(source_path).resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        digest = sha256_file(source)
        original = original_filename or source.name
        suffix = Path(original).suffix or source.suffix
        filename = f"content-{digest[:16]}{suffix.casefold()}"
        destination = self.storage_root / "documents" / document_id / digest / filename
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            if sha256_file(destination) != digest:
                raise RuntimeError(f"Colisão de armazenamento em {destination}")
        else:
            shutil.copy2(source, destination)
        content_text, extraction_meta = _read_text_best_effort(destination)
        normalized_path: Path | None = None
        if content_text is not None:
            normalized_path = (
                self.storage_root
                / "normalized"
                / document_id
                / f"{digest}.txt"
            )
            normalized_path.parent.mkdir(parents=True, exist_ok=True)
            if not normalized_path.exists():
                normalized_path.write_text(content_text, encoding="utf-8", newline="\n")
        file_id = _stable_id("FILE", version_id, digest, filename)
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO document_files(
                    document_file_id, document_id, version_id, external_source_id,
                    storage_path, normalized_text_path, original_filename, mime_type,
                    extension, size_bytes, content_hash, imported_at, private, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?)
                ON CONFLICT(version_id, storage_path) DO NOTHING
                """,
                (
                    file_id,
                    document_id,
                    version_id,
                    external_source_id,
                    str(destination),
                    str(normalized_path) if normalized_path else None,
                    original,
                    mime_type,
                    source.suffix.casefold().lstrip("."),
                    source.stat().st_size,
                    digest,
                    utc_now(),
                    _json({**(metadata or {}), **extraction_meta}),
                ),
            )
            if external_source_id:
                connection.execute(
                    """
                    INSERT INTO document_file_sources(
                        document_file_source_id, document_file_id,
                        external_source_id, source_context_path,
                        associated_at, metadata_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(document_file_id, external_source_id) DO NOTHING
                    """,
                    (
                        _stable_id("FILESRC", file_id, external_source_id),
                        file_id,
                        external_source_id,
                        (metadata or {}).get("drive_path"),
                        utc_now(),
                        _json(metadata or {}),
                    ),
                )
        return file_id

    def add_relationship(
        self,
        *,
        relationship_type: str,
        actor_id: str,
        rationale: str,
        source_document_id: str | None = None,
        source_version_id: str | None = None,
        target_document_id: str | None = None,
        target_version_id: str | None = None,
        confidence: float = 1.0,
        confirmed: bool = False,
    ) -> str:
        self.authorize(actor_id, "write")
        relationship_id = _stable_id(
            "REL",
            relationship_type,
            source_document_id,
            source_version_id,
            target_document_id,
            target_version_id,
        )
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO document_relationships(
                    relationship_id, relationship_type, source_document_id,
                    source_version_id, target_document_id, target_version_id,
                    confidence, confirmed, rationale, created_by, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(relationship_id) DO NOTHING
                """,
                (
                    relationship_id,
                    relationship_type,
                    source_document_id,
                    source_version_id,
                    target_document_id,
                    target_version_id,
                    confidence,
                    int(confirmed),
                    rationale,
                    actor_id,
                    utc_now(),
                ),
            )
            document_id = source_document_id or target_document_id
            edition = None
            if document_id:
                row = connection.execute(
                    "SELECT edition_id FROM documents WHERE document_id=?", (document_id,)
                ).fetchone()
                edition = row["edition_id"] if row else None
            self.append_event(
                entity_type="relationship",
                entity_id=relationship_id,
                edition_id=edition,
                document_id=document_id,
                event_type="relationship_created",
                actor_id=actor_id,
                justification=rationale,
                origin="registry",
                after={"relationship_type": relationship_type, "confirmed": confirmed},
                connection=connection,
            )
        return relationship_id

    def restore_version(
        self,
        version_id: str,
        *,
        actor_id: str,
        reason: str,
    ) -> str:
        self.authorize(actor_id, "write")
        with self.connection() as connection:
            source = connection.execute(
                "SELECT * FROM document_versions WHERE version_id=?", (version_id,)
            ).fetchone()
        if source is None:
            raise KeyError(version_id)
        restore_marker = _json({"restored_from": version_id, "at": utc_now(), "reason": reason})
        restore_hash = uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"{source['content_hash']}|{restore_marker}",
        ).hex.ljust(64, "0")[:64]
        return self.create_version(
            document_id=source["document_id"],
            content_hash=restore_hash,
            actor_id=actor_id,
            reason=reason,
            change_summary=f"Restauração derivada de {version_id}; a história anterior foi preservada.",
            status_id=source["status_id"],
            editorial_meaning=source["editorial_meaning"],
            content_text=source["content_text"],
            content_path=source["content_path"],
            source_kind="restoration",
            meaning_confidence=source["meaning_confidence"],
            restored_from_version_id=version_id,
            metadata={"restored_source_hash": source["content_hash"]},
        )

    def compare_and_record_versions(
        self,
        from_version_id: str,
        to_version_id: str,
        *,
        actor_id: str,
    ) -> dict[str, Any]:
        self.authorize(actor_id, "read")
        with self.connection() as connection:
            rows = connection.execute(
                """
                SELECT version_id, content_text, content_path FROM document_versions
                WHERE version_id IN (?, ?)
                """,
                (from_version_id, to_version_id),
            ).fetchall()
        versions = {row["version_id"]: row for row in rows}
        if set(versions) != {from_version_id, to_version_id}:
            raise KeyError("Uma ou ambas as versões não existem")
        before = versions[from_version_id]["content_text"] or ""
        after = versions[to_version_id]["content_text"] or ""
        report = compare_versions(before, after)
        diff_id = _stable_id("DIFF", from_version_id, to_version_id)
        semantic = {
            "interpretation_changes": report.get("interpretation_changes", []),
            "reference_changes": report.get("reference_changes", []),
            "structural_changes": report.get("structural_changes", []),
        }
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO version_diffs(
                    version_diff_id, from_version_id, to_version_id,
                    literal_diff_json, semantic_diff_json, numeric_changes_json,
                    created_at, created_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(from_version_id, to_version_id) DO NOTHING
                """,
                (
                    diff_id,
                    from_version_id,
                    to_version_id,
                    _json(
                        {
                            "similarity_ratio": report["similarity_ratio"],
                            "unified_diff": report["unified_diff"],
                            "changes": report["changes"],
                        }
                    ),
                    _json(semantic),
                    _json(report.get("numeric_changes", [])),
                    utc_now(),
                    actor_id,
                ),
            )
        return {**report, "version_diff_id": diff_id}

    def approve_version(
        self,
        version_id: str,
        *,
        actor_id: str,
        rationale: str,
        approval_type: str = "editorial",
    ) -> str:
        self.authorize(actor_id, "approve_version")
        if not rationale.strip():
            raise ValueError("A aprovação exige rationale")
        with self.connection() as connection:
            version = connection.execute(
                """
                SELECT v.*, d.edition_id FROM document_versions v
                JOIN documents d ON d.document_id=v.document_id
                WHERE v.version_id=?
                """,
                (version_id,),
            ).fetchone()
            if version is None:
                raise KeyError(version_id)
            approval_id = _new_id("APR")
            connection.execute(
                """
                INSERT INTO approvals(
                    approval_id, edition_id, document_id, version_id,
                    approval_type, decision, actor_id, rationale, created_at
                ) VALUES (?, ?, ?, ?, ?, 'approved', ?, ?, ?)
                """,
                (
                    approval_id,
                    version["edition_id"],
                    version["document_id"],
                    version_id,
                    approval_type,
                    actor_id,
                    rationale,
                    utc_now(),
                ),
            )
            self.append_event(
                entity_type="document_version",
                entity_id=version_id,
                edition_id=version["edition_id"],
                document_id=version["document_id"],
                version_id=version_id,
                event_type="document_approved",
                actor_id=actor_id,
                justification=rationale,
                origin="human",
                after={"approval_id": approval_id, "approval_type": approval_type},
                connection=connection,
            )
        return approval_id

    def publish_version(
        self,
        version_id: str,
        *,
        actor_id: str,
        rationale: str,
        destination: str | None = None,
        external_url: str | None = None,
        correction_of_publication_id: str | None = None,
    ) -> str:
        self.authorize(actor_id, "publish_version")
        with self.connection() as connection:
            version = connection.execute(
                """
                SELECT v.version_id, v.document_id, d.edition_id
                FROM document_versions v
                JOIN documents d ON d.document_id=v.document_id
                WHERE v.version_id=?
                """,
                (version_id,),
            ).fetchone()
            if version is None:
                raise KeyError(version_id)
            approval = connection.execute(
                """
                SELECT approval_id FROM approvals
                WHERE version_id=? AND decision='approved'
                ORDER BY created_at DESC LIMIT 1
                """,
                (version_id,),
            ).fetchone()
            if approval is None:
                raise RegistryPermissionError(
                    "A publicação exige aprovação explícita da versão exata"
                )
            publication_id = _new_id("PUB")
            connection.execute(
                """
                INSERT INTO publication_records(
                    publication_id, edition_id, document_id, version_id,
                    approval_id, published_by, published_at, destination,
                    external_url, correction_of_publication_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    publication_id,
                    version["edition_id"],
                    version["document_id"],
                    version_id,
                    approval["approval_id"],
                    actor_id,
                    utc_now(),
                    destination,
                    external_url,
                    correction_of_publication_id,
                ),
            )
            self.append_event(
                entity_type="publication",
                entity_id=publication_id,
                edition_id=version["edition_id"],
                document_id=version["document_id"],
                version_id=version_id,
                event_type="edition_published",
                actor_id=actor_id,
                justification=rationale,
                origin="human",
                after={
                    "version_id": version_id,
                    "approval_id": approval["approval_id"],
                    "destination": destination,
                },
                connection=connection,
            )
        return publication_id

    def propose_lesson(
        self,
        *,
        title: str,
        content: str,
        lesson_type: str,
        scope: str,
        actor_id: str,
        rationale: str,
        confidence: float,
        source_version_ids: Iterable[str] = (),
    ) -> str:
        self.authorize(actor_id, "write")
        lesson_id = _new_id("LESSON")
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO editorial_lessons(
                    lesson_id, title, content, lesson_type, status, scope,
                    confidence, proposed_by, proposed_at, rationale
                ) VALUES (?, ?, ?, ?, 'proposed', ?, ?, ?, ?, ?)
                """,
                (
                    lesson_id,
                    title,
                    content,
                    lesson_type,
                    scope,
                    confidence,
                    actor_id,
                    utc_now(),
                    rationale,
                ),
            )
            for version_id in source_version_ids:
                row = connection.execute(
                    """
                    SELECT v.document_id, d.edition_id
                    FROM document_versions v JOIN documents d ON d.document_id=v.document_id
                    WHERE v.version_id=?
                    """,
                    (version_id,),
                ).fetchone()
                if row is None:
                    raise KeyError(version_id)
                memory_id = _stable_id("MEM", lesson_id, version_id, "proposed")
                connection.execute(
                    """
                    INSERT INTO memory_items(
                        memory_item_id, memory_tier, category, title, content,
                        status, scope, confidence, normative, justification, created_at
                    ) VALUES (?, 'historical', ?, ?, ?, 'proposed', ?, ?, 0, ?, ?)
                    """,
                    (
                        memory_id,
                        lesson_type,
                        title,
                        content,
                        scope,
                        confidence,
                        "Lição proposta por IA ou humano; aguarda aprovação e não é normativa.",
                        utc_now(),
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO memory_item_sources(
                        memory_item_source_id, memory_item_id, edition_id,
                        document_id, version_id, lesson_id, relationship,
                        relevance_reason
                    ) VALUES (?, ?, ?, ?, ?, ?, 'evidence', ?)
                    """,
                    (
                        _stable_id("MEMSRC", memory_id, version_id),
                        memory_id,
                        row["edition_id"],
                        row["document_id"],
                        version_id,
                        lesson_id,
                        rationale,
                    ),
                )
            self.append_event(
                entity_type="editorial_lesson",
                entity_id=lesson_id,
                event_type="editorial_lesson_proposed",
                actor_id=actor_id,
                justification=rationale,
                origin="human_or_agent_proposal",
                after={"status": "proposed", "scope": scope},
                connection=connection,
            )
        return lesson_id

    def approve_lesson(
        self,
        lesson_id: str,
        *,
        actor_id: str,
        rationale: str,
    ) -> str:
        self.authorize(actor_id, "approve_lesson")
        with self.connection() as connection:
            lesson = connection.execute(
                "SELECT * FROM editorial_lessons WHERE lesson_id=?", (lesson_id,)
            ).fetchone()
            if lesson is None:
                raise KeyError(lesson_id)
            source_versions = [
                row["version_id"]
                for row in connection.execute(
                    """
                    SELECT DISTINCT mis.version_id
                    FROM memory_item_sources mis
                    JOIN memory_items mi ON mi.memory_item_id=mis.memory_item_id
                    WHERE mis.lesson_id=? AND mis.version_id IS NOT NULL
                    """,
                    (lesson_id,),
                )
            ]
            if not source_versions:
                raise RegistryPermissionError(
                    "LiÃ§Ã£o sem versÃ£o-fonte nÃ£o pode entrar na memÃ³ria validada"
                )
            unapproved = [
                version_id
                for version_id in source_versions
                if connection.execute(
                    """
                    SELECT 1
                    FROM document_versions v
                    JOIN approvals a ON a.version_id=v.version_id
                    WHERE v.version_id=?
                      AND a.decision='approved'
                      AND v.status_id NOT IN (
                          'status.preliminary',
                          'status.unverified',
                          'status.rejected',
                          'status.do_not_use'
                      )
                    LIMIT 1
                    """,
                    (version_id,),
                ).fetchone()
                is None
            ]
            if unapproved:
                raise RegistryPermissionError(
                    "LiÃ§Ã£o baseada em versÃ£o nÃ£o aprovada nÃ£o pode entrar "
                    f"na memÃ³ria validada: {unapproved}"
                )
            connection.execute(
                """
                UPDATE editorial_lessons
                SET status='approved', approved_by=?, approved_at=?
                WHERE lesson_id=?
                """,
                (actor_id, utc_now(), lesson_id),
            )
        return self.promote_memory(
            actor_id=actor_id,
            title=lesson["title"],
            content=lesson["content"],
            category=lesson["lesson_type"],
            scope=lesson["scope"],
            confidence=lesson["confidence"],
            justification=rationale,
            lesson_id=lesson_id,
        )

    def promote_memory(
        self,
        *,
        actor_id: str,
        title: str,
        content: str,
        category: str,
        scope: str,
        confidence: float,
        justification: str,
        edition_id: str | None = None,
        document_id: str | None = None,
        version_id: str | None = None,
        lesson_id: str | None = None,
        positive_examples: list[str] | None = None,
        counterexamples: list[str] | None = None,
        not_applicable_when: str | None = None,
    ) -> str:
        self.authorize(actor_id, "promote_memory")
        if lesson_id is not None:
            with self.connection() as connection:
                lesson = connection.execute(
                    """
                    SELECT status FROM editorial_lessons
                    WHERE lesson_id=? AND deleted_at IS NULL
                    """,
                    (lesson_id,),
                ).fetchone()
            if lesson is None:
                raise KeyError(lesson_id)
            if lesson["status"] != "approved":
                raise RegistryPermissionError(
                    "LiÃ§Ã£o proposta ou rejeitada nÃ£o pode entrar na memÃ³ria validada"
                )
        if version_id is not None:
            with self.connection() as connection:
                version = connection.execute(
                    """
                    SELECT v.document_id, v.status_id, d.edition_id
                    FROM document_versions v JOIN documents d ON d.document_id=v.document_id
                    WHERE v.version_id=?
                    """,
                    (version_id,),
                ).fetchone()
                approval = connection.execute(
                    "SELECT 1 FROM approvals WHERE version_id=? AND decision='approved' LIMIT 1",
                    (version_id,),
                ).fetchone()
            if version is None:
                raise KeyError(version_id)
            if approval is None:
                raise RegistryPermissionError(
                    "Versão não aprovada não pode entrar na memória validada"
                )
            if version["status_id"] in {
                "status.preliminary",
                "status.unverified",
                "status.rejected",
                "status.do_not_use",
            }:
                raise RegistryPermissionError(
                    "Rascunho, fonte nÃ£o verificada ou versÃ£o rejeitada nÃ£o pode "
                    "entrar na memÃ³ria validada"
                )
            document_id = document_id or version["document_id"]
            edition_id = edition_id or version["edition_id"]
        memory_id = _new_id("MEM")
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO memory_items(
                    memory_item_id, memory_tier, category, title, content,
                    status, scope, confidence, normative, approved_by, approved_at,
                    justification, positive_examples_json, counterexamples_json,
                    not_applicable_when, created_at
                ) VALUES (?, 'validated', ?, ?, ?, 'active', ?, ?, 1, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    memory_id,
                    category,
                    title,
                    content,
                    scope,
                    confidence,
                    actor_id,
                    utc_now(),
                    justification,
                    _json(positive_examples or []),
                    _json(counterexamples or []),
                    not_applicable_when,
                    utc_now(),
                ),
            )
            connection.execute(
                """
                INSERT INTO memory_item_sources(
                    memory_item_source_id, memory_item_id, edition_id,
                    document_id, version_id, lesson_id, relationship,
                    relevance_reason
                ) VALUES (?, ?, ?, ?, ?, ?, 'validated_origin', ?)
                """,
                (
                    _stable_id("MEMSRC", memory_id, version_id, lesson_id),
                    memory_id,
                    edition_id,
                    document_id,
                    version_id,
                    lesson_id,
                    justification,
                ),
            )
            self._upsert_search(
                connection,
                entity_type="memory",
                entity_id=memory_id,
                edition_id=edition_id,
                document_id=document_id,
                version_id=version_id,
                memory_tier="validated",
                status="active",
                title=title,
                body=content,
                provenance={
                    "edition_id": edition_id,
                    "document_id": document_id,
                    "version_id": version_id,
                    "lesson_id": lesson_id,
                    "approved_by": actor_id,
                },
            )
            self.append_event(
                entity_type="memory_item",
                entity_id=memory_id,
                edition_id=edition_id,
                document_id=document_id,
                version_id=version_id,
                event_type="item_promoted_to_validated_memory",
                actor_id=actor_id,
                justification=justification,
                origin="human",
                after={"memory_tier": "validated", "category": category},
                connection=connection,
            )
        return memory_id

    def search_memory(
        self,
        query: str,
        *,
        memory_tier: str = "validated",
        include_rejected: bool = False,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        terms = [term for term in re.findall(r"[\wÀ-ÿ-]+", query.casefold()) if len(term) > 2]
        where = ["memory_tier=?"]
        params: list[Any] = [memory_tier]
        if not include_rejected:
            where.append("status NOT IN ('rejected', 'status.rejected', 'status.do_not_use')")
        for term in terms:
            where.append("(lower(title) LIKE ? OR lower(body) LIKE ?)")
            params.extend((f"%{term}%", f"%{term}%"))
        params.append(limit)
        sql = (
            "SELECT entity_type, entity_id, edition_id, document_id, version_id, "
            "memory_tier, status, title, body, provenance_json "
            "FROM editorial_search WHERE "
            + " AND ".join(where)
            + " ORDER BY updated_at DESC LIMIT ?"
        )
        with self.connection() as connection:
            rows = connection.execute(sql, params).fetchall()
        return [
            {
                **dict(row),
                "provenance": json.loads(row["provenance_json"]),
                "relevance_reason": (
                    f"Correspondência textual/contextual com: {', '.join(terms)}"
                    if terms
                    else "Itens recentes no escopo solicitado"
                ),
            }
            for row in rows
        ]

    def register_generated_output(
        self,
        *,
        edition_id: str,
        actor_id: str,
        agent_name: str,
        model: str | None,
        purpose: str,
        prompt: str,
        context: dict[str, Any],
        configuration: dict[str, Any],
        result: str,
        output_type: str,
        document_title: str,
        discarded: bool = False,
    ) -> dict[str, str]:
        self.authorize(actor_id, "write")
        agent_actor = _stable_id("ACTOR", "agent", agent_name)
        self.ensure_actor(agent_actor, display_name=agent_name, role="agent")
        run_id = _new_id("RUN")
        external_key = f"agent-run:{run_id}:{output_type}"
        document_id = self.create_document(
            external_key=external_key,
            canonical_title=document_title,
            original_name=document_title,
            actor_id=actor_id,
            edition_id=edition_id,
            document_type_id=(
                "type.editorial_draft" if output_type in {"draft", "synthesis", "final_text"}
                else "type.structured_extraction" if output_type == "extraction"
                else "type.audit" if output_type == "audit"
                else "type.supporting_material"
            ),
            editorial_function_id=(
                "function.audit" if output_type == "audit" else "function.draft"
            ),
            stage_id="stage.drafting",
            status_id="status.preliminary",
            editorial_meaning=(
                "Resultado gerado e preservado na memória histórica. "
                "Não foi aprovado como referência normativa."
            ),
            confidence=1.0,
            confirmed=True,
        )
        result_hash = uuid.uuid5(uuid.NAMESPACE_URL, result).hex.ljust(64, "0")[:64]
        version_id = self.create_version(
            document_id=document_id,
            content_hash=result_hash,
            actor_id=actor_id,
            agent_id=agent_actor,
            reason=f"Resultado integral do agente para {purpose}.",
            change_summary="Primeiro resultado persistido deste run.",
            status_id="status.preliminary" if not discarded else "status.archived",
            editorial_meaning=(
                "Resultado descartado preservado apenas para rastreabilidade."
                if discarded
                else "Resultado de agente aguardando avaliação e revisão humana."
            ),
            content_text=result,
            source_kind="agent",
            meaning_confidence=1.0,
            metadata={"prompt": prompt, "context": context, "configuration": configuration},
        )
        with self.connection() as connection:
            connection.execute(
                """
                INSERT INTO agent_runs(
                    agent_run_id, edition_id, actor_id, agent_name, model,
                    purpose, prompt, context_json, configuration_json,
                    started_at, completed_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    edition_id,
                    actor_id,
                    agent_name,
                    model,
                    purpose,
                    prompt,
                    _json(context),
                    _json(configuration),
                    utc_now(),
                    utc_now(),
                    "discarded" if discarded else "completed",
                ),
            )
            output_id = _new_id("OUTPUT")
            connection.execute(
                """
                INSERT INTO generated_outputs(
                    generated_output_id, agent_run_id, edition_id, document_id,
                    version_id, output_type, purpose, result_hash, created_at, discarded
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    output_id,
                    run_id,
                    edition_id,
                    document_id,
                    version_id,
                    output_type,
                    purpose,
                    result_hash,
                    utc_now(),
                    int(discarded),
                ),
            )
        return {
            "agent_run_id": run_id,
            "generated_output_id": output_id,
            "document_id": document_id,
            "version_id": version_id,
        }

    def sync_job(self, job_dir: str | Path, *, actor_id: str) -> dict[str, Any]:
        self.authorize(actor_id, "write")
        root = Path(job_dir).resolve()
        job = load_data(root / "job.yml")
        job_id = str(job["job_id"])
        edition_id = f"EDITION-{job_id}"
        self.upsert_edition(
            edition_id=edition_id,
            canonical_title=str(job["request"]["topic"]),
            status=str(job["state"]),
            editorial_meaning=(
                f"Edição no estado operacional {job['state']}. "
                "Aprovação e publicação continuam dependentes de decisão humana."
            ),
            meaning_confidence=1.0,
            actor_id=actor_id,
            job_id=job_id,
            source_path=str(root),
            confirmed=True,
        )
        source_document_ids: list[str] = []
        created_versions: list[str] = []
        for source in job.get("source_documents", []):
            source_path = Path(source.get("job_copy") or source["location"])
            classification = classify_drive_item(
                {
                    "name": source["original_name"],
                    "path": f"Reviews/jobs/{job_id}/input/{source['original_name']}",
                    "mime_type": "",
                }
            ).to_dict()
            document_id = self.create_document(
                external_key=f"job:{job_id}:source:{source['source_id']}",
                canonical_title=source["original_name"],
                original_name=source["original_name"],
                actor_id=actor_id,
                edition_id=edition_id,
                document_type_id=classification["document_type_id"],
                editorial_function_id="function.main_source",
                stage_id="stage.material_received",
                status_id="status.unverified",
                editorial_meaning=(
                    "Fonte original registrada no job e preservada por hash. "
                    "Sua validação documental segue os gates do pipeline."
                ),
                confidence=1.0,
                confirmed=True,
            )
            source_document_ids.append(document_id)
            version_id = self.create_version(
                document_id=document_id,
                content_hash=source["sha256"],
                actor_id=actor_id,
                reason="Fonte imutável registrada ao criar ou sincronizar o job.",
                change_summary="Versão inicial da fonte recebida.",
                status_id="status.unverified",
                editorial_meaning="Fonte recebida; validação documental ainda pode estar pendente.",
                content_path=str(source_path),
                source_kind="job_source",
                meaning_confidence=1.0,
                metadata={"source_record": source},
            )
            created_versions.append(version_id)
            if source_path.is_file():
                self.preserve_file(
                    source_path,
                    document_id=document_id,
                    version_id=version_id,
                    original_filename=source["original_name"],
                    metadata={"job_id": job_id, "source": True},
                )

        ignored_roots = {".reviews"}
        for path in sorted(root.rglob("*")):
            if not path.is_file() or any(part in ignored_roots for part in path.parts):
                continue
            relative = path.relative_to(root).as_posix()
            if relative.startswith("input/"):
                continue
            if relative == "job.yml":
                document_type = "type.administrative"
                editorial_function = "function.organization"
            else:
                top = relative.split("/", 1)[0]
                document_type = {
                    "normalized": "type.structured_extraction",
                    "extraction": "type.structured_extraction",
                    "analysis": "type.methodological_analysis",
                    "planning": "type.editorial_map",
                    "drafts": "type.editorial_draft",
                    "audits": "type.audit",
                    "feedback": "type.review_comment",
                    "final": "type.publication_version",
                    "visuals": "type.visual_asset",
                }.get(top, "type.supporting_material")
                editorial_function = {
                    "normalized": "function.extraction",
                    "extraction": "function.extraction",
                    "analysis": "function.analysis",
                    "planning": "function.organization",
                    "drafts": "function.draft",
                    "audits": "function.audit",
                    "feedback": "function.learning",
                    "final": "function.final",
                    "visuals": "function.derived",
                }.get(top, "function.organization")
            digest = sha256_file(path)
            content_text, metadata = _read_text_best_effort(path)
            document_id = self.create_document(
                external_key=f"job:{job_id}:artifact:{relative}",
                canonical_title=path.stem,
                original_name=path.name,
                actor_id=actor_id,
                edition_id=edition_id,
                document_type_id=document_type,
                editorial_function_id=editorial_function,
                stage_id=(
                    "stage.awaiting_review"
                    if relative.startswith("final/")
                    else "stage.drafting"
                ),
                status_id=(
                    "status.awaiting_review"
                    if relative.startswith("final/")
                    else "status.preliminary"
                ),
                editorial_meaning=(
                    f"Artefato {relative} produzido no job {job_id}; "
                    "seu significado normativo depende do gate e de aprovação humana."
                ),
                confidence=1.0,
                confirmed=True,
            )
            version_id = self.create_version(
                document_id=document_id,
                content_hash=digest,
                actor_id=actor_id,
                reason=f"Artefato sincronizado a partir do estado {job['state']}.",
                change_summary=f"Conteúdo corrente de {relative}.",
                status_id=(
                    "status.awaiting_review"
                    if relative.startswith("final/")
                    else "status.preliminary"
                ),
                editorial_meaning=(
                    f"Artefato do estado {job['state']}; não é aprovação automática."
                ),
                content_text=content_text,
                content_path=str(path),
                source_kind="job_artifact",
                meaning_confidence=1.0,
                metadata={"job_id": job_id, "relative_path": relative, **metadata},
            )
            created_versions.append(version_id)
            self.preserve_file(
                path,
                document_id=document_id,
                version_id=version_id,
                metadata={"job_id": job_id, "relative_path": relative},
            )
            for source_document_id in source_document_ids:
                self.add_relationship(
                    relationship_type="based_on",
                    actor_id=actor_id,
                    source_document_id=document_id,
                    target_document_id=source_document_id,
                    rationale=f"O artefato {relative} pertence ao job que registrou esta fonte.",
                    confidence=1.0,
                    confirmed=True,
                )
        registry_approval_id: str | None = None
        approval_artifact = root / "final" / "publication-approval.json"
        if job.get("state") == "approved" and approval_artifact.is_file():
            with self.connection() as connection:
                candidate = connection.execute(
                    """
                    SELECT v.version_id FROM documents d
                    JOIN document_versions v ON v.document_id=d.document_id
                    WHERE d.external_key=?
                    ORDER BY v.version_number DESC LIMIT 1
                    """,
                    (f"job:{job_id}:artifact:final/candidate.md",),
                ).fetchone()
                existing_approval = (
                    connection.execute(
                        """
                        SELECT approval_id FROM approvals
                        WHERE version_id=? AND decision='approved'
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        (candidate["version_id"],),
                    ).fetchone()
                    if candidate is not None
                    else None
                )
            if candidate is None:
                raise RuntimeError(
                    "Job aprovado sem versão registrada de final/candidate.md"
                )
            if existing_approval is None:
                registry_approval_id = self.approve_version(
                    candidate["version_id"],
                    actor_id=actor_id,
                    rationale=(
                        "Aprovação importada do gate humano e do artefato "
                        "final/publication-approval.json do job."
                    ),
                    approval_type="job_publication_gate",
                )
            else:
                registry_approval_id = str(existing_approval["approval_id"])
        self.append_event(
            entity_type="edition",
            entity_id=edition_id,
            edition_id=edition_id,
            event_type="job_synced",
            actor_id=actor_id,
            justification=f"Job {job_id} sincronizado no estado {job['state']}.",
            origin="job_pipeline",
            metadata={"versions_seen": len(created_versions)},
        )
        return {
            "edition_id": edition_id,
            "job_id": job_id,
            "source_documents": len(source_document_ids),
            "versions_seen": len(created_versions),
            "approval_id": registry_approval_id,
        }

    def sync_jobs(
        self,
        jobs_root: str | Path,
        *,
        actor_id: str,
    ) -> dict[str, Any]:
        """Migra e reindexa todos os jobs reais encontrados, de forma retomável."""

        root = Path(jobs_root).resolve()
        results: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        for job_file in sorted(root.rglob("job.yml")):
            if job_file.parent.name == "JOB-YYYY-NNN":
                continue
            try:
                results.append(self.sync_job(job_file.parent, actor_id=actor_id))
            except (OSError, ValueError, KeyError, RuntimeError) as exc:
                errors.append({"job_dir": str(job_file.parent), "error": str(exc)})
        return {
            "jobs_root": str(root),
            "jobs_found": len(results) + len(errors),
            "jobs_synced": len(results),
            "errors": errors,
            "results": results,
            "status": "completed" if not errors else "partial",
        }

    def edition_record(self, edition_id: str) -> dict[str, Any]:
        with self.connection() as connection:
            edition = connection.execute(
                "SELECT * FROM editions WHERE edition_id=?", (edition_id,)
            ).fetchone()
            if edition is None:
                raise KeyError(edition_id)
            documents = connection.execute(
                """
                SELECT d.*, COUNT(v.version_id) AS version_count
                FROM documents d
                LEFT JOIN document_versions v ON v.document_id=d.document_id
                WHERE d.edition_id=? AND d.deleted_at IS NULL
                GROUP BY d.document_id
                ORDER BY d.editorial_function_id, d.canonical_title
                """,
                (edition_id,),
            ).fetchall()
            events = connection.execute(
                """
                SELECT * FROM editorial_events WHERE edition_id=?
                ORDER BY occurred_at, event_id
                """,
                (edition_id,),
            ).fetchall()
            relationships = connection.execute(
                """
                SELECT r.* FROM document_relationships r
                LEFT JOIN documents sd ON sd.document_id=r.source_document_id
                LEFT JOIN documents td ON td.document_id=r.target_document_id
                WHERE sd.edition_id=? OR td.edition_id=?
                ORDER BY r.created_at
                """,
                (edition_id, edition_id),
            ).fetchall()
        return {
            "contract_version": "1.0.0",
            "edition": dict(edition),
            "documents": [dict(row) for row in documents],
            "timeline": [dict(row) for row in events],
            "lineage": [dict(row) for row in relationships],
        }

    def dashboard(self) -> dict[str, Any]:
        with self.connection() as connection:
            counts = {
                table: connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
                for table in (
                    "editions",
                    "documents",
                    "document_versions",
                    "document_files",
                    "document_file_sources",
                    "document_relationships",
                    "version_diffs",
                    "editorial_events",
                    "approvals",
                    "publication_records",
                    "editorial_lessons",
                    "memory_items",
                    "memory_item_sources",
                    "drive_import_jobs",
                    "drive_revisions",
                    "drive_comments",
                    "agent_runs",
                    "generated_outputs",
                )
            }
            counts["version_lineage_edges"] = connection.execute(
                """
                SELECT COUNT(*) AS n FROM document_versions
                WHERE previous_version_id IS NOT NULL
                   OR restored_from_version_id IS NOT NULL
                """
            ).fetchone()["n"]
            by_status = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT status_id, COUNT(*) AS count FROM documents
                    WHERE deleted_at IS NULL GROUP BY status_id ORDER BY count DESC
                    """
                )
            ]
            pending = connection.execute(
                "SELECT COUNT(*) AS n FROM classification_suggestions WHERE status='pending'"
            ).fetchone()["n"]
            memory = [
                dict(row)
                for row in connection.execute(
                    """
                    SELECT memory_tier, status, COUNT(*) AS count FROM memory_items
                    WHERE deleted_at IS NULL GROUP BY memory_tier, status
                    """
                )
            ]
        return {
            "counts": counts,
            "documents_by_status": by_status,
            "classification_pending": pending,
            "memory": memory,
        }

    def seed_minimum_example(self, *, actor_id: str = "fixture-editor") -> dict[str, Any]:
        self.ensure_actor(actor_id, display_name="Editor da fixture", role="editor")
        edition_id = "EDITION-TRF-METABOLIC-EXAMPLE"
        self.upsert_edition(
            edition_id=edition_id,
            canonical_title="Restrição de tempo alimentar e síndrome metabólica",
            status="approved",
            editorial_meaning="Fixture de desenvolvimento para validar a trajetória editorial completa.",
            meaning_confidence=1.0,
            actor_id=actor_id,
            confirmed=True,
        )
        source_doc = self.create_document(
            external_key="fixture:trf:source",
            canonical_title="Artigo original",
            original_name="artigo-original.pdf",
            actor_id=actor_id,
            edition_id=edition_id,
            document_type_id="type.primary_source",
            editorial_function_id="function.main_source",
            stage_id="stage.material_received",
            status_id="status.source_verified",
            editorial_meaning="Fonte primária validada para a fixture.",
            confidence=1.0,
            confirmed=True,
        )
        source_version = self.create_version(
            document_id=source_doc,
            content_hash="1" * 64,
            actor_id=actor_id,
            reason="Fonte inicial da fixture.",
            change_summary="Registro inicial.",
            status_id="status.source_verified",
            editorial_meaning="Fonte primária validada para a fixture.",
            content_text="Artigo original da fixture.",
            source_kind="fixture",
            meaning_confidence=1.0,
        )
        extraction_doc = self.create_document(
            external_key="fixture:trf:extraction",
            canonical_title="Extração dos resultados",
            original_name="extracao-resultados.json",
            actor_id=actor_id,
            edition_id=edition_id,
            document_type_id="type.structured_extraction",
            editorial_function_id="function.extraction",
            stage_id="stage.awaiting_audit",
            status_id="status.preliminary",
            editorial_meaning="Extração ainda não conferida com o material suplementar.",
            confidence=1.0,
            confirmed=True,
        )
        extraction_v1 = self.create_version(
            document_id=extraction_doc,
            content_hash="2" * 64,
            actor_id=actor_id,
            reason="Extração inicial aguardando auditoria.",
            change_summary="Valores ainda não conferidos com o suplemento.",
            status_id="status.preliminary",
            editorial_meaning="Extração aguardando auditoria; não usar como dado final.",
            content_text="Completaram o estudo: 105 participantes.",
            source_kind="fixture",
            meaning_confidence=1.0,
        )
        extraction_v2 = self.create_version(
            document_id=extraction_doc,
            content_hash="3" * 64,
            actor_id=actor_id,
            reason="Correção após conferência do material suplementar.",
            change_summary="Corrigido o número de participantes que completaram o estudo.",
            status_id="status.approved",
            editorial_meaning="Extração corrigida e aprovada na fixture.",
            content_text="Completaram o estudo: 97 participantes.",
            source_kind="fixture",
            meaning_confidence=1.0,
        )
        response_doc = self.create_document(
            external_key="fixture:trf:clinical-answer",
            canonical_title="Resposta clínica",
            original_name="resposta-clinica.md",
            actor_id=actor_id,
            edition_id=edition_id,
            document_type_id="type.clinical_answer",
            editorial_function_id="function.draft",
            stage_id="stage.changes_requested",
            status_id="status.changes_requested",
            editorial_meaning="Resposta que recebeu alterações metodológicas.",
            confidence=1.0,
            confirmed=True,
        )
        response_v1 = self.create_version(
            document_id=response_doc,
            content_hash="4" * 64,
            actor_id=actor_id,
            reason="Primeira resposta enviada para revisão.",
            change_summary="Versão inicial.",
            status_id="status.changes_requested",
            editorial_meaning="Atribuição causal inadequada ainda não corrigida.",
            content_text="O horário alimentar causou a melhora metabólica.",
            source_kind="fixture",
            meaning_confidence=1.0,
        )
        response_v2 = self.create_version(
            document_id=response_doc,
            content_hash="5" * 64,
            actor_id=actor_id,
            reason="Correção metodológica solicitada na revisão.",
            change_summary="Incluída a redução calórica espontânea como explicação concorrente.",
            status_id="status.approved",
            editorial_meaning="Resposta revisada e aprovada na fixture.",
            content_text=(
                "A melhora ocorreu durante a alimentação com tempo restrito, mas a redução "
                "espontânea da ingestão energética impede atribuí-la exclusivamente ao horário."
            ),
            source_kind="fixture",
            meaning_confidence=1.0,
        )
        publication_doc = self.create_document(
            external_key="fixture:trf:publication",
            canonical_title="Publicação final",
            original_name="publicacao-final.md",
            actor_id=actor_id,
            edition_id=edition_id,
            document_type_id="type.published_material",
            editorial_function_id="function.published",
            stage_id="stage.published",
            status_id="status.published",
            editorial_meaning="Material publicado derivado da resposta clínica v2.",
            confidence=1.0,
            confirmed=True,
        )
        publication_version = self.create_version(
            document_id=publication_doc,
            content_hash="6" * 64,
            actor_id=actor_id,
            reason="Material final preparado para publicação.",
            change_summary="Derivado integralmente da resposta clínica v2.",
            status_id="status.published",
            editorial_meaning="Publicação final da fixture.",
            content_text=(
                "A melhora ocorreu durante a alimentação com tempo restrito, mas a redução "
                "espontânea da ingestão energética impede atribuí-la exclusivamente ao horário."
            ),
            source_kind="fixture",
            meaning_confidence=1.0,
        )
        for source, target, relation, rationale in (
            (extraction_doc, source_doc, "based_on", "A extração usa o artigo original."),
            (response_doc, extraction_doc, "based_on", "A resposta usa a extração aprovada."),
            (publication_doc, response_doc, "published_from", "A publicação deriva da resposta v2."),
        ):
            self.add_relationship(
                relationship_type=relation,
                actor_id=actor_id,
                source_document_id=source,
                target_document_id=target,
                rationale=rationale,
                confirmed=True,
            )
        approval_id = self.approve_version(
            publication_version,
            actor_id=actor_id,
            rationale="A fixture exige uma publicação ligada à versão exata aprovada.",
        )
        publication_id = self.publish_version(
            publication_version,
            actor_id=actor_id,
            rationale="Publicação controlada da fixture de desenvolvimento.",
            destination="fixture",
        )
        lesson_id = self.propose_lesson(
            title="Não atribuir efeitos exclusivamente ao horário alimentar",
            content=(
                "Em intervenções de alimentação com tempo restrito acompanhadas de redução "
                "espontânea da ingestão energética, não atribuir os efeitos exclusivamente "
                "ao horário alimentar."
            ),
            lesson_type="memory.interpretation_alert",
            scope="intervenções de alimentação com tempo restrito",
            actor_id=actor_id,
            rationale="Diferença entre as versões 1 e 2 da resposta clínica.",
            confidence=0.95,
            source_version_ids=(response_v1, response_v2),
        )
        self.compare_and_record_versions(extraction_v1, extraction_v2, actor_id=actor_id)
        self.compare_and_record_versions(response_v1, response_v2, actor_id=actor_id)
        return {
            "edition_id": edition_id,
            "source_version_id": source_version,
            "extraction_versions": [extraction_v1, extraction_v2],
            "response_versions": [response_v1, response_v2],
            "publication_version_id": publication_version,
            "approval_id": approval_id,
            "publication_id": publication_id,
            "lesson_id": lesson_id,
        }


def registry_path_for_job(job_dir: str | Path) -> Path:
    override = os.environ.get("REVIEWS_REGISTRY_PATH")
    if override:
        return Path(override).resolve()
    root = Path(job_dir).resolve()
    workspace = root.parent.parent if root.parent.name == "jobs" else root.parent
    return workspace / ".reviews" / "editorial-registry.sqlite3"


def sync_job_to_registry(
    job_dir: str | Path,
    *,
    actor_id: str,
    role: str = "contributor",
) -> dict[str, Any]:
    registry = EditorialRegistry(registry_path_for_job(job_dir))
    registry.ensure_actor(actor_id, display_name=actor_id, role=role)
    return registry.sync_job(job_dir, actor_id=actor_id)
