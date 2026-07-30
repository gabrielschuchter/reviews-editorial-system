from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.drive_import import (
    DriveImportError,
    DriveImporter,
    EXCLUDED_FOLDER_IDS,
    validate_snapshot,
)
from reviews_editorial.classification import classify_drive_item
from reviews_editorial.jobs import create_job
from reviews_editorial.registry import EditorialRegistry, RegistryPermissionError


def _snapshot(items: list[dict], *, files_included: int) -> dict:
    return {
        "snapshot_version": "1.0.0",
        "source": "test",
        "source_root": {
            "id": "root",
            "name": "Reviews",
            "url": "https://drive.google.com/drive/folders/root",
        },
        "scanned_at": "2026-07-30T00:00:00Z",
        "exclusion_policy": {
            "excluded_folder_ids": sorted(EXCLUDED_FOLDER_IDS),
            "match_by": ["folder_id", "tree_location"],
            "content_fetched": False,
            "content_classified": False,
            "content_indexed": False,
        },
        "totals": {
            "folders_found": 5,
            "files_found": files_included + 13,
            "folders_included": 3,
            "files_included": files_included,
            "folders_excluded": 2,
            "files_excluded": 13,
        },
        "exclusions": [
            {
                "folder_id": "1XPBN2r5RXsfKtcuzD7peZXBLV812IN0i",
                "path": "Reviews/Documentos/POPs",
                "reason": "árvore excluída",
                "descendant_file_count": 5,
            },
            {
                "folder_id": "1zt-6Jt46GOyzFJZlKm6oNqlMuV7wKgQt",
                "path": "Reviews/Documentos/Diretrizes/Estatutos",
                "reason": "árvore excluída",
                "descendant_file_count": 8,
            },
        ],
        "items": items,
    }


def _item(
    item_id: str,
    name: str,
    path: str,
    mime: str,
    *,
    item_kind: str = "file",
) -> dict:
    return {
        "id": item_id,
        "name": name,
        "item_kind": item_kind,
        "mime_type": mime,
        "size_bytes": 10,
        "path": path,
        "parent_id": "parent",
        "created_time": "2026-01-01T00:00:00Z",
        "modified_time": "2026-07-01T00:00:00Z",
        "web_url": f"https://drive.google.com/open?id={item_id}",
        "source_root_name": "Reviews",
    }


class FakeDownloader:
    def __init__(self, payloads: dict[str, bytes], fail_ids: set[str] | None = None):
        self.payloads = payloads
        self.fail_ids = set(fail_ids or set())

    def download_spec(self, item):
        mime = item.get("mime_type") or "application/octet-stream"
        extension = ".docx" if mime == "application/vnd.google-apps.document" else Path(
            item["name"]
        ).suffix
        stored_mime = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if extension == ".docx"
            else mime
        )
        return "https://example.invalid", stored_mime, extension

    def download(self, item, destination):
        if item["id"] in self.fail_ids:
            raise DriveImportError(f"falha controlada: {item['id']}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(self.payloads[item["id"]])
        _, stored_mime, extension = self.download_spec(item)
        return {
            "path": str(destination),
            "mime_type": stored_mime,
            "extension": extension,
            "resumed": False,
            "bytes": destination.stat().st_size,
        }


class RegistryTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.registry = EditorialRegistry(
            self.root / "registry.sqlite3",
            storage_root=self.root / "private-storage",
        )
        self.registry.ensure_actor("editor", display_name="Editor", role="editor")

    def tearDown(self):
        self.temporary.cleanup()

    def _document(self):
        self.registry.upsert_edition(
            edition_id="EDITION-TEST",
            canonical_title="Edição de teste",
            status="drafting",
            editorial_meaning="Edição de teste.",
            actor_id="editor",
            confirmed=True,
        )
        return self.registry.create_document(
            external_key="test:document",
            canonical_title="Resposta clínica",
            original_name="resposta.md",
            actor_id="editor",
            edition_id="EDITION-TEST",
            document_type_id="type.clinical_answer",
            editorial_function_id="function.draft",
            stage_id="stage.drafting",
            status_id="status.preliminary",
            editorial_meaning="Rascunho não aprovado.",
            confidence=1.0,
            confirmed=True,
        )


class ImmutabilityAndLineageTests(RegistryTestCase):
    def test_versions_and_events_are_append_only(self):
        document_id = self._document()
        first = self.registry.create_version(
            document_id=document_id,
            content_hash="a" * 64,
            actor_id="editor",
            reason="Primeira versão.",
            change_summary="Início.",
            status_id="status.preliminary",
            editorial_meaning="Rascunho.",
            content_text="Participantes: 120.",
        )
        second = self.registry.create_version(
            document_id=document_id,
            content_hash="b" * 64,
            actor_id="editor",
            reason="Correção numérica.",
            change_summary="Participantes corrigidos.",
            status_id="status.awaiting_review",
            editorial_meaning="Versão corrigida aguardando revisão.",
            content_text="Participantes: 97.",
        )
        with self.registry.connection() as connection:
            versions = connection.execute(
                "SELECT version_id, version_number, previous_version_id "
                "FROM document_versions ORDER BY version_number"
            ).fetchall()
            event_id = connection.execute(
                "SELECT event_id FROM editorial_events LIMIT 1"
            ).fetchone()["event_id"]
        self.assertEqual([row["version_number"] for row in versions], [1, 2])
        self.assertEqual(versions[1]["previous_version_id"], first)
        self.assertEqual(versions[1]["version_id"], second)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.registry.connection() as connection:
                connection.execute(
                    "UPDATE document_versions SET reason='apagado' WHERE version_id=?",
                    (first,),
                )
        with self.assertRaises(sqlite3.IntegrityError):
            with self.registry.connection() as connection:
                connection.execute(
                    "UPDATE editorial_events SET justification='apagada' WHERE event_id=?",
                    (event_id,),
                )

    def test_restore_creates_a_new_version(self):
        document_id = self._document()
        first = self.registry.create_version(
            document_id=document_id,
            content_hash="1" * 64,
            actor_id="editor",
            reason="Primeira versão.",
            change_summary="Início.",
            status_id="status.preliminary",
            editorial_meaning="Primeira versão.",
            content_text="Texto original.",
        )
        self.registry.create_version(
            document_id=document_id,
            content_hash="2" * 64,
            actor_id="editor",
            reason="Segunda versão.",
            change_summary="Mudança.",
            status_id="status.awaiting_review",
            editorial_meaning="Segunda versão.",
            content_text="Texto alterado.",
        )
        restored = self.registry.restore_version(
            first, actor_id="editor", reason="Restaurar conteúdo original."
        )
        with self.registry.connection() as connection:
            rows = connection.execute(
                "SELECT version_number, restored_from_version_id FROM document_versions "
                "ORDER BY version_number"
            ).fetchall()
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[-1]["version_number"], 3)
        self.assertEqual(rows[-1]["restored_from_version_id"], first)
        self.assertNotEqual(restored, first)

    def test_diff_detects_numeric_and_interpretation_changes(self):
        document_id = self._document()
        first = self.registry.create_version(
            document_id=document_id,
            content_hash="3" * 64,
            actor_id="editor",
            reason="Versão causal.",
            change_summary="Início.",
            status_id="status.preliminary",
            editorial_meaning="Rascunho.",
            content_text="O horário causou melhora em 120 participantes.",
        )
        second = self.registry.create_version(
            document_id=document_id,
            content_hash="4" * 64,
            actor_id="editor",
            reason="Correção metodológica.",
            change_summary="Causalidade suavizada e número corrigido.",
            status_id="status.awaiting_review",
            editorial_meaning="Versão corrigida.",
            content_text="O horário foi associado à melhora em 97 participantes.",
        )
        report = self.registry.compare_and_record_versions(
            first, second, actor_id="editor"
        )
        self.assertTrue(report["numeric_changes"])
        self.assertTrue(report["interpretation_changes"])
        with self.registry.connection() as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) AS n FROM version_diffs").fetchone()["n"],
                1,
            )


class ApprovalAndMemoryTests(RegistryTestCase):
    def test_publication_remains_bound_to_exact_approved_version(self):
        document_id = self._document()
        first = self.registry.create_version(
            document_id=document_id,
            content_hash="5" * 64,
            actor_id="editor",
            reason="Versão aprovada.",
            change_summary="Pronta.",
            status_id="status.approved",
            editorial_meaning="Versão aprovada.",
            content_text="Texto aprovado.",
        )
        self.registry.approve_version(first, actor_id="editor", rationale="Revisão concluída.")
        publication = self.registry.publish_version(
            first, actor_id="editor", rationale="Publicação autorizada."
        )
        second = self.registry.create_version(
            document_id=document_id,
            content_hash="6" * 64,
            actor_id="editor",
            reason="Correção posterior.",
            change_summary="Nova versão.",
            status_id="status.preliminary",
            editorial_meaning="Correção ainda não aprovada.",
            content_text="Texto posterior.",
        )
        with self.registry.connection() as connection:
            row = connection.execute(
                "SELECT version_id FROM publication_records WHERE publication_id=?",
                (publication,),
            ).fetchone()
        self.assertEqual(row["version_id"], first)
        self.assertNotEqual(row["version_id"], second)

    def test_draft_cannot_enter_validated_memory_and_viewer_cannot_approve(self):
        document_id = self._document()
        version_id = self.registry.create_version(
            document_id=document_id,
            content_hash="7" * 64,
            actor_id="editor",
            reason="Rascunho.",
            change_summary="Início.",
            status_id="status.preliminary",
            editorial_meaning="Rascunho.",
            content_text="Rascunho não aprovado.",
        )
        with self.assertRaises(RegistryPermissionError):
            self.registry.promote_memory(
                actor_id="editor",
                title="Rascunho",
                content="Não promover.",
                category="memory.good_example",
                scope="geral",
                confidence=1.0,
                justification="Tentativa de teste.",
                version_id=version_id,
            )
        self.registry.ensure_actor("viewer", display_name="Viewer", role="viewer")
        with self.assertRaises(RegistryPermissionError):
            self.registry.approve_version(
                version_id, actor_id="viewer", rationale="Não autorizado."
            )
        self.assertEqual(self.registry.search_memory("rascunho"), [])
        historical = self.registry.search_memory("rascunho", memory_tier="historical")
        self.assertTrue(historical)

    def test_lesson_stays_proposed_until_human_approval(self):
        document_id = self._document()
        version_id = self.registry.create_version(
            document_id=document_id,
            content_hash="8" * 64,
            actor_id="editor",
            reason="Base da lição.",
            change_summary="Início.",
            status_id="status.approved",
            editorial_meaning="Base aprovada.",
            content_text="Redução calórica acompanhou a intervenção.",
        )
        lesson = self.registry.propose_lesson(
            title="Considerar redução calórica",
            content="Não atribuir o efeito apenas ao horário.",
            lesson_type="memory.interpretation_alert",
            scope="alimentação com tempo restrito",
            actor_id="editor",
            rationale="Comparação editorial.",
            confidence=0.9,
            source_version_ids=[version_id],
        )
        with self.registry.connection() as connection:
            before = connection.execute(
                "SELECT status FROM editorial_lessons WHERE lesson_id=?", (lesson,)
            ).fetchone()["status"]
            validated_before = connection.execute(
                "SELECT COUNT(*) AS n FROM memory_items WHERE memory_tier='validated'"
            ).fetchone()["n"]
        self.assertEqual(before, "proposed")
        self.assertEqual(validated_before, 0)
        with self.assertRaises(RegistryPermissionError):
            self.registry.approve_lesson(
                lesson,
                actor_id="editor",
                rationale="NÃ£o deveria aceitar fonte ainda nÃ£o aprovada.",
            )
        self.registry.approve_version(
            version_id,
            actor_id="editor",
            rationale="VersÃ£o-fonte revisada antes da liÃ§Ã£o.",
        )
        memory_id = self.registry.approve_lesson(
            lesson, actor_id="editor", rationale="Lição revisada e aprovada."
        )
        with self.registry.connection() as connection:
            row = connection.execute(
                "SELECT memory_tier, normative, approved_by FROM memory_items "
                "WHERE memory_item_id=?",
                (memory_id,),
            ).fetchone()
        self.assertEqual(row["memory_tier"], "validated")
        self.assertEqual(row["normative"], 1)
        self.assertEqual(row["approved_by"], "editor")


class DriveImportTests(RegistryTestCase):
    def _write_snapshot(self, payload: dict, name: str = "snapshot.json") -> Path:
        path = self.root / name
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def test_exclusions_allowed_guideline_physical_copy_and_idempotency(self):
        items = [
            _item(
                "folder-models",
                "Modelos de Reviews",
                "Reviews/Documentos/Modelos de Reviews",
                "application/vnd.google-apps.folder",
                item_kind="folder",
            ),
            _item(
                "allowed-guideline",
                "Modelo Diretrizes",
                "Reviews/Documentos/Modelos de Reviews/Modelo Diretrizes",
                "application/vnd.google-apps.document",
            ),
            _item(
                "source-a",
                "guideline-a.pdf",
                "Reviews/Testes/ACG SII/guideline-a.pdf",
                "application/pdf",
            ),
            _item(
                "source-b",
                "guideline-copy.pdf",
                "Reviews/Testes/Outro/guideline-copy.pdf",
                "application/pdf",
            ),
        ]
        snapshot_path = self._write_snapshot(_snapshot(items, files_included=3))
        payloads = {
            "allowed-guideline": b"durable google doc export",
            "source-a": b"%PDF same content",
            "source-b": b"%PDF same content",
        }
        importer = DriveImporter(
            self.registry,
            actor_id="editor",
            downloader=FakeDownloader(payloads),
        )
        first = importer.import_snapshot(snapshot_path)
        self.assertEqual(first["status"], "completed")
        self.assertEqual(first["totals"]["files_imported"], 3)
        self.assertEqual(first["totals"]["files_excluded"], 13)
        self.assertTrue(
            any(
                item["drive_id"] == "allowed-guideline"
                for item in first["classification_pending"]
            )
            or first["totals_by_classification"].get("type.template") == 1
        )
        with self.registry.connection() as connection:
            before = {
                table: connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
                for table in ("documents", "document_versions", "document_files")
            }
            imported_ids = {
                row["external_id"]
                for row in connection.execute(
                    "SELECT external_id FROM external_sources"
                )
            }
            duplicates = connection.execute(
                "SELECT COUNT(*) AS n FROM document_relationships "
                "WHERE relationship_type='possible_duplicate_of'"
            ).fetchone()["n"]
            source_links = connection.execute(
                """
                SELECT COUNT(DISTINCT dfs.external_source_id) AS n
                FROM document_file_sources dfs
                JOIN external_sources es
                  ON es.external_source_id=dfs.external_source_id
                WHERE es.provider='google-drive'
                """
            ).fetchone()["n"]
        self.assertIn("allowed-guideline", imported_ids)
        self.assertNotIn("1XPBN2r5RXsfKtcuzD7peZXBLV812IN0i", imported_ids)
        self.assertNotIn("1zt-6Jt46GOyzFJZlKm6oNqlMuV7wKgQt", imported_ids)
        self.assertGreaterEqual(duplicates, 1)
        self.assertEqual(source_links, 3)
        self.assertEqual(len(list(self.registry.storage_root.rglob("*.pdf"))), 2)
        second = importer.import_snapshot(snapshot_path)
        self.assertEqual(second["status"], "completed")
        with self.registry.connection() as connection:
            after = {
                table: connection.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()["n"]
                for table in ("documents", "document_versions", "document_files")
            }
        self.assertEqual(before, after)

    def test_failed_import_can_resume_only_failed_item(self):
        items = [
            _item(
                "ok",
                "ok.pdf",
                "Reviews/Testes/A/ok.pdf",
                "application/pdf",
            ),
            _item(
                "fails",
                "fails.pdf",
                "Reviews/Testes/B/fails.pdf",
                "application/pdf",
            ),
        ]
        snapshot_path = self._write_snapshot(_snapshot(items, files_included=2))
        first = DriveImporter(
            self.registry,
            actor_id="editor",
            downloader=FakeDownloader({"ok": b"ok", "fails": b"fixed"}, {"fails"}),
        ).import_snapshot(snapshot_path)
        self.assertEqual(first["status"], "partial")
        self.assertEqual(first["totals"]["files_imported"], 1)
        self.assertEqual(first["totals"]["errors"], 1)
        second = DriveImporter(
            self.registry,
            actor_id="editor",
            downloader=FakeDownloader({"ok": b"ok", "fails": b"fixed"}),
        ).import_snapshot(snapshot_path, resume_failed_from=first["import_job_id"])
        self.assertEqual(second["totals"]["files_imported"], 1)
        self.assertEqual(second["totals"]["skipped_not_failed"], 1)
        with self.registry.connection() as connection:
            result = connection.execute(
                """
                SELECT result FROM drive_import_items
                WHERE import_job_id=? AND external_id='fails'
                """,
                (second["import_job_id"],),
            ).fetchone()["result"]
        self.assertEqual(result, "imported")

    def test_drive_history_import_is_private_idempotent_metadata(self):
        item = _item(
            "history-file",
            "Histórico",
            "Reviews/Testes/Histórico",
            "application/vnd.google-apps.document",
        )
        snapshot_path = self._write_snapshot(
            _snapshot([item], files_included=1)
        )
        DriveImporter(
            self.registry,
            actor_id="editor",
            downloader=FakeDownloader({"history-file": b"current version"}),
        ).import_snapshot(snapshot_path)
        history_dir = self.root / "private-history"
        history_dir.mkdir()
        history_fragment = {
            "history_snapshot_version": "1.0.0",
            "items": [
                {
                    "id": "history-file",
                    "revisions": [
                        {
                            "id": "1",
                            "modified_time": "2026-01-01T00:00:00Z",
                            "author": {"display_name": "Editor"},
                            "limitation": "Conteúdo histórico não baixado.",
                        },
                        {
                            "id": "2",
                            "modified_time": "2026-02-01T00:00:00Z",
                            "author": {"display_name": "Editor"},
                            "limitation": "Conteúdo histórico não baixado.",
                        },
                    ],
                    "comments": [
                        {
                            "id": "comment-1",
                            "content": "Revisar conclusão.",
                            "author": {"display_name": "Revisor"},
                            "resolved": False,
                            "replies": [],
                        }
                    ],
                }
            ],
        }
        (history_dir / "fragment-001.json").write_text(
            json.dumps(history_fragment, ensure_ascii=False),
            encoding="utf-8",
        )
        importer = DriveImporter(self.registry, actor_id="editor")
        first = importer.import_history_snapshots(history_dir)
        second = importer.import_history_snapshots(history_dir)
        self.assertEqual(first["totals"]["revisions_inserted"], 2)
        self.assertEqual(first["totals"]["comments_inserted"], 1)
        self.assertEqual(second["totals"]["revisions_inserted"], 0)
        self.assertEqual(second["totals"]["comments_inserted"], 0)

    def test_snapshot_rejects_any_prohibited_descendant(self):
        forbidden = _item(
            "forbidden",
            "segredo.docx",
            "Reviews/Documentos/POPs/segredo.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        with self.assertRaises(DriveImportError):
            validate_snapshot(_snapshot([forbidden], files_included=1))

    def test_delivery_month_file_uses_parent_folder_as_edition(self):
        item = _item(
            "delivery",
            "01",
            (
                "Reviews/Entregas Gabriel/"
                "Cópia de Creatina mulheres menopausa 15/01"
            ),
            "application/vnd.google-apps.document",
        )
        classification = classify_drive_item(item)
        self.assertEqual(
            classification.suggested_edition_title,
            "Creatina mulheres menopausa 15",
        )


class ExistingFlowIntegrationTests(RegistryTestCase):
    def test_create_job_automatically_registers_edition_and_source(self):
        source = self.root / "source.md"
        source.write_text("# Fonte\n", encoding="utf-8")
        jobs_root = self.root / "jobs"
        job_dir = create_job(
            jobs_root,
            [source],
            topic="Edição integrada",
            editor="Editor",
            copy_inputs=True,
        )
        registry_path = self.root / ".reviews" / "editorial-registry.sqlite3"
        self.assertTrue(registry_path.is_file())
        integrated = EditorialRegistry(registry_path)
        record = integrated.edition_record(f"EDITION-{job_dir.name}")
        self.assertEqual(record["edition"]["canonical_title"], "Edição integrada")
        self.assertGreaterEqual(len(record["documents"]), 2)
        self.assertTrue(record["timeline"])


if __name__ == "__main__":
    unittest.main()
