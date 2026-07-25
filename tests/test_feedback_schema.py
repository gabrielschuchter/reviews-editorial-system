from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.feedback import validate_feedback
from reviews_editorial.io import load_data
from reviews_editorial.schema_validation import validate


class FeedbackContractTests(unittest.TestCase):
    def _valid_payload(self) -> dict:
        return {
            "feedback_id": "FDB-0001",
            "job_id": "JOB-2026-001",
            "edition_id": "EDITION-test",
            "candidate_version": "v1",
            "revised_version": "v2",
            "section": "Resultados",
            "feedback_type": "style-correction",
            "original": "Antes.",
            "edited": "Depois.",
            "difference": "Substituição textual.",
            "reason": "Maior clareza.",
            "generalizable": False,
            "generalization_status": "local-only",
            "candidate_rule": None,
            "target_destination": None,
            "regression_test": None,
            "editor_approval": {
                "decision": "pending",
                "editor": None,
                "decided_at": None,
            },
            "sources": [
                {
                    "version_role": "candidate",
                    "location": "drafts/v1.md",
                    "hash": "a" * 64,
                },
                {
                    "version_role": "revised",
                    "location": "drafts/v2.md",
                    "hash": "b" * 64,
                },
            ],
            "provenance": {
                "compared_at": "2026-07-25T12:00:00Z",
                "compared_by": "test",
                "method": "line-diff",
                "notes": None,
            },
        }

    def test_feedback_schema_enforces_both_version_roles(self) -> None:
        schema = load_data(ROOT / "schemas" / "feedback.schema.json")
        payload = self._valid_payload()
        self.assertEqual(validate(payload, schema), [])
        payload["sources"][1]["version_role"] = "candidate"
        self.assertTrue(validate(payload, schema))

    def test_general_rule_requires_real_passing_regression(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "rule.md").write_text("regra", encoding="utf-8")
            result = validate_feedback(
                [
                    {
                        "feedback_id": "FDB-1",
                        "feedback_type": "candidate-general-rule",
                        "generalizable": True,
                        "reason": "Erro recorrente.",
                        "candidate_rule": "Evitar o erro.",
                        "target_rule_file": "rule.md",
                        "regression_test": {
                            "test_id": "REG-1",
                            "location": "missing.json",
                            "passed_existing_cases": False,
                        },
                        "approval_status": "approved-by-editor",
                    }
                ],
                repository_root=root,
            )
            self.assertFalse(result["valid"])
            self.assertEqual(result["approved_rule_proposals"], [])


if __name__ == "__main__":
    unittest.main()
