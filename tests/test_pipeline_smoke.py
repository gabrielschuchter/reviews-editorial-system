from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.documents import normalize_job_documents
from reviews_editorial.io import dump_data, load_data
from reviews_editorial.jobs import confirm_document_validation, create_job
from reviews_editorial.pipeline import advance_job, validate_pipeline


class PipelineSmokeTests(unittest.TestCase):
    def test_job_advances_through_normalized_package_after_manual_review(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.md"
            source.write_text(
                "# Documento sintético\n\nSem conteúdo científico para publicação.",
                encoding="utf-8",
            )
            job_dir = create_job(root / "jobs", [source], topic="Smoke test", year=2026)
            normalize_job_documents(job_dir, [str(source)])

            review_path = job_dir / "normalized" / "manual-document-review.json"
            review = load_data(review_path)
            for check in review["checks"].values():
                check["confirmed"] = True
                check["notes"] = "Confirmado no pacote sintético do teste."
            dump_data(review_path, review)
            confirm_document_validation(job_dir, "test-suite")

            advance_job(job_dir, "documents_validated", actor="test-suite")
            advance_job(job_dir, "document_package_normalized", actor="test-suite")

            job = load_data(job_dir / "job.yml")
            report = validate_pipeline(job_dir)
            self.assertEqual(job["state"], "document_package_normalized")
            self.assertTrue(report["valid"], report["errors"])
            self.assertEqual(
                [entry["state"] for entry in job["history"]],
                [
                    "received",
                    "documents_validated",
                    "document_package_normalized",
                ],
            )


if __name__ == "__main__":
    unittest.main()
