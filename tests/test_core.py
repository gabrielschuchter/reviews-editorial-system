from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.anti_ai import lint_text
from reviews_editorial.claims import (
    audit_draft_text,
    build_claim_ledger,
    verify_number_records,
)
from reviews_editorial.documents import normalize_job_documents
from reviews_editorial.edition_router import recommend_edition_type
from reviews_editorial.exemplars import select_exemplars
from reviews_editorial.feedback import validate_feedback
from reviews_editorial.io import load_data
from reviews_editorial.jobs import (
    confirm_document_validation,
    create_job,
    validate_job_shape,
)
from reviews_editorial.pipeline import validate_pipeline


class EditorialSafetyTests(unittest.TestCase):
    @staticmethod
    def _verified_claim(number: str = "12") -> dict[str, object]:
        return {
            "job_id": "JOB-2026-001",
            "claim_text": f"O escore caiu {number} pontos.",
            "claim_type": "result",
            "source_document": "DOC-artigo",
            "page": 4,
            "table": None,
            "figure": None,
            "section": "Results",
            "source_excerpt": f"Mean change was {number} points.",
            "verification_status": "verified",
            "allowed_in_public_draft": True,
            "provenance": {
                "extracted_at": "2026-07-25T12:00:00Z",
                "extracted_by": "test-suite",
                "method": "manual-double-check",
                "source_hash": "0" * 64,
            },
        }

    def test_empty_ledger_is_invalid(self) -> None:
        ledger = build_claim_ledger([])
        self.assertFalse(ledger["validation"]["valid"])
        self.assertIn(
            "ledger-empty",
            {item["issue_id"] for item in ledger["validation"]["issues"]},
        )

    def test_number_without_public_claim_is_critical(self) -> None:
        ledger = build_claim_ledger([])
        audit = audit_draft_text("O escore caiu 12 pontos.", ledger)
        self.assertFalse(audit["passed"])
        self.assertTrue(any(item["severity"] == "critical" for item in audit["issues"]))

    def test_verified_sourced_number_can_pass(self) -> None:
        claim = self._verified_claim()
        ledger = build_claim_ledger([claim])
        self.assertTrue(ledger["validation"]["valid"])
        self.assertTrue(audit_draft_text(claim["claim_text"], ledger)["passed"])

    def test_number_tokens_do_not_confuse_12_with_120(self) -> None:
        ledger = build_claim_ledger([self._verified_claim("12")])
        audit = audit_draft_text("O escore caiu 120 pontos.", ledger)
        self.assertFalse(audit["passed"])
        self.assertIn(
            "unmapped-number:120",
            {item["issue_id"] for item in audit["issues"]},
        )

    def test_divergent_number_is_critical(self) -> None:
        result = verify_number_records(
            [
                {
                    "record_id": "NUM-1",
                    "reported_value": "12",
                    "source_document": "DOC-artigo",
                    "locator": "p. 4",
                    "unit": "pontos",
                    "direction": "decrease",
                    "verification_status": "divergent",
                }
            ]
        )
        self.assertFalse(result["valid"])
        self.assertTrue(
            any(
                item["severity"] == "critical"
                and "diverg" in item["message"].casefold()
                for item in result["issues"]
            )
        )

    def test_ai_linter_flags_tool_token(self) -> None:
        result = lint_text("Segundo turn0search0, o resultado foi favorável.")
        self.assertFalse(result["passed"])
        self.assertIn("tool-token-leak", {item["rule"] for item in result["findings"]})

    def test_guideline_routes_to_guideline_summary(self) -> None:
        result = recommend_edition_type({"study_design": "clinical-guideline"})
        self.assertEqual(result["selected_type"], "guideline-summary")

    def test_feedback_does_not_mutate_rules(self) -> None:
        result = validate_feedback(
            [
                {
                    "feedback_id": "FDB-1",
                    "feedback_type": "style-correction",
                    "generalizable": False,
                }
            ]
        )
        self.assertTrue(result["valid"])
        self.assertFalse(result["automatic_rule_mutation_performed"])


class JobTests(unittest.TestCase):
    def test_create_and_normalize_job(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.md"
            source.write_text("# Documento\n\nTexto de teste sem afirmação científica.", encoding="utf-8")
            job_dir = create_job(root / "jobs", [source], topic="Teste", year=2026)
            job = load_data(job_dir / "job.yml")
            self.assertEqual(validate_job_shape(job), [])
            normalize_job_documents(job_dir, [str(source)])
            report = validate_pipeline(job_dir)
            self.assertTrue(report["valid"])
            self.assertTrue((job_dir / "normalized" / "document-inventory.json").is_file())

    def test_mutated_source_hash_blocks_normalization(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.md"
            source.write_text("versão original", encoding="utf-8")
            job_dir = create_job(root / "jobs", [source], topic="Teste", year=2026)
            source.write_text("versão alterada", encoding="utf-8")

            result = normalize_job_documents(job_dir, [str(source)])

            self.assertEqual(result["inventory"]["documents"], [])
            self.assertTrue(result["validation"]["critical_errors"])
            self.assertIn(
                "hash da fonte diverge",
                result["validation"]["critical_errors"][0]["error"],
            )

    def test_same_stem_sources_get_distinct_normalized_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "a" / "source.md"
            second = root / "b" / "source.md"
            first.parent.mkdir()
            second.parent.mkdir()
            first.write_text("primeiro documento", encoding="utf-8")
            second.write_text("segundo documento", encoding="utf-8")
            job_dir = create_job(
                root / "jobs",
                [first, second],
                topic="Teste",
                year=2026,
            )

            result = normalize_job_documents(job_dir, [str(first), str(second)])
            normalized_paths = {
                item["normalized_path"] for item in result["inventory"]["documents"]
            }

            self.assertEqual(len(result["inventory"]["documents"]), 2)
            self.assertEqual(len(normalized_paths), 2)
            self.assertTrue(all(Path(path).is_file() for path in normalized_paths))

    def test_manual_checklist_must_be_confirmed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.md"
            source.write_text("documento para revisão", encoding="utf-8")
            job_dir = create_job(root / "jobs", [source], topic="Teste", year=2026)
            normalize_job_documents(job_dir, [str(source)])

            with self.assertRaisesRegex(RuntimeError, "pendentes"):
                confirm_document_validation(job_dir, "Revisor")


class ExemplarTests(unittest.TestCase):
    def test_holdout_is_excluded_from_selection(self) -> None:
        manifest = {
            "records": [
                {
                    "record_id": "REC-holdout",
                    "classification_level": "A",
                    "classification_status": "approved",
                    "holdout": True,
                    "editorial_metadata": {
                        "edition_type": "clinical-answer-classic",
                    },
                },
                {
                    "record_id": "REC-eligible",
                    "classification_level": "B",
                    "classification_status": "approved",
                    "holdout": False,
                    "editorial_metadata": {
                        "edition_type": "clinical-answer-classic",
                    },
                },
            ]
        }

        result = select_exemplars(
            manifest,
            edition_type="clinical-answer-classic",
        )

        self.assertEqual(
            [item["record_id"] for item in result["selected"]],
            ["REC-eligible"],
        )


if __name__ == "__main__":
    unittest.main()
