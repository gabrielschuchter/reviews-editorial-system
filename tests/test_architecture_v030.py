from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.assurance import (
    EDITORIAL_BRIEF_FIELDS,
    audit_inference_text,
    scan_skill_tree,
    validate_audit_report,
    validate_editorial_brief,
    validate_source_roles,
    validate_table_rows,
)


class ModularArchitectureTests(unittest.TestCase):
    def test_editorial_brief_requires_every_decision_field(self) -> None:
        payload = {field: "registrado" for field in EDITORIAL_BRIEF_FIELDS}
        payload["must_include"] = ["CLM-1"]
        payload["must_not_claim"] = ["causalidade"]
        self.assertTrue(validate_editorial_brief(payload)["valid"])
        payload.pop("nut_graf")
        self.assertFalse(validate_editorial_brief(payload)["valid"])

    def test_source_roles_preserve_authority_rank(self) -> None:
        result = validate_source_roles({"sources": [{"source_id": "DOC-1", "source_role": "primary-evidence", "authority_rank": 1, "location": "p. 2", "rationale": "artigo"}]})
        self.assertTrue(result["valid"], result["issues"])

    def test_inference_linter_blocks_surrogate_overclaim(self) -> None:
        result = audit_inference_text("A redução da HbA1c demonstrou benefício clínico global.")
        self.assertFalse(result["passed"])
        self.assertEqual(result["findings"][0]["rule"], "surrogate-clinical-overclaim")

    def test_table_rows_cannot_hide_context_in_header(self) -> None:
        result = validate_table_rows([{ "recommendation": "Realizar colonoscopia.", "population": "adultos", "condition": "sangramento baixo estável", "action": "realizar durante internação" }])
        self.assertTrue(result["passed"])

    def test_audit_report_requires_evidence_for_each_finding(self) -> None:
        report = {"audit_id": "AUD-1", "job_id": "JOB-2026-001", "mode": "numbers", "coverage": "complete", "provenance": "test", "findings": [{"id": "F-1", "mode": "numbers", "severity": "major", "confidence": "high", "status": "confirmed", "evidence": "Tabela 2", "issue": "unidade", "why_it_matters": "muda a leitura", "recommended_fix": "corrigir"}]}
        self.assertTrue(validate_audit_report(report)["valid"])

    def test_skill_scanner_accepts_repository_skills(self) -> None:
        result = scan_skill_tree(ROOT / ".codex" / "skills")
        self.assertTrue(result["passed"], result["findings"])


if __name__ == "__main__":
    unittest.main()
