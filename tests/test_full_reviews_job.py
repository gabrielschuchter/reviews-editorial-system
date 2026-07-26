from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.integration_smoke import run_full_job


class FullReviewsJobTests(unittest.TestCase):
    def test_complete_fixture_reaches_human_review_gate_without_autoapproval(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reviews-full-job-") as temporary:
            report = run_full_job(Path(temporary))
        self.assertTrue(report["passed"])
        self.assertEqual(report["state"], "candidate_for_review")
        self.assertEqual(report["status"], "AGUARDANDO REVISÃO EDITORIAL")
        self.assertEqual(report["humanizer"], {"status": "completed", "changes": 1, "diff": True})
        self.assertEqual(len(report["skills_routed"]), 11)
        self.assertIn("candidate_for_review", report["states_completed"])


if __name__ == "__main__":
    unittest.main()
