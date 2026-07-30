"""Validações estruturais e de integridade do registro editorial local."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import sha256_file
from .registry import EditorialRegistry


REQUIRED_TRIGGERS = {
    "document_versions_no_update",
    "document_versions_no_delete",
    "editorial_events_no_update",
    "editorial_events_no_delete",
    "approvals_no_update",
    "approvals_no_delete",
}


def validate_registry(
    registry: EditorialRegistry,
    *,
    verify_files: bool = True,
    repository_root: str | Path | None = None,
    require_external_storage: bool = False,
) -> dict[str, Any]:
    """Audita invariantes que não dependem de interpretação editorial."""

    issues: list[str] = []
    checks: dict[str, Any] = {}
    with registry.connection() as connection:
        migrations = {
            row["version"]
            for row in connection.execute("SELECT version FROM schema_migrations")
        }
        required_migrations = {
            path.name for path in registry.migrations_root.glob("*.sql")
        }
        missing_migrations = sorted(required_migrations - migrations)
        if missing_migrations:
            issues.append(f"migrações ausentes: {missing_migrations}")
        checks["migrations"] = {
            "applied": sorted(migrations),
            "missing": missing_migrations,
        }

        triggers = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='trigger'"
            )
        }
        missing_triggers = sorted(REQUIRED_TRIGGERS - triggers)
        if missing_triggers:
            issues.append(f"triggers de imutabilidade ausentes: {missing_triggers}")
        checks["immutability_triggers"] = {
            "present": sorted(triggers & REQUIRED_TRIGGERS),
            "missing": missing_triggers,
        }

        foreign_key_issues = [
            dict(row) for row in connection.execute("PRAGMA foreign_key_check")
        ]
        if foreign_key_issues:
            issues.append(
                f"referências inválidas no SQLite: {len(foreign_key_issues)}"
            )
        checks["foreign_keys"] = {"issues": foreign_key_issues}

        broken_chains = connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM document_versions current
            LEFT JOIN document_versions previous
              ON previous.version_id=current.previous_version_id
            WHERE current.version_number > 1
              AND (
                  previous.version_id IS NULL
                  OR previous.document_id <> current.document_id
                  OR previous.version_number <> current.version_number - 1
              )
            """
        ).fetchone()["n"]
        if broken_chains:
            issues.append(f"cadeias de versão quebradas: {broken_chains}")
        checks["version_chains"] = {"broken": broken_chains}

        invalid_publications = connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM publication_records p
            LEFT JOIN approvals a
              ON a.approval_id=p.approval_id
             AND a.version_id=p.version_id
             AND a.document_id=p.document_id
             AND a.decision='approved'
            WHERE a.approval_id IS NULL
            """
        ).fetchone()["n"]
        if invalid_publications:
            issues.append(
                f"publicações sem aprovação da versão exata: {invalid_publications}"
            )
        checks["exact_publication_version"] = {"invalid": invalid_publications}

        invalid_direct_memory = connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM memory_items mi
            JOIN memory_item_sources mis
              ON mis.memory_item_id=mi.memory_item_id
            JOIN document_versions v ON v.version_id=mis.version_id
            LEFT JOIN approvals a
              ON a.version_id=v.version_id AND a.decision='approved'
            WHERE mi.memory_tier='validated'
              AND (
                  a.approval_id IS NULL
                  OR v.status_id IN (
                      'status.preliminary',
                      'status.unverified',
                      'status.rejected',
                      'status.do_not_use'
                  )
              )
            """
        ).fetchone()["n"]
        invalid_lesson_memory = connection.execute(
            """
            SELECT COUNT(DISTINCT validated.memory_item_id) AS n
            FROM memory_items validated
            JOIN memory_item_sources validated_source
              ON validated_source.memory_item_id=validated.memory_item_id
            JOIN editorial_lessons lesson
              ON lesson.lesson_id=validated_source.lesson_id
            JOIN memory_item_sources evidence
              ON evidence.lesson_id=lesson.lesson_id
             AND evidence.version_id IS NOT NULL
            JOIN document_versions v ON v.version_id=evidence.version_id
            LEFT JOIN approvals a
              ON a.version_id=v.version_id AND a.decision='approved'
            WHERE validated.memory_tier='validated'
              AND (
                  lesson.status <> 'approved'
                  OR a.approval_id IS NULL
                  OR v.status_id IN (
                      'status.preliminary',
                      'status.unverified',
                      'status.rejected',
                      'status.do_not_use'
                  )
              )
            """
        ).fetchone()["n"]
        validated_without_source = connection.execute(
            """
            SELECT COUNT(*) AS n
            FROM memory_items mi
            LEFT JOIN memory_item_sources mis
              ON mis.memory_item_id=mi.memory_item_id
            WHERE mi.memory_tier='validated'
            GROUP BY mi.memory_item_id
            HAVING COUNT(mis.memory_item_source_id)=0
            """
        ).fetchall()
        source_less_count = len(validated_without_source)
        if invalid_direct_memory or invalid_lesson_memory or source_less_count:
            issues.append(
                "memória validada contém origem não aprovada, rascunho ou item sem fonte"
            )
        checks["validated_memory"] = {
            "invalid_direct_sources": invalid_direct_memory,
            "invalid_lesson_sources": invalid_lesson_memory,
            "items_without_sources": source_less_count,
        }

        file_rows = [
            dict(row)
            for row in connection.execute(
                """
                SELECT document_file_id, storage_path, content_hash, size_bytes,
                       private
                FROM document_files
                ORDER BY document_file_id
                """
            )
        ]
        counts = {
            table: connection.execute(
                f"SELECT COUNT(*) AS n FROM {table}"
            ).fetchone()["n"]
            for table in (
                "editions",
                "documents",
                "document_versions",
                "editorial_events",
                "document_relationships",
                "memory_items",
                "agent_runs",
                "generated_outputs",
                "external_sources",
                "document_files",
                "document_file_sources",
                "drive_import_jobs",
            )
        }

    missing_files: list[str] = []
    hash_mismatches: list[str] = []
    non_private: list[str] = []
    if verify_files:
        for row in file_rows:
            path = Path(row["storage_path"])
            if not path.is_file():
                missing_files.append(row["document_file_id"])
                continue
            if sha256_file(path) != row["content_hash"]:
                hash_mismatches.append(row["document_file_id"])
            if row["private"] != 1:
                non_private.append(row["document_file_id"])
    if missing_files:
        issues.append(f"cópias privadas ausentes: {len(missing_files)}")
    if hash_mismatches:
        issues.append(f"hashes de cópias privadas divergentes: {len(hash_mismatches)}")
    if non_private:
        issues.append(f"arquivos marcados como não privados: {len(non_private)}")
    checks["files"] = {
        "registered": len(file_rows),
        "missing": missing_files,
        "hash_mismatches": hash_mismatches,
        "non_private": non_private,
    }

    if require_external_storage:
        if repository_root is None:
            issues.append(
                "repository_root é obrigatório quando armazenamento externo é exigido"
            )
        else:
            repository = Path(repository_root).resolve()
            try:
                registry.storage_root.relative_to(repository)
                inside_repository = True
            except ValueError:
                inside_repository = False
            if inside_repository:
                issues.append("arquivo privado está dentro do repositório")
            checks["external_storage"] = {
                "required": True,
                "inside_repository": inside_repository,
                "storage_root": str(registry.storage_root),
            }

    return {
        "passed": not issues,
        "issues": issues,
        "database": str(registry.database_path),
        "storage_root": str(registry.storage_root),
        "counts": counts,
        "checks": checks,
    }


def validate_drive_import(
    registry: EditorialRegistry,
    snapshot_path: str | Path,
    *,
    manifest_path: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    """Compara snapshot permitido, manifesto final e arquivo físico preservado."""

    import json
    import re

    from .drive_import import validate_snapshot

    snapshot_file = Path(snapshot_path).resolve()
    snapshot = json.loads(snapshot_file.read_text(encoding="utf-8-sig"))
    validate_snapshot(snapshot)
    file_items = [
        item for item in snapshot["items"] if item.get("item_kind") == "file"
    ]
    folder_items = [
        item for item in snapshot["items"] if item.get("item_kind") == "folder"
    ]
    expected_file_ids = {str(item["id"]) for item in file_items}
    expected_folder_ids = {str(item["id"]) for item in folder_items}
    excluded_folder_ids = {
        str(item["folder_id"]) for item in snapshot.get("exclusions", [])
    }
    issues: list[str] = []

    with registry.connection() as connection:
        covered_file_ids = {
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
                """
            )
        }
        covered_folder_ids = {
            row["external_id"]
            for row in connection.execute(
                """
                SELECT DISTINCT external_id
                FROM drive_import_items
                WHERE item_kind='folder' AND result='folder_registered'
                """
            )
        }
        prohibited_registered = [
            dict(row)
            for row in connection.execute(
                """
                SELECT external_id, full_path
                FROM external_sources
                WHERE provider='google-drive'
                  AND (
                      external_id IN (?, ?)
                      OR replace(full_path, '\\', '/') LIKE '%/POPs/%'
                      OR replace(full_path, '\\', '/') LIKE '%/POPs'
                      OR replace(full_path, '\\', '/') LIKE '%/Diretrizes/Estatutos/%'
                      OR replace(full_path, '\\', '/') LIKE '%/Diretrizes/Estatutos'
                  )
                """,
                tuple(sorted(excluded_folder_ids)),
            )
        ]
        file_metadata_missing = [
            dict(row)
            for row in connection.execute(
                """
                SELECT external_id, full_path
                FROM external_sources
                WHERE provider='google-drive'
                  AND mime_type <> 'application/vnd.google-apps.folder'
                  AND (
                      original_url IS NULL OR original_url=''
                      OR full_path IS NULL OR full_path=''
                      OR mime_type IS NULL OR mime_type=''
                      OR modified_time IS NULL OR modified_time=''
                  )
                """
            )
        ]
        guideline_rows = [
            dict(row)
            for row in connection.execute(
                """
                SELECT external_id, original_name, full_path
                FROM external_sources
                WHERE provider='google-drive'
                  AND lower(full_path) NOT LIKE '%/diretrizes/estatutos/%'
                """
            )
            if re.search(
                r"diretriz|guideline",
                f"{row['original_name']} {row['full_path']}",
                flags=re.IGNORECASE,
            )
        ]
        history_counts = {
            "revisions_registered": connection.execute(
                "SELECT COUNT(*) AS n FROM drive_revisions"
            ).fetchone()["n"],
            "comments_registered": connection.execute(
                "SELECT COUNT(*) AS n FROM drive_comments"
            ).fetchone()["n"],
            "files_with_revision_metadata": connection.execute(
                "SELECT COUNT(DISTINCT external_source_id) AS n FROM drive_revisions"
            ).fetchone()["n"],
        }

    missing_files = sorted(expected_file_ids - covered_file_ids)
    missing_folders = sorted(expected_folder_ids - covered_folder_ids)
    unexpected_files = sorted(covered_file_ids - expected_file_ids)
    if missing_files:
        issues.append(f"arquivos permitidos sem cópia registrada: {len(missing_files)}")
    if missing_folders:
        issues.append(f"pastas permitidas sem registro: {len(missing_folders)}")
    if prohibited_registered:
        issues.append(
            f"itens de árvores proibidas registrados: {len(prohibited_registered)}"
        )
    if file_metadata_missing:
        issues.append(
            f"fontes permitidas sem metadados mínimos: {len(file_metadata_missing)}"
        )
    if not guideline_rows:
        issues.append("nenhuma diretriz permitida fora das árvores excluídas foi importada")

    manifest: dict[str, Any] | None = None
    if manifest_path is not None:
        manifest_file = Path(manifest_path).resolve()
        manifest = json.loads(manifest_file.read_text(encoding="utf-8-sig"))
        if manifest.get("status") != "completed":
            issues.append("manifesto final não está concluído")
        totals = manifest.get("totals") or {}
        for field in (
            "folders_found",
            "files_found",
            "folders_included",
            "files_included",
            "folders_excluded",
            "files_excluded",
        ):
            if totals.get(field) != snapshot["totals"].get(field):
                issues.append(
                    f"total {field} diverge entre snapshot e manifesto"
                )
        if totals.get("files_imported") != len(expected_file_ids):
            issues.append("manifesto não confirma todos os arquivos permitidos")
        if manifest.get("errors"):
            issues.append(f"manifesto final contém erros: {len(manifest['errors'])}")

    storage_check = validate_registry(
        registry,
        verify_files=True,
        repository_root=repository_root,
        require_external_storage=repository_root is not None,
    )
    issues.extend(
        f"registro: {issue}" for issue in storage_check["issues"]
    )
    limitations = (
        list(manifest.get("limitations", []))
        if manifest is not None
        else ["manifesto final não foi fornecido para comparação"]
    )
    if history_counts["revisions_registered"]:
        limitations = [
            item
            for item in limitations
            if "Revisões e comentários só são contabilizados" not in item
        ]
        limitations.insert(
            0,
            "O manifesto de arquivos foi emitido antes da captura separada do "
            "histórico; os totais de revisões e comentários acima vêm do registro.",
        )
    return {
        "passed": not issues,
        "issues": issues,
        "snapshot": str(snapshot_file),
        "manifest": str(Path(manifest_path).resolve()) if manifest_path else None,
        "totals": {
            **snapshot["totals"],
            "expected_file_ids": len(expected_file_ids),
            "covered_file_ids": len(expected_file_ids & covered_file_ids),
            "expected_folder_ids": len(expected_folder_ids),
            "covered_folder_ids": len(expected_folder_ids & covered_folder_ids),
            "unexpected_file_ids": len(unexpected_files),
            "allowed_guideline_files": len(guideline_rows),
            "prohibited_registered": len(prohibited_registered),
            "metadata_missing": len(file_metadata_missing),
            **history_counts,
        },
        "missing_file_ids": missing_files,
        "missing_folder_ids": missing_folders,
        "unexpected_file_ids": unexpected_files,
        "allowed_guideline_examples": guideline_rows[:20],
        "prohibited_registered": prohibited_registered,
        "registry": storage_check,
        "limitations": limitations,
    }
