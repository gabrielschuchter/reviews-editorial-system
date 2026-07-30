"""Contrato JSON estável e versionado para clientes locais do Reviews."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable

from .constants import SYSTEM_VERSION
from .io import load_data
from .jobs import utc_now
from .registry import EditorialRegistry
from .registry_validation import validate_registry


BRIDGE_SCHEMA_VERSION = "1.0.0"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = REPOSITORY_ROOT / ".reviews" / "editorial-registry.sqlite3"

JSON_COLUMNS = {
    "after_json",
    "alternatives_json",
    "author_json",
    "before_json",
    "configuration_json",
    "context_json",
    "errors_json",
    "evaluation_json",
    "evidence_json",
    "metadata_json",
    "numeric_changes_json",
    "owner_json",
    "parent_ids_json",
    "permissions_json",
    "provenance_json",
    "replies_json",
    "semantic_diff_json",
    "totals_json",
}


class UiBridgeError(RuntimeError):
    """Erro público, sanitizado e classificável do contrato da interface."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        action: str,
        category: str,
        retryable: bool = False,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.action = action
        self.category = category
        self.retryable = retryable
        self.details = details or {}

    def as_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "recommended_action": self.action,
            "category": self.category,
            "retryable": self.retryable,
            "details": self.details,
        }


def envelope(
    command: str,
    *,
    data: Any = None,
    warnings: Iterable[dict[str, Any]] = (),
    errors: Iterable[dict[str, Any]] = (),
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    error_list = list(errors)
    return {
        "schema_version": BRIDGE_SCHEMA_VERSION,
        "ok": not error_list,
        "command": command,
        "generated_at": utc_now(),
        "data": data,
        "warnings": list(warnings),
        "errors": error_list,
        "meta": meta or {},
    }


def _decode_json_columns(row: dict[str, Any]) -> dict[str, Any]:
    decoded = dict(row)
    for key in JSON_COLUMNS.intersection(decoded):
        value = decoded[key]
        if not isinstance(value, str):
            continue
        try:
            decoded[key.removesuffix("_json")] = json.loads(value)
        except json.JSONDecodeError:
            decoded[key.removesuffix("_json")] = None
    return decoded


def _git(*args: str) -> tuple[int, str]:
    try:
        completed = subprocess.run(
            ["git", "-c", f"safe.directory={REPOSITORY_ROOT.as_posix()}", *args],
            cwd=REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return 1, ""
    return completed.returncode, completed.stdout.strip()


def _run_core_script(script_name: str, arguments: list[str]) -> dict[str, Any]:
    script = (REPOSITORY_ROOT / "scripts" / script_name).resolve()
    scripts_root = (REPOSITORY_ROOT / "scripts").resolve()
    if script.parent != scripts_root or not script.is_file():
        raise UiBridgeError(
            "SCRIPT_NOT_ALLOWED",
            "O comando solicitado não pertence à allowlist do núcleo.",
            action="Use apenas uma ação editorial exposta pela ponte.",
            category="usage_error",
        )
    completed = subprocess.run(
        [sys.executable, str(script), *arguments],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    stdout = completed.stdout.strip()
    try:
        payload = json.loads(stdout) if stdout else {}
    except json.JSONDecodeError as exc:
        raise UiBridgeError(
            "INVALID_CORE_OUTPUT",
            f"{script_name} não retornou JSON válido.",
            action="Execute o comando diretamente para inspecionar a falha.",
            category="internal_failure",
            details={"exit_code": completed.returncode},
        ) from exc
    if completed.returncode != 0:
        raise UiBridgeError(
            "CORE_COMMAND_FAILED",
            f"{script_name} terminou com erro.",
            action="Revise os gates e os detalhes apresentados pelo núcleo.",
            category="editorial_block" if completed.returncode == 2 else "environment_failure",
            retryable=True,
            details={
                "exit_code": completed.returncode,
                "stderr": completed.stderr.strip()[-2000:],
                "result": payload,
            },
        )
    return payload


class ReviewsUiBridge:
    """Consultas públicas e composição de comandos do núcleo para o desktop."""

    def __init__(
        self,
        *,
        database_path: str | Path = DEFAULT_DB,
        storage_root: str | Path | None = None,
    ) -> None:
        self.registry = EditorialRegistry(database_path, storage_root=storage_root)

    def workspace_info(self) -> dict[str, Any]:
        head_code, head = _git("rev-parse", "HEAD")
        branch_code, branch = _git("branch", "--show-current")
        status_code, status = _git("status", "--porcelain")
        return {
            "repository_root": str(REPOSITORY_ROOT),
            "system_version": SYSTEM_VERSION,
            "bridge_schema_version": BRIDGE_SCHEMA_VERSION,
            "commit": head if head_code == 0 else None,
            "branch": branch if branch_code == 0 else None,
            "working_tree": {
                "clean": status_code == 0 and not status,
                "changed_paths": status.splitlines() if status else [],
            },
            "database": str(self.registry.database_path),
            "storage_root": str(self.registry.storage_root),
            "jobs_root": str(REPOSITORY_ROOT / "jobs"),
            "roles_are_editorial_gates": True,
            "roles_are_authentication": False,
        }

    def doctor(self) -> dict[str, Any]:
        info = self.workspace_info()
        codex_path = shutil.which("codex")
        migration_rows: list[str] = []
        with self.registry.connection() as connection:
            migration_rows = [
                str(row["version"])
                for row in connection.execute(
                    "SELECT version FROM schema_migrations ORDER BY version"
                )
            ]
            job_count = connection.execute(
                "SELECT COUNT(*) AS n FROM editions WHERE job_id IS NOT NULL"
            ).fetchone()["n"]
        checks = [
            self._doctor_check("repository", REPOSITORY_ROOT.is_dir(), str(REPOSITORY_ROOT)),
            self._doctor_check("agents", (REPOSITORY_ROOT / "AGENTS.md").is_file()),
            self._doctor_check("version", bool(SYSTEM_VERSION), SYSTEM_VERSION),
            self._doctor_check("git", bool(info["commit"]), info["commit"]),
            self._doctor_check(
                "working_tree",
                info["working_tree"]["clean"],
                "limpo" if info["working_tree"]["clean"] else "alterações locais presentes",
                severity="warning",
            ),
            self._doctor_check("python", sys.version_info >= (3, 11), sys.version.split()[0]),
            self._doctor_check("codex_cli", bool(codex_path), codex_path),
            self._doctor_check(
                "skills",
                len(list((REPOSITORY_ROOT / ".codex" / "skills").glob("reviews-*"))) == 11,
                "11 skills esperadas",
            ),
            self._doctor_check(
                "schemas",
                len(list((REPOSITORY_ROOT / "schemas").glob("*.schema.json"))) >= 28,
                "schemas versionados disponíveis",
            ),
            self._doctor_check("migrations", len(migration_rows) >= 2, migration_rows),
            self._doctor_check("registry", self.registry.database_path.is_file()),
            self._doctor_check("jobs", (REPOSITORY_ROOT / "jobs").is_dir(), job_count),
            self._doctor_check(
                "private_archive",
                self.registry.storage_root.is_dir(),
                str(self.registry.storage_root),
                severity="warning",
            ),
            self._doctor_check(
                "private_archive_env",
                bool(os.environ.get("REVIEWS_PRIVATE_ARCHIVE_ROOT")),
                os.environ.get("REVIEWS_PRIVATE_ARCHIVE_ROOT")
                or "não configurado; o arquivo pode apenas não estar montado",
                severity="warning",
            ),
        ]
        integrity = validate_registry(
            self.registry,
            verify_files=False,
            repository_root=REPOSITORY_ROOT,
            require_external_storage=False,
        )
        checks.append(
            self._doctor_check(
                "registry_integrity",
                bool(integrity.get("passed")),
                integrity.get("issues") or "registro íntegro",
            )
        )
        blocking = [check for check in checks if check["status"] == "error"]
        return {
            "passed": not blocking,
            "checks": checks,
            "workspace": info,
            "registry_validation": integrity,
        }

    @staticmethod
    def _doctor_check(
        check_id: str,
        passed: bool,
        detail: Any = None,
        *,
        severity: str = "error",
    ) -> dict[str, Any]:
        return {
            "check_id": check_id,
            "status": "success" if passed else severity,
            "detail": detail,
        }

    def dashboard(self) -> dict[str, Any]:
        data = self.registry.dashboard()
        with self.registry.connection() as connection:
            editions = [
                _decode_json_columns(dict(row))
                for row in connection.execute(
                    """
                    SELECT e.*,
                           MAX(ev.occurred_at) AS last_activity,
                           COUNT(DISTINCT d.document_id) AS document_count
                    FROM editions e
                    LEFT JOIN documents d
                      ON d.edition_id=e.edition_id AND d.deleted_at IS NULL
                    LEFT JOIN editorial_events ev ON ev.edition_id=e.edition_id
                    WHERE e.deleted_at IS NULL
                    GROUP BY e.edition_id
                    ORDER BY COALESCE(MAX(ev.occurred_at), e.updated_at) DESC
                    LIMIT 8
                    """
                )
            ]
            data["recent_editions"] = editions
            data["active_runs"] = [
                _decode_json_columns(dict(row))
                for row in connection.execute(
                    """
                    SELECT * FROM agent_runs
                    WHERE status IN ('queued', 'running', 'waiting_for_human')
                    ORDER BY started_at DESC
                    """
                )
            ]
            data["pending_lessons"] = connection.execute(
                "SELECT COUNT(*) AS n FROM editorial_lessons WHERE status='proposed'"
            ).fetchone()["n"]
            data["pending_decisions"] = connection.execute(
                """
                SELECT COUNT(*) AS n FROM change_requests
                WHERE status IN ('pending', 'open', 'awaiting_decision')
                  AND deleted_at IS NULL
                """
            ).fetchone()["n"]
        return data

    def list_editions(
        self,
        *,
        query: str | None = None,
        status: str | None = None,
        limit: int = 250,
        offset: int = 0,
    ) -> dict[str, Any]:
        where = ["e.deleted_at IS NULL"]
        params: list[Any] = []
        if query:
            where.append(
                "(lower(e.canonical_title) LIKE ? OR lower(COALESCE(e.summary,'')) LIKE ?)"
            )
            needle = f"%{query.casefold()}%"
            params.extend((needle, needle))
        if status:
            where.append("e.status=?")
            params.append(status)
        params.extend((max(1, min(limit, 1000)), max(0, offset)))
        sql = f"""
            SELECT e.*,
                   COUNT(DISTINCT d.document_id) AS document_count,
                   COUNT(DISTINCT CASE WHEN d.classification_confirmed=0
                                      THEN d.document_id END) AS pending_classifications,
                   MAX(ev.occurred_at) AS last_activity,
                   COUNT(DISTINCT a.approval_id) AS approval_count,
                   COUNT(DISTINCT p.publication_id) AS publication_count
            FROM editions e
            LEFT JOIN documents d
              ON d.edition_id=e.edition_id AND d.deleted_at IS NULL
            LEFT JOIN editorial_events ev ON ev.edition_id=e.edition_id
            LEFT JOIN approvals a ON a.edition_id=e.edition_id
            LEFT JOIN publication_records p
              ON p.edition_id=e.edition_id AND p.deleted_at IS NULL
            WHERE {" AND ".join(where)}
            GROUP BY e.edition_id
            ORDER BY COALESCE(MAX(ev.occurred_at), e.updated_at) DESC,
                     e.canonical_title
            LIMIT ? OFFSET ?
        """
        with self.registry.connection() as connection:
            rows = [_decode_json_columns(dict(row)) for row in connection.execute(sql, params)]
            total = connection.execute(
                f"SELECT COUNT(*) AS n FROM editions e WHERE {' AND '.join(where)}",
                params[:-2],
            ).fetchone()["n"]
        return {"items": rows, "total": total, "limit": params[-2], "offset": params[-1]}

    def inspect_edition(self, edition_id: str) -> dict[str, Any]:
        try:
            data = self.registry.edition_record(edition_id)
        except KeyError as exc:
            raise UiBridgeError(
                "EDITION_NOT_FOUND",
                "A edição solicitada não existe no registro.",
                action="Atualize a lista de edições e tente novamente.",
                category="usage_error",
                details={"edition_id": edition_id},
            ) from exc
        with self.registry.connection() as connection:
            data["versions"] = self._rows(
                connection,
                """
                SELECT v.*, d.canonical_title AS document_title
                FROM document_versions v
                JOIN documents d ON d.document_id=v.document_id
                WHERE d.edition_id=?
                ORDER BY v.created_at DESC, v.version_number DESC
                """,
                (edition_id,),
            )
            data["approvals"] = self._rows(
                connection,
                "SELECT * FROM approvals WHERE edition_id=? ORDER BY created_at DESC",
                (edition_id,),
            )
            data["publications"] = self._rows(
                connection,
                """
                SELECT * FROM publication_records
                WHERE edition_id=? AND deleted_at IS NULL ORDER BY published_at DESC
                """,
                (edition_id,),
            )
            data["agent_runs"] = self._rows(
                connection,
                "SELECT * FROM agent_runs WHERE edition_id=? ORDER BY started_at DESC",
                (edition_id,),
            )
            data["memory"] = self._rows(
                connection,
                """
                SELECT mi.*, mis.document_id, mis.version_id, mis.relationship,
                       mis.relevance_reason
                FROM memory_items mi
                JOIN memory_item_sources mis
                  ON mis.memory_item_id=mi.memory_item_id
                WHERE mis.edition_id=? AND mi.deleted_at IS NULL
                ORDER BY mi.memory_tier DESC, mi.created_at DESC
                """,
                (edition_id,),
            )
            data["lessons"] = self._rows(
                connection,
                """
                SELECT DISTINCT l.*
                FROM editorial_lessons l
                JOIN memory_item_sources mis ON mis.lesson_id=l.lesson_id
                WHERE mis.edition_id=? AND l.deleted_at IS NULL
                ORDER BY l.proposed_at DESC
                """,
                (edition_id,),
            )
            data["audits"] = [
                row
                for row in data["documents"]
                if row.get("document_type_id") == "type.audit"
                or row.get("editorial_function_id") == "function.audit"
            ]
        data["documents"] = [_decode_json_columns(row) for row in data["documents"]]
        data["timeline"] = [_decode_json_columns(row) for row in data["timeline"]]
        data["lineage"] = [_decode_json_columns(row) for row in data["lineage"]]
        return data

    def list_jobs(self) -> dict[str, Any]:
        items: list[dict[str, Any]] = []
        for job_file in sorted((REPOSITORY_ROOT / "jobs").rglob("job.yml")):
            if job_file.parent.name == "JOB-YYYY-NNN":
                continue
            try:
                payload = load_data(job_file)
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                items.append(
                    {
                        "job_id": job_file.parent.name,
                        "job_dir": str(job_file.parent),
                        "load_error": str(exc),
                    }
                )
                continue
            items.append(
                {
                    "job_id": payload.get("job_id") or job_file.parent.name,
                    "job_dir": str(job_file.parent),
                    "state": payload.get("state"),
                    "status": payload.get("status"),
                    "topic": payload.get("topic") or payload.get("request", {}).get("topic"),
                    "edition_type": payload.get("edition_type"),
                    "editor": payload.get("editor"),
                    "updated_at": payload.get("updated_at"),
                }
            )
        return {"items": items, "total": len(items)}

    def inspect_job(self, job_id: str) -> dict[str, Any]:
        job_dir = self._resolve_job(job_id)
        payload = load_data(job_dir / "job.yml")
        return {"job_dir": str(job_dir), "job": payload}

    def list_documents(
        self,
        *,
        edition_id: str | None = None,
        status: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        where = ["d.deleted_at IS NULL"]
        params: list[Any] = []
        if edition_id:
            where.append("d.edition_id=?")
            params.append(edition_id)
        if status:
            where.append("d.status_id=?")
            params.append(status)
        params.append(max(1, min(limit, 2000)))
        with self.registry.connection() as connection:
            rows = self._rows(
                connection,
                f"""
                SELECT d.*, e.canonical_title AS edition_title,
                       COUNT(v.version_id) AS version_count,
                       MAX(v.version_number) AS current_version_number
                FROM documents d
                LEFT JOIN editions e ON e.edition_id=d.edition_id
                LEFT JOIN document_versions v ON v.document_id=d.document_id
                WHERE {" AND ".join(where)}
                GROUP BY d.document_id
                ORDER BY d.updated_at DESC, d.canonical_title
                LIMIT ?
                """,
                tuple(params),
            )
        return {"items": rows, "total": len(rows)}

    def list_versions(
        self,
        *,
        document_id: str | None = None,
        edition_id: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        where = ["1=1"]
        params: list[Any] = []
        if document_id:
            where.append("v.document_id=?")
            params.append(document_id)
        if edition_id:
            where.append("d.edition_id=?")
            params.append(edition_id)
        params.append(max(1, min(limit, 2000)))
        with self.registry.connection() as connection:
            rows = self._rows(
                connection,
                f"""
                SELECT v.*, d.canonical_title AS document_title, d.edition_id,
                       EXISTS(SELECT 1 FROM approvals a
                              WHERE a.version_id=v.version_id
                                AND a.decision='approved') AS approved,
                       EXISTS(SELECT 1 FROM publication_records p
                              WHERE p.version_id=v.version_id
                                AND p.deleted_at IS NULL) AS published
                FROM document_versions v
                JOIN documents d ON d.document_id=v.document_id
                WHERE {" AND ".join(where)}
                ORDER BY v.created_at DESC, v.version_number DESC
                LIMIT ?
                """,
                tuple(params),
            )
        return {"items": rows, "total": len(rows)}

    def compare_versions(self, from_version_id: str, to_version_id: str) -> dict[str, Any]:
        self.registry.ensure_actor(
            "reviews-desktop",
            display_name="Reviews Desktop",
            role="editor",
        )
        return self.registry.compare_and_record_versions(
            from_version_id,
            to_version_id,
            actor_id="reviews-desktop",
        )

    def list_events(
        self,
        *,
        edition_id: str | None = None,
        document_id: str | None = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        where = ["1=1"]
        params: list[Any] = []
        if edition_id:
            where.append("edition_id=?")
            params.append(edition_id)
        if document_id:
            where.append("document_id=?")
            params.append(document_id)
        params.append(max(1, min(limit, 2000)))
        with self.registry.connection() as connection:
            rows = self._rows(
                connection,
                f"""
                SELECT * FROM editorial_events
                WHERE {" AND ".join(where)}
                ORDER BY occurred_at DESC, event_id DESC LIMIT ?
                """,
                tuple(params),
            )
        return {"items": rows, "total": len(rows), "append_only": True}

    def list_approvals(self, *, edition_id: str | None = None) -> dict[str, Any]:
        return self._simple_list(
            "approvals",
            "edition_id",
            edition_id,
            order_by="created_at DESC",
        )

    def list_publications(self, *, edition_id: str | None = None) -> dict[str, Any]:
        return self._simple_list(
            "publication_records",
            "edition_id",
            edition_id,
            order_by="published_at DESC",
            extra_where="deleted_at IS NULL",
        )

    def list_agent_runs(self, *, edition_id: str | None = None) -> dict[str, Any]:
        return self._simple_list(
            "agent_runs",
            "edition_id",
            edition_id,
            order_by="started_at DESC",
        )

    def list_pending_decisions(self) -> dict[str, Any]:
        with self.registry.connection() as connection:
            rows = self._rows(
                connection,
                """
                SELECT * FROM change_requests
                WHERE status IN ('pending', 'open', 'awaiting_decision')
                  AND deleted_at IS NULL
                ORDER BY requested_at DESC
                """,
            )
        return {"items": rows, "total": len(rows)}

    def list_classification_queue(self, *, limit: int = 500) -> dict[str, Any]:
        with self.registry.connection() as connection:
            rows = self._rows(
                connection,
                """
                SELECT cs.*, d.canonical_title, d.original_name, d.edition_id,
                       es.full_path AS source_path, es.original_url
                FROM classification_suggestions cs
                LEFT JOIN documents d ON d.document_id=cs.document_id
                LEFT JOIN external_sources es
                  ON es.external_source_id=cs.external_source_id
                WHERE cs.status='pending'
                ORDER BY cs.confidence DESC, cs.created_at DESC
                LIMIT ?
                """,
                (max(1, min(limit, 2000)),),
            )
        return {"items": rows, "total": len(rows)}

    def search_memory(
        self,
        query: str,
        *,
        tier: str = "validated",
        include_rejected: bool = False,
        limit: int = 50,
    ) -> dict[str, Any]:
        if tier not in {"validated", "historical"}:
            raise UiBridgeError(
                "INVALID_MEMORY_TIER",
                "A camada de memória deve ser validated ou historical.",
                action="Selecione uma camada de memória válida.",
                category="usage_error",
            )
        rows = self.registry.search_memory(
            query,
            memory_tier=tier,
            include_rejected=include_rejected,
            limit=max(1, min(limit, 200)),
        )
        return {"items": rows, "total": len(rows), "memory_tier": tier}

    def list_lessons(self, *, status: str | None = None) -> dict[str, Any]:
        return self._simple_list(
            "editorial_lessons",
            "status",
            status,
            order_by="proposed_at DESC",
            extra_where="deleted_at IS NULL",
        )

    def list_drive_imports(self) -> dict[str, Any]:
        return self._simple_list(
            "drive_import_jobs",
            None,
            None,
            order_by="started_at DESC",
        )

    def inspect_drive_import(self, import_job_id: str) -> dict[str, Any]:
        with self.registry.connection() as connection:
            job = connection.execute(
                "SELECT * FROM drive_import_jobs WHERE import_job_id=?",
                (import_job_id,),
            ).fetchone()
            if job is None:
                raise UiBridgeError(
                    "DRIVE_IMPORT_NOT_FOUND",
                    "O manifesto de importação solicitado não existe.",
                    action="Atualize a lista de importações.",
                    category="usage_error",
                )
            items = self._rows(
                connection,
                """
                SELECT * FROM drive_import_items
                WHERE import_job_id=? ORDER BY processed_at, import_item_id
                """,
                (import_job_id,),
            )
        return {"import_job": _decode_json_columns(dict(job)), "items": items}

    def validate_drive_archive(self, *, require_external_storage: bool = False) -> dict[str, Any]:
        return validate_registry(
            self.registry,
            verify_files=True,
            repository_root=REPOSITORY_ROOT,
            require_external_storage=require_external_storage,
        )

    def create_job(
        self,
        *,
        sources: list[str],
        topic: str,
        edition_type: str = "analise",
        editor: str = "Reviews Desktop",
        notes: str | None = None,
        copy_inputs: bool = False,
    ) -> dict[str, Any]:
        if not sources:
            raise UiBridgeError(
                "SOURCE_REQUIRED",
                "Ao menos uma fonte é obrigatória para criar o job.",
                action="Selecione uma ou mais fontes dentro do workspace.",
                category="usage_error",
            )
        arguments: list[str] = []
        for source in sources:
            arguments.extend(("--source", source))
        arguments.extend(("--topic", topic, "--edition-type", edition_type, "--editor", editor))
        if notes:
            arguments.extend(("--notes", notes))
        if copy_inputs:
            arguments.append("--copy-inputs")
        return _run_core_script("create_job.py", arguments)

    def validate_job(
        self,
        job_id: str,
        *,
        target_state: str | None = None,
    ) -> dict[str, Any]:
        arguments = [str(self._resolve_job(job_id))]
        if target_state:
            arguments.extend(("--target-state", target_state))
        return _run_core_script("validate_job.py", arguments)

    def advance_job(
        self,
        job_id: str,
        *,
        target_state: str | None = None,
        actor: str = "reviews-desktop",
        human_approval: bool = False,
    ) -> dict[str, Any]:
        arguments = [str(self._resolve_job(job_id)), "--advance", "--actor", actor]
        if target_state:
            arguments.extend(("--target-state", target_state))
        if human_approval:
            arguments.append("--human-approval")
        return _run_core_script("validate_job.py", arguments)

    def correct_classification(self, **payload: Any) -> dict[str, Any]:
        actor = str(payload.pop("actor", "reviews-desktop"))
        role = str(payload.pop("role", "editor"))
        self.registry.ensure_actor(actor, display_name=actor, role=role)
        self.registry.correct_classification(actor_id=actor, **payload)
        return {"document_id": payload["document_id"], "classification": "confirmed"}

    def propose_lesson(self, **payload: Any) -> dict[str, Any]:
        actor = str(payload.pop("actor", "reviews-desktop"))
        role = str(payload.pop("role", "editor"))
        self.registry.ensure_actor(actor, display_name=actor, role=role)
        lesson_id = self.registry.propose_lesson(actor_id=actor, **payload)
        return {"lesson_id": lesson_id}

    def approve_lesson(self, lesson_id: str, *, rationale: str, actor: str, role: str) -> dict[str, Any]:
        self.registry.ensure_actor(actor, display_name=actor, role=role)
        memory_item_id = self.registry.approve_lesson(
            lesson_id,
            actor_id=actor,
            rationale=rationale,
        )
        return {"lesson_id": lesson_id, "memory_item_id": memory_item_id}

    def dispatch(self, command: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        args = dict(arguments or {})
        routes = {
            "doctor": self.doctor,
            "workspace-info": self.workspace_info,
            "dashboard": self.dashboard,
            "list-editions": self.list_editions,
            "inspect-edition": self.inspect_edition,
            "list-jobs": self.list_jobs,
            "inspect-job": self.inspect_job,
            "list-documents": self.list_documents,
            "list-versions": self.list_versions,
            "compare-versions": self.compare_versions,
            "list-events": self.list_events,
            "list-approvals": self.list_approvals,
            "list-publications": self.list_publications,
            "list-agent-runs": self.list_agent_runs,
            "list-pending-decisions": self.list_pending_decisions,
            "list-classification-queue": self.list_classification_queue,
            "search-memory": self.search_memory,
            "list-lessons": self.list_lessons,
            "list-drive-imports": self.list_drive_imports,
            "inspect-drive-import": self.inspect_drive_import,
            "validate-drive-archive": self.validate_drive_archive,
            "create-job": self.create_job,
            "validate-job": self.validate_job,
            "advance-job": self.advance_job,
            "correct-classification": self.correct_classification,
            "propose-lesson": self.propose_lesson,
            "approve-lesson": self.approve_lesson,
        }
        handler = routes.get(command)
        if handler is None:
            raise UiBridgeError(
                "COMMAND_NOT_ALLOWED",
                "O comando não pertence à allowlist pública da ponte.",
                action="Atualize o aplicativo ou selecione uma ação disponível.",
                category="usage_error",
                details={"command": command},
            )
        try:
            return envelope(command, data=handler(**args))
        except UiBridgeError:
            raise
        except PermissionError as exc:
            raise UiBridgeError(
                "EDITORIAL_ROLE_DENIED",
                str(exc),
                action="Selecione um papel editorial habilitado ou solicite revisão humana.",
                category="editorial_block",
            ) from exc
        except KeyError as exc:
            raise UiBridgeError(
                "ENTITY_NOT_FOUND",
                "A entidade solicitada não foi localizada.",
                action="Atualize os dados e tente novamente.",
                category="usage_error",
                details={"entity_id": str(exc).strip("'")},
            ) from exc
        except (OSError, ValueError, RuntimeError) as exc:
            raise UiBridgeError(
                "CORE_OPERATION_FAILED",
                str(exc),
                action="Revise os parâmetros e o diagnóstico do workspace.",
                category="environment_failure",
                retryable=True,
            ) from exc

    def _resolve_job(self, job_id: str) -> Path:
        candidate = (REPOSITORY_ROOT / "jobs" / job_id).resolve()
        jobs_root = (REPOSITORY_ROOT / "jobs").resolve()
        if candidate.parent != jobs_root or not (candidate / "job.yml").is_file():
            raise UiBridgeError(
                "JOB_NOT_FOUND",
                "O job solicitado não existe dentro do workspace configurado.",
                action="Atualize a lista de jobs e tente novamente.",
                category="usage_error",
                details={"job_id": job_id},
            )
        return candidate

    @staticmethod
    def _rows(
        connection: Any,
        sql: str,
        params: tuple[Any, ...] = (),
    ) -> list[dict[str, Any]]:
        return [_decode_json_columns(dict(row)) for row in connection.execute(sql, params)]

    def _simple_list(
        self,
        table: str,
        filter_column: str | None,
        filter_value: str | None,
        *,
        order_by: str,
        extra_where: str | None = None,
    ) -> dict[str, Any]:
        allowed = {
            "approvals",
            "publication_records",
            "agent_runs",
            "editorial_lessons",
            "drive_import_jobs",
        }
        if table not in allowed:
            raise AssertionError(table)
        where: list[str] = []
        params: list[Any] = []
        if extra_where:
            where.append(extra_where)
        if filter_column and filter_value:
            where.append(f"{filter_column}=?")
            params.append(filter_value)
        clause = f"WHERE {' AND '.join(where)}" if where else ""
        with self.registry.connection() as connection:
            rows = self._rows(
                connection,
                f"SELECT * FROM {table} {clause} ORDER BY {order_by}",
                tuple(params),
            )
        return {"items": rows, "total": len(rows)}
