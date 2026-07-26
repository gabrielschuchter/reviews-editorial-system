from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.provenance import validate_claim_provenance


def _claim(source: str = "DOC-1") -> dict[str, object]:
    return {
        "claim_id": "CLM-1",
        "claim_text": "O risco absoluto caiu 2 por 100.",
        "claim_type": "result",
        "source_document": source,
        "source_excerpt": "Absolute risk difference: -2 per 100.",
        "page": 3,
        "table": "Table 2",
        "figure": None,
        "section": "Results",
        "verification_status": "verified",
        "allowed_in_public_draft": True,
        "provenance": {
            "extracted_at": "2026-07-25T12:00:00Z",
            "extracted_by": "test-suite",
            "method": "manual-double-check",
            "source_hash": "0" * 64,
        },
    }


class ProvenanceTests(unittest.TestCase):
    def test_public_claim_is_traceable_to_registered_primary_source(self) -> None:
        report = validate_claim_provenance(
            {"claims": [_claim()]},
            {"sources": [{"source_id": "DOC-1", "source_role": "primary-evidence", "authority_rank": 1, "location": "p. 3", "rationale": "artigo"}]},
        )
        self.assertTrue(report["valid"], report["issues"])

    def test_public_claim_with_unregistered_source_is_rejected(self) -> None:
        report = validate_claim_provenance(
            {"claims": [_claim("DOC-unknown")]},
            {"sources": [{"source_id": "DOC-1", "source_role": "primary-evidence", "authority_rank": 1, "location": "p. 3", "rationale": "artigo"}]},
        )
        self.assertFalse(report["valid"])
        self.assertTrue(any("não está registrada" in issue["message"] for issue in report["issues"]))


if __name__ == "__main__":
    unittest.main()
