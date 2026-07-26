from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from reviews_editorial.orchestrator import run_preflight, select_capabilities
from reviews_editorial.skill_validation import REQUIRED_SKILLS, validate_skill_tree
from run_skill_evals import evaluate_declarative_manifests


class OrchestrationTests(unittest.TestCase):
    def test_full_request_starts_with_orchestrator_and_chains_all_capabilities(self) -> None:
        report = select_capabilities({"stage": "full"})
        names = [item["skill"] for item in report["selected_capabilities"]]
        self.assertEqual(names[0], "reviews-writer")
        self.assertEqual(set(names), set(REQUIRED_SKILLS))
        self.assertLess(names.index("reviews-source-provenance"), names.index("reviews-edition-writing"))
        self.assertLess(names.index("reviews-edition-writing"), names.index("reviews-audit"))

    def test_preflight_rejects_incomplete_brief_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            brief = Path(temporary) / "brief.json"
            brief.write_text(json.dumps({"edition_type": "guideline-summary"}), encoding="utf-8")
            report = run_preflight({"stage": "planning", "editorial_brief": str(brief)})
        self.assertFalse(report["preflight_passed"])
        self.assertIn("editorial brief incompleto", report["blocked_reasons"])

    def test_unknown_stage_is_not_silently_routed(self) -> None:
        with self.assertRaisesRegex(ValueError, "stage desconhecido"):
            select_capabilities({"stage": "redigir-sem-evidencia"})


class SkillAndCliContractTests(unittest.TestCase):
    def test_all_required_skill_bundles_pass_deep_validation(self) -> None:
        report = validate_skill_tree(ROOT / ".codex" / "skills")
        self.assertTrue(report["valid"], json.dumps(report, ensure_ascii=False, indent=2))

    def test_declarative_skill_manifests_are_executed_as_contract_checks(self) -> None:
        report = evaluate_declarative_manifests(ROOT / ".codex" / "skills", repo_root=ROOT)
        self.assertTrue(report["passed"], json.dumps(report, ensure_ascii=False, indent=2))
        self.assertEqual(report["mode"], "deterministic-manifest-contract")
        self.assertFalse(report["llm_execution"])
        self.assertEqual(report["manifest_count"], len(REQUIRED_SKILLS))
        self.assertEqual(report["total_cases"], 44)
        self.assertEqual(report["passed_cases"], 44)
        self.assertTrue(all(skill["contract_paths"] for skill in report["skills"]))
        self.assertTrue(all(case["contract_paths"] for skill in report["skills"] for case in skill["cases"]))

    def test_cited_validation_clis_bootstrap_the_package(self) -> None:
        for script in (
            "validate_artifact.py",
            "validate_tables.py",
            "orchestrate_reviews.py",
            "validate_skills.py",
            "run_integration_smoke.py",
        ):
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts" / script), "--help"],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(completed.returncode, 0, f"{script}: {completed.stderr}")


if __name__ == "__main__":
    unittest.main()
