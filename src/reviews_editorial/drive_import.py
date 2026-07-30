"""Importação física, idempotente e retomável de snapshots do Google Drive."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import unicodedata
import urllib.error
import urllib.request
import uuid
from collections import Counter
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from .classification import classify_drive_item
from .io import load_data, sha256_file
from .jobs import utc_now
from .registry import EditorialRegistry, _json, _new_id, _safe_name, _stable_id


GOOGLE_NATIVE_EXPORTS = {
    "application/vnd.google-apps.document": (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".docx",
        "https://docs.google.com/document/d/{id}/export?format=docx",
    ),
    "application/vnd.google-apps.spreadsheet": (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".xlsx",
        "https://docs.google.com/spreadsheets/d/{id}/export?format=xlsx",
    ),
    "application/vnd.google-apps.presentation": (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ".pptx",
        "https://docs.google.com/presentation/d/{id}/export/pptx",
    ),
}

EXCLUDED_FOLDER_IDS = frozenset(
    {
        "1XPBN2r5RXsfKtcuzD7peZXBLV812IN0i",
        "1zt-6Jt46GOyzFJZlKm6oNqlMuV7wKgQt",
    }
)
EXCLUDED_PATHS = (
    "Reviews/Documentos/POPs",
    "Reviews/Documentos/Diretrizes/Estatutos",
)


class DriveImportError(RuntimeError):
    """Erro explícito de inventário ou importação."""


def _key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold()


def _edition_key(value: str) -> str:
    cleaned = re.sub(r"^\s*\d+[_\s-]+", "", value)
    cleaned = re.sub(r"\s+", " ", cleaned.replace("_", " ")).strip()
    return re.sub(r"[^a-z0-9]+", "-", _key(cleaned)).strip("-") or "unclassified"


def _document_group_key(item: dict[str, Any], classification: dict[str, Any]) -> str:
    edition = classification.get("suggested_edition_title")
    grouped_types = {
        "type.editorial_draft",
        "type.editorial_review",
        "type.clinical_answer",
        "type.publication_version",
        "type.published_material",
    }
    if edition and classification["document_type_id"] in grouped_types:
        return f"drive-edition:{_edition_key(str(edition))}:editorial-text"
    return f"drive:{item['id']}"


def _item_order(item: dict[str, Any]) -> tuple[str, int, str, str]:
    signal = _key(str(item.get("name") or ""))
    if "versao antiga" in signal:
        stage = 0
    elif "publicacao final" in signal or "[publicad" in signal:
        stage = 5
    elif "final revisada" in signal or "final humana" in signal:
        stage = 4
    elif re.search(r"(^|\s)final\s*[—-]", signal):
        stage = 3
    elif "auditoria" in signal:
        stage = 2
    else:
        stage = 1
    return (
        _edition_key(str(classify_drive_item(item).suggested_edition_title or item.get("path") or "")),
        stage,
        str(item.get("modified_time") or ""),
        str(item.get("path") or ""),
    )


def validate_snapshot(snapshot: dict[str, Any]) -> None:
    if not isinstance(snapshot.get("items"), list):
        raise DriveImportError("Snapshot sem items")
    policy = snapshot.get("exclusion_policy") or {}
    observed_ids = set(policy.get("excluded_folder_ids") or [])
    if observed_ids != EXCLUDED_FOLDER_IDS:
        raise DriveImportError(
            "O snapshot não declara exatamente as duas árvores obrigatoriamente excluídas"
        )
    for item in snapshot["items"]:
        path = str(item.get("path") or "")
        if item.get("id") in EXCLUDED_FOLDER_IDS:
            raise DriveImportError(f"Raiz proibida presente em items: {item.get('id')}")
        if any(path == root or path.startswith(root + "/") for root in EXCLUDED_PATHS):
            raise DriveImportError(f"Descendente proibido presente em items: {path}")


class DriveDownloader:
    """Transporte padrão sem dependências; usa OAuth opcional ou acesso compartilhado."""

    def __init__(self, *, access_token: str | None = None, retries: int = 3) -> None:
        self.access_token = access_token or os.environ.get("REVIEWS_DRIVE_ACCESS_TOKEN")
        self.retries = max(1, retries)

    def download_spec(self, item: dict[str, Any]) -> tuple[str, str, str]:
        item_id = str(item["id"])
        mime = str(item.get("mime_type") or "")
        if mime in GOOGLE_NATIVE_EXPORTS:
            export_mime, extension, template = GOOGLE_NATIVE_EXPORTS[mime]
            return template.format(id=item_id), export_mime, extension
        return (
            f"https://drive.usercontent.google.com/download?id={item_id}&export=download&confirm=t",
            mime or "application/octet-stream",
            PurePosixPath(str(item.get("name") or "")).suffix,
        )

    def download(self, item: dict[str, Any], destination: Path) -> dict[str, Any]:
        url, stored_mime, extension = self.download_spec(item)
        if destination.exists() and destination.stat().st_size > 0:
            return {
                "path": str(destination),
                "mime_type": stored_mime,
                "extension": extension,
                "resumed": True,
                "bytes": destination.stat().st_size,
            }
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".part")
        curl = shutil.which("curl.exe") or shutil.which("curl")
        if curl:
            return self._download_with_curl(
                item,
                url=url,
                stored_mime=stored_mime,
                extension=extension,
                destination=destination,
                temporary=temporary,
                curl=curl,
            )
        last_error: Exception | None = None
        for attempt in range(1, self.retries + 1):
            headers = {"User-Agent": "ReviewsEditorialSystem/0.4"}
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            request = urllib.request.Request(url, headers=headers)
            try:
                with urllib.request.urlopen(request, timeout=120) as response:
                    with temporary.open("wb") as handle:
                        shutil.copyfileobj(response, handle, length=1024 * 1024)
                if temporary.stat().st_size <= 0:
                    raise DriveImportError("Download retornou arquivo vazio")
                os.replace(temporary, destination)
                return {
                    "path": str(destination),
                    "mime_type": stored_mime,
                    "extension": extension,
                    "resumed": False,
                    "bytes": destination.stat().st_size,
                    "attempt": attempt,
                }
            except (OSError, urllib.error.URLError, DriveImportError) as exc:
                last_error = exc
                if temporary.exists():
                    temporary.unlink()
                if attempt < self.retries:
                    time.sleep(min(2**attempt, 8))
        raise DriveImportError(f"Falha ao baixar {item['id']}: {last_error}")

    def _download_with_curl(
        self,
        item: dict[str, Any],
        *,
        url: str,
        stored_mime: str,
        extension: str,
        destination: Path,
        temporary: Path,
        curl: str,
    ) -> dict[str, Any]:
        last_error = ""
        for attempt in range(1, self.retries + 1):
            command = [
                curl,
                "-L",
                "--fail",
                "--silent",
                "--show-error",
                "--connect-timeout",
                "30",
                "--max-time",
                "300",
                "--user-agent",
                "ReviewsEditorialSystem/0.4",
            ]
            if self.access_token:
                command.extend(["--header", f"Authorization: Bearer {self.access_token}"])
            command.extend(["--output", str(temporary), url])
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=False,
            )
            if completed.returncode == 0 and temporary.is_file() and temporary.stat().st_size > 0:
                os.replace(temporary, destination)
                return {
                    "path": str(destination),
                    "mime_type": stored_mime,
                    "extension": extension,
                    "resumed": False,
                    "bytes": destination.stat().st_size,
                    "attempt": attempt,
                    "transport": "curl",
                }
            last_error = completed.stderr.strip() or f"curl exit {completed.returncode}"
            if temporary.exists():
                temporary.unlink()
            if attempt < self.retries:
                time.sleep(min(2**attempt, 8))
        raise DriveImportError(f"Falha ao baixar {item['id']}: {last_error}")


class DriveImporter:
    def __init__(
        self,
        registry: EditorialRegistry,
        *,
        actor_id: str,
        downloader: DriveDownloader | None = None,
    ) -> None:
        self.registry = registry
        self.actor_id = actor_id
        self.downloader = downloader or DriveDownloader()
        self.registry.authorize(actor_id, "write")

    def _upsert_external_source(
        self,
        item: dict[str, Any],
        *,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        external_source_id = _stable_id("EXT", "google-drive", item["id"])
        with self.registry.connection() as connection:
            connection.execute(
                """
                INSERT INTO external_sources(
                    external_source_id, provider, external_id, original_url,
                    original_name, mime_type, full_path, parent_ids_json,
                    created_time, modified_time, owner_json, permissions_json,
                    drive_revision_id, imported_at, metadata_json
                ) VALUES (?, 'google-drive', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, external_id) DO UPDATE SET
                    original_url=excluded.original_url,
                    original_name=excluded.original_name,
                    mime_type=excluded.mime_type,
                    full_path=excluded.full_path,
                    parent_ids_json=excluded.parent_ids_json,
                    created_time=COALESCE(excluded.created_time, external_sources.created_time),
                    modified_time=COALESCE(excluded.modified_time, external_sources.modified_time),
                    owner_json=COALESCE(excluded.owner_json, external_sources.owner_json),
                    permissions_json=COALESCE(excluded.permissions_json, external_sources.permissions_json),
                    imported_at=excluded.imported_at,
                    metadata_json=excluded.metadata_json
                """,
                (
                    external_source_id,
                    item["id"],
                    item.get("web_url"),
                    item.get("name") or "",
                    item.get("mime_type"),
                    item.get("path"),
                    _json([item.get("parent_id")] if item.get("parent_id") else []),
                    item.get("created_time"),
                    item.get("modified_time"),
                    _json(item.get("owner")) if item.get("owner") is not None else None,
                    _json(item.get("permissions")) if item.get("permissions") is not None else None,
                    item.get("drive_revision_id"),
                    utc_now(),
                    _json({**item, **(metadata or {})}),
                ),
            )
        return external_source_id

    def _edition_for(
        self, classification: dict[str, Any]
    ) -> str | None:
        title = classification.get("suggested_edition_title")
        if not title:
            return None
        edition_id = _stable_id("EDITION", "drive", _edition_key(str(title)))
        self.registry.upsert_edition(
            edition_id=edition_id,
            canonical_title=str(title),
            status="awaiting_classification",
            editorial_meaning=(
                "Edição sugerida a partir do contexto de pasta. O vínculo documental "
                "e o título canônico aguardam confirmação humana."
            ),
            meaning_confidence=float(classification["confidence"]),
            actor_id=self.actor_id,
            source_path=None,
            confirmed=False,
        )
        return edition_id

    def _record_import_item(
        self,
        *,
        import_job_id: str,
        item: dict[str, Any],
        result: str,
        external_source_id: str | None,
        document_id: str | None = None,
        version_id: str | None = None,
        content_hash: str | None = None,
        error: str | None = None,
        classification_status: str | None = None,
    ) -> None:
        import_item_id = _stable_id("IMPORTITEM", import_job_id, item["id"])
        with self.registry.connection() as connection:
            connection.execute(
                """
                INSERT INTO drive_import_items(
                    import_item_id, import_job_id, external_source_id, external_id,
                    full_path, item_kind, result, error, content_hash,
                    document_id, version_id, classification_status, processed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(import_job_id, external_id) DO UPDATE SET
                    result=excluded.result,
                    error=excluded.error,
                    content_hash=excluded.content_hash,
                    document_id=excluded.document_id,
                    version_id=excluded.version_id,
                    classification_status=excluded.classification_status,
                    processed_at=excluded.processed_at
                """,
                (
                    import_item_id,
                    import_job_id,
                    external_source_id,
                    item["id"],
                    item.get("path") or "",
                    item.get("item_kind") or "file",
                    result,
                    error,
                    content_hash,
                    document_id,
                    version_id,
                    classification_status,
                    utc_now(),
                ),
            )

    def _ingest_sidecars(
        self, external_source_id: str, item: dict[str, Any]
    ) -> tuple[int, int]:
        revisions = item.get("revisions") or []
        comments = item.get("comments") or []
        with self.registry.connection() as connection:
            for revision in revisions:
                provider_id = str(revision["id"])
                connection.execute(
                    """
                    INSERT INTO drive_revisions(
                        drive_revision_id, external_source_id, provider_revision_id,
                        modified_time, author_json, content_path, content_hash,
                        limitation, metadata_json, imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(external_source_id, provider_revision_id) DO NOTHING
                    """,
                    (
                        _stable_id("DRVREV", external_source_id, provider_id),
                        external_source_id,
                        provider_id,
                        revision.get("modified_time"),
                        _json(revision.get("author") or {}),
                        revision.get("content_path"),
                        revision.get("content_hash"),
                        revision.get("limitation"),
                        _json(revision),
                        utc_now(),
                    ),
                )
            for comment in comments:
                provider_id = str(comment["id"])
                connection.execute(
                    """
                    INSERT INTO drive_comments(
                        drive_comment_id, external_source_id, provider_comment_id,
                        author_json, content, quoted_text, resolved, created_time,
                        modified_time, replies_json, metadata_json, imported_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(external_source_id, provider_comment_id) DO NOTHING
                    """,
                    (
                        _stable_id("DRVCOMMENT", external_source_id, provider_id),
                        external_source_id,
                        provider_id,
                        _json(comment.get("author") or {}),
                        comment.get("content"),
                        comment.get("quoted_text"),
                        int(bool(comment.get("resolved"))),
                        comment.get("created_time"),
                        comment.get("modified_time"),
                        _json(comment.get("replies") or []),
                        _json(comment),
                        utc_now(),
                    ),
                )
        return len(revisions), len(comments)

    def import_history_snapshots(
        self,
        history_path: str | Path,
    ) -> dict[str, Any]:
        """Ingere metadados privados de revisões e comentários de modo idempotente."""

        root = Path(history_path).resolve()
        files = (
            sorted(root.glob("*.json"))
            if root.is_dir()
            else [root]
        )
        if not files or any(not path.is_file() for path in files):
            raise DriveImportError(f"Snapshot de histórico não encontrado: {root}")
        with self.registry.connection() as connection:
            before_revisions = connection.execute(
                "SELECT COUNT(*) AS n FROM drive_revisions"
            ).fetchone()["n"]
            before_comments = connection.execute(
                "SELECT COUNT(*) AS n FROM drive_comments"
            ).fetchone()["n"]
        counters: Counter[str] = Counter()
        errors: list[dict[str, str]] = []
        fragments: list[dict[str, str]] = []
        for path in files:
            fragment = load_data(path)
            if fragment.get("history_snapshot_version") != "1.0.0":
                raise DriveImportError(
                    f"Versão de snapshot de histórico incompatível: {path}"
                )
            fragments.append({"path": str(path), "sha256": sha256_file(path)})
            for item in fragment.get("items") or []:
                counters["items_seen"] += 1
                external_id = str(item.get("id") or "")
                with self.registry.connection() as connection:
                    source = connection.execute(
                        """
                        SELECT external_source_id
                        FROM external_sources
                        WHERE provider='google-drive' AND external_id=?
                        """,
                        (external_id,),
                    ).fetchone()
                if source is None:
                    errors.append(
                        {
                            "drive_id": external_id,
                            "error": "fonte não registrada no inventário permitido",
                        }
                    )
                    continue
                revisions, comments = self._ingest_sidecars(
                    source["external_source_id"],
                    item,
                )
                counters["revisions_seen"] += revisions
                counters["comments_seen"] += comments
                if revisions or comments:
                    counters["items_with_history"] += 1
        with self.registry.connection() as connection:
            after_revisions = connection.execute(
                "SELECT COUNT(*) AS n FROM drive_revisions"
            ).fetchone()["n"]
            after_comments = connection.execute(
                "SELECT COUNT(*) AS n FROM drive_comments"
            ).fetchone()["n"]
        return {
            "history_import_version": "1.0.0",
            "status": "completed" if not errors else "partial",
            "history_path": str(root),
            "fragments": fragments,
            "totals": {
                **counters,
                "revisions_inserted": after_revisions - before_revisions,
                "comments_inserted": after_comments - before_comments,
                "revisions_registered": after_revisions,
                "comments_registered": after_comments,
            },
            "errors": errors,
            "idempotent": (
                counters["revisions_seen"] >= after_revisions - before_revisions
                and counters["comments_seen"] >= after_comments - before_comments
            ),
        }

    def import_snapshot(
        self,
        snapshot_path: str | Path,
        *,
        download_files: bool = True,
        approved_drive_ids: Iterable[str] = (),
        resume_failed_from: str | None = None,
        max_items: int | None = None,
    ) -> dict[str, Any]:
        snapshot_file = Path(snapshot_path).resolve()
        snapshot = load_data(snapshot_file)
        validate_snapshot(snapshot)
        snapshot_hash = sha256_file(snapshot_file)
        import_job_id = _new_id("IMPORT")
        root = snapshot["source_root"]
        started_at = utc_now()
        with self.registry.connection() as connection:
            connection.execute(
                """
                UPDATE drive_import_jobs SET
                    status='interrupted',
                    completed_at=?,
                    errors_json=?
                WHERE snapshot_path=? AND status='running'
                """,
                (
                    started_at,
                    _json(
                        [
                            {
                                "error": (
                                    "Execução anterior interrompida antes da emissão "
                                    "do manifesto; reexecução idempotente permitida."
                                )
                            }
                        ]
                    ),
                    str(snapshot_file),
                ),
            )
            connection.execute(
                """
                INSERT INTO drive_import_jobs(
                    import_job_id, source_root_id, source_root_url, snapshot_path,
                    status, started_at, actor_id, resume_of_job_id
                ) VALUES (?, ?, ?, ?, 'running', ?, ?, ?)
                """,
                (
                    import_job_id,
                    root["id"],
                    root["url"],
                    str(snapshot_file),
                    started_at,
                    self.actor_id,
                    resume_failed_from,
                ),
            )
        allowed_failed_ids: set[str] | None = None
        if resume_failed_from:
            with self.registry.connection() as connection:
                allowed_failed_ids = {
                    row["external_id"]
                    for row in connection.execute(
                        """
                        SELECT external_id FROM drive_import_items
                        WHERE import_job_id=? AND result='error'
                        """,
                        (resume_failed_from,),
                    )
                }
        approved_ids = set(approved_drive_ids)
        counters: Counter[str] = Counter()
        by_format: Counter[str] = Counter()
        by_folder: Counter[str] = Counter()
        by_classification: Counter[str] = Counter()
        errors: list[dict[str, str]] = []
        pending: list[dict[str, Any]] = []
        duplicate_links = 0
        revisions_total = 0
        comments_total = 0
        items = sorted(snapshot["items"], key=_item_order)
        if max_items is not None:
            with self.registry.connection() as connection:
                completed_ids = {
                    row["external_id"]
                    for row in connection.execute(
                        """
                        SELECT DISTINCT es.external_id
                        FROM external_sources es
                        JOIN document_files df
                          ON df.external_source_id=es.external_source_id
                        WHERE es.provider='google-drive'
                        UNION
                        SELECT DISTINCT es.external_id
                        FROM external_sources es
                        JOIN document_file_sources dfs
                          ON dfs.external_source_id=es.external_source_id
                        WHERE es.provider='google-drive'
                        UNION
                        SELECT DISTINCT external_id
                        FROM drive_import_items
                        WHERE result='folder_registered'
                        """
                    )
                }
            items = [item for item in items if item["id"] not in completed_ids][:max_items]
        staging = (
            self.registry.storage_root.parent
            / "imports"
            / import_job_id
            / "downloads"
        )
        for item in items:
            if allowed_failed_ids is not None and item["id"] not in allowed_failed_ids:
                counters["skipped_not_failed"] += 1
                continue
            counters["items_seen"] += 1
            try:
                external_source_id = self._upsert_external_source(item)
                if item.get("item_kind") == "folder":
                    self._record_import_item(
                        import_job_id=import_job_id,
                        item=item,
                        result="folder_registered",
                        external_source_id=external_source_id,
                    )
                    counters["folders_registered"] += 1
                    continue
                classification = classify_drive_item(item).to_dict()
                edition_id = self._edition_for(classification)
                document_key = _document_group_key(item, classification)
                document_id = self.registry.create_document(
                    external_key=document_key,
                    canonical_title=(
                        str(classification.get("suggested_edition_title"))
                        if document_key.endswith(":editorial-text")
                        else str(item.get("name") or item["id"])
                    ),
                    original_name=str(item.get("name") or item["id"]),
                    actor_id=self.actor_id,
                    edition_id=edition_id,
                    document_type_id=classification["document_type_id"],
                    editorial_function_id=classification["editorial_function_id"],
                    stage_id=classification["stage_id"],
                    status_id=classification["status_id"],
                    editorial_meaning=classification["editorial_meaning"],
                    confidence=float(classification["confidence"]),
                    confirmed=False,
                    notes=f"Importado de {item.get('path')}",
                )
                self.registry.create_classification_suggestion(
                    document_id=document_id,
                    external_source_id=external_source_id,
                    classification=classification,
                    actor_id=self.actor_id,
                )
                by_classification[classification["document_type_id"]] += 1
                if classification["confidence"] < 0.85:
                    pending.append(
                        {
                            "drive_id": item["id"],
                            "path": item.get("path"),
                            "document_id": document_id,
                            "confidence": classification["confidence"],
                            "rationale": classification["rationale"],
                        }
                    )
                with self.registry.connection() as connection:
                    existing_file = connection.execute(
                        """
                        SELECT df.storage_path, df.content_hash, df.mime_type,
                               df.version_id
                        FROM document_files df
                        LEFT JOIN document_file_sources dfs
                          ON dfs.document_file_id=df.document_file_id
                        WHERE df.external_source_id=? OR dfs.external_source_id=?
                        ORDER BY df.imported_at DESC LIMIT 1
                        """,
                        (external_source_id, external_source_id),
                    ).fetchone()
                if existing_file is not None:
                    preserved_path = Path(existing_file["storage_path"])
                    if (
                        preserved_path.is_file()
                        and sha256_file(preserved_path) == existing_file["content_hash"]
                    ):
                        self._record_import_item(
                            import_job_id=import_job_id,
                            item=item,
                            result="already_imported",
                            external_source_id=external_source_id,
                            document_id=document_id,
                            version_id=existing_file["version_id"],
                            content_hash=existing_file["content_hash"],
                            classification_status="pending",
                        )
                        counters["files_imported"] += 1
                        counters["already_imported"] += 1
                        by_format[existing_file["mime_type"] or item.get("mime_type") or ""] += 1
                        by_folder[
                            str(PurePosixPath(str(item.get("path") or "")).parent)
                        ] += 1
                        revisions, comments = self._ingest_sidecars(external_source_id, item)
                        revisions_total += revisions
                        comments_total += comments
                        continue
                if not download_files:
                    self._record_import_item(
                        import_job_id=import_job_id,
                        item=item,
                        result="metadata_only",
                        external_source_id=external_source_id,
                        document_id=document_id,
                        classification_status="pending",
                    )
                    counters["metadata_only"] += 1
                    continue
                url, stored_mime, extension = self.downloader.download_spec(item)
                del url
                original_name = str(item.get("name") or item["id"])
                filename = _safe_name(
                    original_name
                    if PurePosixPath(original_name).suffix or not extension
                    else original_name + extension
                )
                destination = staging / str(item["id"]) / f"content{extension}"
                transfer = self.downloader.download(item, destination)
                digest = sha256_file(destination)
                version_id = self.registry.create_version(
                    document_id=document_id,
                    content_hash=digest,
                    actor_id=self.actor_id,
                    reason=(
                        "Arquivo importado fisicamente do Google Drive e preservado "
                        "como estado imutável."
                    ),
                    change_summary=(
                        f"Importação de {item.get('path')} em "
                        f"{item.get('modified_time') or 'data não disponível'}."
                    ),
                    status_id=classification["status_id"],
                    editorial_meaning=classification["editorial_meaning"],
                    content_path=str(destination),
                    source_kind="google_drive_import",
                    meaning_confidence=float(classification["confidence"]),
                    metadata={
                        "drive_id": item["id"],
                        "drive_url": item.get("web_url"),
                        "drive_path": item.get("path"),
                        "original_mime_type": item.get("mime_type"),
                        "stored_mime_type": stored_mime,
                        "snapshot_hash": snapshot_hash,
                        "transfer": transfer,
                    },
                )
                self.registry.preserve_file(
                    destination,
                    document_id=document_id,
                    version_id=version_id,
                    external_source_id=external_source_id,
                    original_filename=filename,
                    mime_type=stored_mime,
                    metadata={
                        "drive_id": item["id"],
                        "drive_path": item.get("path"),
                        "original_name": original_name,
                        "original_mime_type": item.get("mime_type"),
                        "native_export": item.get("mime_type") in GOOGLE_NATIVE_EXPORTS,
                    },
                )
                with self.registry.connection() as connection:
                    duplicates = connection.execute(
                        """
                        SELECT DISTINCT document_id FROM document_files
                        WHERE content_hash=? AND document_id<>?
                        """,
                        (digest, document_id),
                    ).fetchall()
                for duplicate in duplicates:
                    self.registry.add_relationship(
                        relationship_type="possible_duplicate_of",
                        actor_id=self.actor_id,
                        source_document_id=document_id,
                        target_document_id=duplicate["document_id"],
                        rationale=(
                            "Hash binário idêntico; os registros e contextos de pasta "
                            "foram preservados separadamente."
                        ),
                        confidence=1.0,
                        confirmed=False,
                    )
                    duplicate_links += 1
                revisions, comments = self._ingest_sidecars(external_source_id, item)
                revisions_total += revisions
                comments_total += comments
                self._record_import_item(
                    import_job_id=import_job_id,
                    item=item,
                    result="imported",
                    external_source_id=external_source_id,
                    document_id=document_id,
                    version_id=version_id,
                    content_hash=digest,
                    classification_status="pending",
                )
                self.registry.append_event(
                    entity_type="document",
                    entity_id=document_id,
                    edition_id=edition_id,
                    document_id=document_id,
                    version_id=version_id,
                    event_type="document_imported",
                    actor_id=self.actor_id,
                    justification="Cópia local durável importada do snapshot autorizado.",
                    origin="google_drive",
                    metadata={
                        "drive_id": item["id"],
                        "path": item.get("path"),
                        "hash": digest,
                    },
                )
                if item["id"] in approved_ids:
                    approval_id = self.registry.approve_version(
                        version_id,
                        actor_id=self.actor_id,
                        rationale=(
                            "O manifesto curado existente identifica este item como "
                            "exemplar aprovado; a origem foi preservada."
                        ),
                        approval_type="legacy_curated_corpus",
                    )
                    self.registry.promote_memory(
                        actor_id=self.actor_id,
                        title=f"Exemplar aprovado — {original_name}",
                        content=classification["editorial_meaning"],
                        category="memory.good_example",
                        scope="exemplo editorial do corpus Reviews",
                        confidence=1.0,
                        justification=(
                            f"Promoção baseada no corpus/manifest.yml já curado; "
                            f"approval_id={approval_id}."
                        ),
                        edition_id=edition_id,
                        document_id=document_id,
                        version_id=version_id,
                    )
                    counters["validated_memory_promotions"] += 1
                counters["files_imported"] += 1
                by_format[stored_mime] += 1
                by_folder[str(PurePosixPath(str(item.get("path") or "")).parent)] += 1
            except Exception as exc:  # item boundary: record and continue
                error = {"drive_id": str(item.get("id")), "path": str(item.get("path")), "error": str(exc)}
                errors.append(error)
                counters["errors"] += 1
                try:
                    self._record_import_item(
                        import_job_id=import_job_id,
                        item=item,
                        result="error",
                        external_source_id=None,
                        error=str(exc),
                    )
                except Exception:
                    pass
        totals = {
            "folders_found": snapshot["totals"]["folders_found"],
            "files_found": snapshot["totals"]["files_found"],
            "folders_included": snapshot["totals"]["folders_included"],
            "files_included": snapshot["totals"]["files_included"],
            "folders_excluded": snapshot["totals"]["folders_excluded"],
            "files_excluded": snapshot["totals"]["files_excluded"],
            **dict(counters),
            "revisions_recovered": revisions_total,
            "comments_recovered": comments_total,
            "duplicate_relationships": duplicate_links,
        }
        status = "completed" if not errors and counters["files_imported"] == snapshot["totals"]["files_included"] else "partial"
        if not download_files:
            status = "metadata_only"
        manifest = {
            "manifest_version": "1.0.0",
            "import_job_id": import_job_id,
            "source_root": root,
            "snapshot_path": str(snapshot_file),
            "snapshot_sha256": snapshot_hash,
            "started_at": started_at,
            "completed_at": utc_now(),
            "status": status,
            "totals": totals,
            "totals_by_format": dict(sorted(by_format.items())),
            "totals_by_folder": dict(sorted(by_folder.items())),
            "totals_by_classification": dict(sorted(by_classification.items())),
            "classification_pending": pending,
            "exclusions": snapshot.get("exclusions") or [],
            "errors": errors,
            "limitations": [
                (
                    "Revisões e comentários só são contabilizados quando presentes no "
                    "snapshot enriquecido pelo conector."
                ),
                (
                    "Classificações automáticas permanecem sugestões até confirmação "
                    "humana, mesmo quando o nome ou a pasta indicam publicação."
                ),
            ],
            "private_storage_root": str(self.registry.storage_root),
            "git_storage_policy": ".reviews/ permanece fora do Git",
        }
        report_dir = self.registry.storage_root.parent / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        report_path = report_dir / f"{import_job_id}.json"
        report_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        with self.registry.connection() as connection:
            connection.execute(
                """
                UPDATE drive_import_jobs SET
                    status=?, completed_at=?, totals_json=?, errors_json=?
                WHERE import_job_id=?
                """,
                (
                    status,
                    manifest["completed_at"],
                    _json(totals),
                    _json(errors),
                    import_job_id,
                ),
            )
        self.registry.append_event(
            entity_type="drive_import_job",
            entity_id=import_job_id,
            event_type="drive_import_completed",
            actor_id=self.actor_id,
            justification=(
                "Importação física concluída."
                if status == "completed"
                else "Importação encerrada com itens pendentes ou erros registrados."
            ),
            origin="google_drive",
            metadata={"status": status, "report_path": str(report_path), "totals": totals},
        )
        return {**manifest, "report_path": str(report_path)}


def approved_drive_ids_from_corpus_manifest(path: str | Path) -> set[str]:
    payload = load_data(path)
    result: set[str] = set()
    for key in ("canonical_items", "exemplar_items"):
        for value in payload.get(key) or []:
            if isinstance(value, str) and value.startswith("drive:"):
                result.add(value.removeprefix("drive:"))
    return result
