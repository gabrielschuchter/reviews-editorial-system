from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.anti_ai import audit_text, lint_text
from reviews_editorial.claims import build_claim_ledger
from reviews_editorial.humanizer import humanize_text
from reviews_editorial.io import dump_data, load_data, write_text
from reviews_editorial.schema_validation import validate


class AntiAiAuditTests(unittest.TestCase):
    def test_occurrence_report_has_required_localized_contract(self) -> None:
        report = audit_text("Uma síntese crítica das principais recomendações atualizadas.")
        finding = next(item for item in report["findings"] if item["category"] == "self-importance-announcement")

        self.assertEqual(finding["review_status"], "candidate")
        self.assertTrue(finding["requires_manual_confirmation"])
        self.assertTrue(finding["excerpt"])
        self.assertTrue(finding["evidence"])
        self.assertTrue(finding["localized_recommendation"])
        self.assertFalse(any("score" in key.casefold() or "autoria" in key.casefold() for key in report))
        schema = load_data(ROOT / "schemas" / "anti-ai-report.schema.json")
        self.assertEqual(validate(report, schema), [])

    def test_single_human_transition_is_not_a_formulaic_violation(self) -> None:
        report = audit_text(
            "A recomendação depende da população, da condição e da certeza disponível. "
            "Por fim, a aplicação precisa respeitar as exceções da fonte."
        )
        self.assertNotIn("formulaic-transition", {item["category"] for item in report["findings"]})

    def test_repeated_transition_is_reported_per_occurrence(self) -> None:
        report = audit_text(
            "Além disso, a primeira decisão depende do risco. "
            "Além disso, a segunda decisão depende da população."
        )
        findings = [item for item in report["findings"] if item["category"] == "formulaic-transition"]
        self.assertEqual(len(findings), 2)
        self.assertTrue(all(item["false_positive_risk"] == "high" for item in findings))

    def test_tool_token_remains_critical_for_backward_compatibility(self) -> None:
        report = lint_text("Segundo turn0search0, o resultado foi favorável.")
        self.assertFalse(report["passed"])
        self.assertIn("tool-token-leak", {item["rule"] for item in report["findings"]})

    def test_extended_taxonomy_keeps_empty_conclusion_and_symmetry_as_candidates(self) -> None:
        text = (
            "Seja por risco, seja por benefício, seja por aplicabilidade, a decisão exige contexto clínico.\n\n"
            "Em conclusão, é fundamental continuar avançando sem ignorar as escolhas do cuidado."
        )
        categories = {item["category"] for item in audit_text(text)["findings"]}
        self.assertIn("overly-symmetric-sentence", categories)
        self.assertIn("relevance-inflation", categories)
        self.assertIn("empty-conclusion", categories)


class HumanizerTests(unittest.TestCase):
    @staticmethod
    def _finding(report: dict[str, object], category: str) -> dict[str, object]:
        return next(item for item in report["findings"] if item["category"] == category)  # type: ignore[index]

    @staticmethod
    def _ledger_for(text: str) -> dict[str, object]:
        claim = {
            "job_id": "JOB-2026-001",
            "claim_text": text,
            "claim_type": "result",
            "source_document": "DOC-ACG-2023",
            "page": 1,
            "table": "Tabela 1",
            "figure": None,
            "section": "Recomendações",
            "source_excerpt": text,
            "verification_status": "verified",
            "allowed_in_public_draft": True,
            "provenance": {
                "extracted_at": "2026-07-25T12:00:00Z",
                "extracted_by": "test-suite",
                "method": "manual-double-check",
                "source_hash": "0" * 64,
            },
        }
        return build_claim_ledger([claim])

    def test_unconfirmed_finding_cannot_mutate_text(self) -> None:
        text = "Uma síntese crítica das principais recomendações atualizadas."
        report = audit_text(text)

        result = humanize_text(text, report, [])

        self.assertEqual(result["status"], "no-confirmed-findings")
        self.assertEqual(result["revised_text"], text)
        self.assertEqual(result["summary"]["applied"], 0)

    def test_confirmed_subtitle_is_edited_minimally_with_diff(self) -> None:
        text = "Uma síntese crítica das principais recomendações atualizadas."
        report = audit_text(text)
        finding = self._finding(report, "self-importance-announcement")

        result = humanize_text(
            text,
            report,
            [{"finding_id": finding["finding_id"], "status": "confirmed", "reviewed_by": "editora-humana"}],
        )

        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["revised_text"], "As principais recomendações atualizadas.")
        self.assertIn("--- before", result["unified_diff"])
        self.assertEqual(result["summary"]["applied"], 1)
        schema = load_data(ROOT / "schemas" / "humanization-diff.schema.json")
        self.assertEqual(validate(result, schema), [])

    def test_confirmed_edit_preserves_number_unit_and_modality_then_reaudits(self) -> None:
        text = (
            "Vale destacar que a estratégia restritiva usa limiar de 7 g/dL. "
            "A recomendação é condicional, com evidência de baixa qualidade."
        )
        report = audit_text(text)
        finding = self._finding(report, "metadiscourse")
        ledger = self._ledger_for(text)

        result = humanize_text(
            text,
            report,
            [{"finding_id": finding["finding_id"], "status": "confirmed", "reviewed_by": "editora-humana"}],
            claim_ledger=ledger,
        )

        self.assertEqual(result["status"], "completed")
        self.assertIn("7 g/dL", result["revised_text"])
        self.assertIn("condicional", result["revised_text"])
        applied = next(item for item in result["changes"] if item["status"] == "applied")
        self.assertTrue(applied["protected_content"]["preserved"])
        self.assertEqual(applied["claim_reaudit"]["status"], "passed")

    def test_human_rejection_is_preserved_in_the_diff(self) -> None:
        text = "Uma síntese crítica das principais recomendações atualizadas."
        report = audit_text(text)
        finding = self._finding(report, "self-importance-announcement")

        result = humanize_text(
            text,
            report,
            [
                {
                    "finding_id": finding["finding_id"],
                    "status": "confirmed",
                    "disposition": "rejected",
                    "reason": "O título é uma citação histórica que deve permanecer.",
                    "reviewed_by": "editora-humana",
                }
            ],
        )

        self.assertEqual(result["revised_text"], text)
        self.assertEqual(result["summary"]["rejected"], 1)
        self.assertEqual(result["changes"][0]["status"], "rejected")

    def test_broad_confirmation_is_blocked(self) -> None:
        labels = ("primeiro", "segundo", "terceiro", "quarto", "quinto")
        text = " ".join(f"Além disso, o ponto {label} precisa de contexto." for label in labels)
        report = audit_text(text)
        decisions = [
            {"finding_id": item["finding_id"], "status": "confirmed", "reviewed_by": "editora-humana"}
            for item in report["findings"]
            if item["category"] == "formulaic-transition"
        ]

        result = humanize_text(text, report, decisions, max_operations=2)

        self.assertEqual(result["status"], "blocked")
        self.assertEqual(result["revised_text"], text)


class AntiAiHumanizerCliTests(unittest.TestCase):
    def test_confirmed_finding_round_trips_through_both_clis(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reviews-humanizer-cli-") as temporary:
            root = Path(temporary)
            draft = root / "draft.md"
            report_path = root / "anti-ai-report.json"
            decisions_path = root / "decisions.json"
            diff_path = root / "humanization-diff.json"
            rewritten_path = root / "rewritten.md"
            write_text(draft, "Uma síntese crítica das principais recomendações atualizadas.")

            audit = subprocess.run(
                [
                    sys.executable, str(ROOT / "scripts" / "audit_anti_ai.py"),
                    "--input", str(draft), "--output", str(report_path), "--artifact-id", "cli-round-trip",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(audit.returncode, 0, audit.stderr)
            report = load_data(report_path)
            finding = next(item for item in report["findings"] if item["category"] == "self-importance-announcement")
            dump_data(decisions_path, {"decisions": [{
                "finding_id": finding["finding_id"], "status": "confirmed", "reviewed_by": "editorial-human-reviewer",
            }]})

            humanize = subprocess.run(
                [
                    sys.executable, str(ROOT / "scripts" / "humanize_ptbr.py"),
                    "--input", str(draft), "--anti-ai-report", str(report_path), "--decisions", str(decisions_path),
                    "--output", str(diff_path), "--rewritten-output", str(rewritten_path),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(humanize.returncode, 0, humanize.stderr)
            diff = load_data(diff_path)
            self.assertEqual(diff["status"], "completed")
            self.assertTrue(diff["unified_diff"])
            self.assertEqual(rewritten_path.read_text(encoding="utf-8"), "As principais recomendações atualizadas.")


class EvalFixtureTests(unittest.TestCase):
    def test_new_eval_fixtures_are_declarative_and_use_anonymized_corpus_ids(self) -> None:
        paths = sorted((ROOT / "evals" / "cases").glob("anti-ai-*.json")) + sorted(
            (ROOT / "evals" / "cases").glob("humanizer-*.json")
        )
        self.assertGreaterEqual(len(paths), 8)
        for path in paths:
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertIn("case_id", payload)
            self.assertIn("expected", payload)
            self.assertIn("source_excerpt_id", payload)
            self.assertTrue(payload["source_excerpt_id"].startswith("DRV-"))

    def test_humanizer_fixtures_execute_confirmed_and_guardrail_paths(self) -> None:
        for path in sorted((ROOT / "evals" / "cases").glob("humanizer-*.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            text = payload["input"]
            report = audit_text(text)
            config = payload["humanizer"]
            required_category = config.get("required_category", "self-importance-announcement")
            finding = next(item for item in report["findings"] if item["category"] == required_category)
            decision: dict[str, object] = {
                "finding_id": finding["finding_id"],
                "status": "confirmed" if config["decision"] in {"confirmed", "rejected"} else "candidate",
            }
            if config.get("reviewed_by"):
                decision["reviewed_by"] = config["reviewed_by"]
            if config["decision"] == "rejected":
                decision["disposition"] = "rejected"
                decision["reason"] = config["reason"]
            ledger = HumanizerTests._ledger_for(text) if config.get("requires_claim_ledger") else None
            result = humanize_text(text, report, [decision], claim_ledger=ledger)
            expected = payload["expected"]
            expected_status = "completed" if expected["humanizer_status"] == "completed-with-ledger" else expected["humanizer_status"]
            self.assertEqual(result["status"], expected_status, path.name)
            if "expected_after" in expected:
                self.assertEqual(result["revised_text"], expected["expected_after"], path.name)
            for protected in expected.get("must_preserve", []):
                self.assertIn(protected, result["revised_text"], path.name)


if __name__ == "__main__":
    unittest.main()
