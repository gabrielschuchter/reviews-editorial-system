#!/usr/bin/env python3
"""CLI do registro editorial, memória, importação e linhagem."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

from reviews_editorial.drive_import import (  # noqa: E402
    DriveImporter,
    approved_drive_ids_from_corpus_manifest,
)
from reviews_editorial.io import load_data  # noqa: E402
from reviews_editorial.registry import EditorialRegistry  # noqa: E402
from reviews_editorial.registry_validation import (  # noqa: E402
    validate_drive_import,
    validate_registry,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = REPOSITORY_ROOT / ".reviews" / "editorial-registry.sqlite3"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Registro central local do Reviews. Papéis são gates editoriais auditáveis, "
            "não autenticação."
        )
    )
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument(
        "--storage",
        default=os.environ.get("REVIEWS_PRIVATE_ARCHIVE_ROOT"),
    )
    parser.add_argument("--actor", default="reviews-editor")
    parser.add_argument(
        "--role",
        default="editor",
        choices=(
            "administrator",
            "editor",
            "methodological_reviewer",
            "editorial_reviewer",
            "auditor",
            "contributor",
            "viewer",
            "agent",
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Aplicar migrações e taxonomia.")
    subparsers.add_parser("dashboard", help="Totais do registro geral.")

    edition = subparsers.add_parser("edition", help="Exibir edição, árvore, timeline e linhagem.")
    edition.add_argument("edition_id")

    search = subparsers.add_parser("search-memory", help="Recuperar memória com proveniência.")
    search.add_argument("query")
    search.add_argument("--tier", choices=("validated", "historical"), default="validated")
    search.add_argument("--include-rejected", action="store_true")
    search.add_argument("--limit", type=int, default=20)

    sync = subparsers.add_parser("sync-job", help="Indexar ou atualizar um job existente.")
    sync.add_argument("job_dir")

    sync_all = subparsers.add_parser(
        "sync-all-jobs",
        help="Migrar e reindexar todos os jobs existentes de forma retomável.",
    )
    sync_all.add_argument(
        "jobs_root",
        nargs="?",
        default=str(REPOSITORY_ROOT / "jobs"),
    )

    validate = subparsers.add_parser(
        "validate-registry",
        help="Validar imutabilidade, referências, memória e cópias privadas.",
    )
    validate.add_argument("--no-file-hashes", action="store_true")
    validate.add_argument("--require-external-storage", action="store_true")

    validate_drive = subparsers.add_parser(
        "validate-drive-import",
        help="Comparar snapshot, manifesto e cópias privadas do Drive.",
    )
    validate_drive.add_argument("snapshot")
    validate_drive.add_argument("--manifest")

    import_drive = subparsers.add_parser(
        "import-drive", help="Importar fisicamente os arquivos permitidos de um snapshot."
    )
    import_drive.add_argument("snapshot")
    import_drive.add_argument("--metadata-only", action="store_true")
    import_drive.add_argument("--resume-failed-from")
    import_drive.add_argument(
        "--max-items",
        type=int,
        help="Processar somente o próximo lote ainda não preservado.",
    )
    import_drive.add_argument(
        "--approved-corpus-manifest",
        default=str(REPOSITORY_ROOT / "corpus" / "manifest.yml"),
    )

    import_history = subparsers.add_parser(
        "import-drive-history",
        help="Ingerir snapshots privados de revisões e comentários do Drive.",
    )
    import_history.add_argument("history_path")

    subparsers.add_parser("seed-example", help="Criar a trajetória mínima de desenvolvimento.")

    compare = subparsers.add_parser("compare", help="Comparar e persistir duas versões.")
    compare.add_argument("from_version_id")
    compare.add_argument("to_version_id")

    restore = subparsers.add_parser("restore", help="Restaurar criando nova versão derivada.")
    restore.add_argument("version_id")
    restore.add_argument("--reason", required=True)

    approve = subparsers.add_parser("approve-version", help="Aprovar uma versão exata.")
    approve.add_argument("version_id")
    approve.add_argument("--rationale", required=True)
    approve.add_argument("--approval-type", default="editorial")

    publish = subparsers.add_parser("publish-version", help="Publicar uma versão já aprovada.")
    publish.add_argument("version_id")
    publish.add_argument("--rationale", required=True)
    publish.add_argument("--destination")
    publish.add_argument("--external-url")

    correct = subparsers.add_parser(
        "correct-classification", help="Confirmar ou corrigir classificação com novo evento."
    )
    correct.add_argument("document_id")
    correct.add_argument("--document-type", required=True)
    correct.add_argument("--function", required=True)
    correct.add_argument("--stage", required=True)
    correct.add_argument("--status", required=True)
    correct.add_argument("--meaning", required=True)
    correct.add_argument("--justification", required=True)

    propose = subparsers.add_parser("propose-lesson", help="Propor lição não normativa.")
    propose.add_argument("--title", required=True)
    propose.add_argument("--content", required=True)
    propose.add_argument("--lesson-type", required=True)
    propose.add_argument("--scope", required=True)
    propose.add_argument("--rationale", required=True)
    propose.add_argument("--confidence", type=float, required=True)
    propose.add_argument("--source-version", action="append", default=[])

    approve_lesson = subparsers.add_parser(
        "approve-lesson", help="Aprovar lição e promovê-la à memória validada."
    )
    approve_lesson.add_argument("lesson_id")
    approve_lesson.add_argument("--rationale", required=True)

    output = subparsers.add_parser(
        "register-output", help="Persistir prompt, contexto e resultado integral de um agente."
    )
    output.add_argument("--edition-id", required=True)
    output.add_argument("--agent-name", required=True)
    output.add_argument("--model")
    output.add_argument("--purpose", required=True)
    output.add_argument("--prompt-file", required=True)
    output.add_argument("--context-file", required=True)
    output.add_argument("--configuration-file")
    output.add_argument("--result-file", required=True)
    output.add_argument("--output-type", required=True)
    output.add_argument("--document-title", required=True)
    output.add_argument("--discarded", action="store_true")
    return parser


def _print(payload) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args()
    registry = EditorialRegistry(args.db, storage_root=args.storage)
    registry.ensure_actor(args.actor, display_name=args.actor, role=args.role)

    if args.command == "init":
        _print(
            {
                "database": str(registry.database_path),
                "storage": str(registry.storage_root),
                "migrations": "applied",
                "roles_are_editorial_gates": True,
            }
        )
    elif args.command == "dashboard":
        _print(registry.dashboard())
    elif args.command == "edition":
        _print(registry.edition_record(args.edition_id))
    elif args.command == "search-memory":
        _print(
            registry.search_memory(
                args.query,
                memory_tier=args.tier,
                include_rejected=args.include_rejected,
                limit=args.limit,
            )
        )
    elif args.command == "sync-job":
        _print(registry.sync_job(args.job_dir, actor_id=args.actor))
    elif args.command == "sync-all-jobs":
        _print(registry.sync_jobs(args.jobs_root, actor_id=args.actor))
    elif args.command == "validate-registry":
        report = validate_registry(
            registry,
            verify_files=not args.no_file_hashes,
            repository_root=REPOSITORY_ROOT,
            require_external_storage=args.require_external_storage,
        )
        _print(report)
        if not report["passed"]:
            return 1
    elif args.command == "validate-drive-import":
        report = validate_drive_import(
            registry,
            args.snapshot,
            manifest_path=args.manifest,
            repository_root=REPOSITORY_ROOT,
        )
        _print(report)
        if not report["passed"]:
            return 1
    elif args.command == "import-drive":
        manifest_path = Path(args.approved_corpus_manifest)
        approved = (
            approved_drive_ids_from_corpus_manifest(manifest_path)
            if manifest_path.is_file()
            else set()
        )
        importer = DriveImporter(registry, actor_id=args.actor)
        _print(
            importer.import_snapshot(
                args.snapshot,
                download_files=not args.metadata_only,
                approved_drive_ids=approved,
                resume_failed_from=args.resume_failed_from,
                max_items=args.max_items,
            )
        )
    elif args.command == "import-drive-history":
        importer = DriveImporter(registry, actor_id=args.actor)
        _print(importer.import_history_snapshots(args.history_path))
    elif args.command == "seed-example":
        _print(registry.seed_minimum_example(actor_id=args.actor))
    elif args.command == "compare":
        _print(
            registry.compare_and_record_versions(
                args.from_version_id,
                args.to_version_id,
                actor_id=args.actor,
            )
        )
    elif args.command == "restore":
        _print(
            {
                "restored_version_id": registry.restore_version(
                    args.version_id,
                    actor_id=args.actor,
                    reason=args.reason,
                )
            }
        )
    elif args.command == "approve-version":
        _print(
            {
                "approval_id": registry.approve_version(
                    args.version_id,
                    actor_id=args.actor,
                    rationale=args.rationale,
                    approval_type=args.approval_type,
                )
            }
        )
    elif args.command == "publish-version":
        _print(
            {
                "publication_id": registry.publish_version(
                    args.version_id,
                    actor_id=args.actor,
                    rationale=args.rationale,
                    destination=args.destination,
                    external_url=args.external_url,
                )
            }
        )
    elif args.command == "correct-classification":
        registry.correct_classification(
            document_id=args.document_id,
            actor_id=args.actor,
            document_type_id=args.document_type,
            editorial_function_id=args.function,
            stage_id=args.stage,
            status_id=args.status,
            editorial_meaning=args.meaning,
            justification=args.justification,
        )
        _print({"document_id": args.document_id, "classification": "confirmed"})
    elif args.command == "propose-lesson":
        _print(
            {
                "lesson_id": registry.propose_lesson(
                    title=args.title,
                    content=args.content,
                    lesson_type=args.lesson_type,
                    scope=args.scope,
                    actor_id=args.actor,
                    rationale=args.rationale,
                    confidence=args.confidence,
                    source_version_ids=args.source_version,
                )
            }
        )
    elif args.command == "approve-lesson":
        _print(
            {
                "memory_item_id": registry.approve_lesson(
                    args.lesson_id,
                    actor_id=args.actor,
                    rationale=args.rationale,
                )
            }
        )
    elif args.command == "register-output":
        prompt = Path(args.prompt_file).read_text(encoding="utf-8")
        context = load_data(args.context_file)
        configuration = (
            load_data(args.configuration_file) if args.configuration_file else {}
        )
        result = Path(args.result_file).read_text(encoding="utf-8")
        _print(
            registry.register_generated_output(
                edition_id=args.edition_id,
                actor_id=args.actor,
                agent_name=args.agent_name,
                model=args.model,
                purpose=args.purpose,
                prompt=prompt,
                context=context,
                configuration=configuration,
                result=result,
                output_type=args.output_type,
                document_title=args.document_title,
                discarded=args.discarded,
            )
        )
    else:
        raise AssertionError(args.command)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        raise
