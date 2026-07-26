from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from extract_evidence import validate_extraction_package
from reviews_editorial.jobs import create_job, load_job


def _package(source_id: str) -> dict[str, object]:
    base = {
        "extraction_status": "validated",
        "validated_by": "test-suite",
        "validated_at": "2026-07-25T12:00:00Z",
        "source_documents": [source_id],
    }
    return {
        "artifacts": {
            "study-overview.json": {**base, "study_id": "GUIDE-1", "design": "clinical-guideline", "primary_outcome": "conduta"},
            "population.json": {**base, "population": "adultos", "randomized": None, "analyzed": None, "groups": []},
            "interventions.json": {**base, "interventions": ["conduta"], "comparators": []},
            "outcomes.json": {**base, "outcomes": ["desfecho clínico"]},
            "results.json": {**base, "results": ["recomendação localizada"]},
            "safety.json": {**base, "safety_outcomes": ["dano considerado"]},
            "missing-information.json": {**base, "items": []},
        }
    }


class ExtractEvidenceTests(unittest.TestCase):
    def test_validated_curated_package_is_accepted(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source.md"
            source.write_text("Fonte clínica", encoding="utf-8")
            job_dir = create_job(root / "jobs", [source], topic="Teste", year=2026)
            source_id = load_job(job_dir)["source_documents"][0]["source_id"]
            report = validate_extraction_package(_package(source_id), known_source_ids={source_id})
        self.assertTrue(report["valid"], report["errors"])

    def test_blank_shell_or_foreign_source_is_rejected(self) -> None:
        report = validate_extraction_package(
            {"artifacts": {"study-overview.json": {}}},
            known_source_ids={"local:known"},
        )
        self.assertFalse(report["valid"])
        self.assertTrue(any("artefato ausente" in item or "extraction_status" in item for item in report["errors"]))


if __name__ == "__main__":
    unittest.main()
