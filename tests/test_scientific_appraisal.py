from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.scientific_appraisal import validate_scientific_appraisal


def _source() -> dict[str, str]:
    return {"document_id": "DOC-1", "locator": "p. 4, Table 2", "excerpt": "Texto localizado"}


def _valid_payload() -> dict[str, object]:
    rob_domains = [
        {"domain": name, "judgement": "low", "rationale": "Julgamento documentado", "evidence_spans": [_source()]}
        for name in (
            "randomization-process",
            "deviations-from-intended-interventions",
            "missing-outcome-data",
            "measurement-of-outcome",
            "selection-of-reported-result",
        )
    ]
    grade_domains = [
        {"domain": name, "judgement": "not-serious", "rationale": "Julgamento documentado"}
        for name in ("risk-of-bias", "inconsistency", "indirectness", "imprecision", "publication-bias")
    ]
    cross = {
        name: {"status": "addressed", "rationale": "Verificado", "sources": [_source()]}
        for name in ("multiplicity", "subgroups", "missing_data", "surrogate_outcomes", "causality", "applicability")
    }
    return {
        "appraisal_id": "APP-1",
        "job_id": "JOB-2026-001",
        "study_id": "STUDY-1",
        "design": "randomized-trial",
        "outcome_appraisals": [{
            "outcome_id": "OUT-1",
            "outcome_name": "Desfecho clínico",
            "claim_classification": ["data", "result", "evidence", "inference"],
            "risk_of_bias": {"domains": rob_domains},
            "certainty": {"overall": "moderate", "domains": grade_domains},
            "clinical_relevance": {"absolute_effect": "2 eventos a menos por 100 pessoas"},
            "sources": [_source()],
        }],
        "cross_cutting": cross,
        "recommendation_boundaries": [{
            "recommendation_text": "Considerar no grupo definido.",
            "strength": "conditional",
            "conditions": "Somente população estudada.",
            "certainty_relation": "Certeza moderada para o desfecho.",
            "source_claim_ids": ["CLM-1"],
        }],
        "human_judgment_required": True,
        "provenance": {"reviewer": "editor"},
    }


class ScientificAppraisalTests(unittest.TestCase):
    def test_complete_outcome_level_appraisal_is_valid(self) -> None:
        report = validate_scientific_appraisal(_valid_payload())
        self.assertTrue(report["valid"], report["issues"])

    def test_randomized_trial_without_all_rob2_domains_is_rejected(self) -> None:
        payload = _valid_payload()
        payload["outcome_appraisals"][0]["risk_of_bias"]["domains"].pop()
        report = validate_scientific_appraisal(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("cinco domínios RoB 2" in issue for issue in report["issues"]))

    def test_unexplained_missing_absolute_effect_is_rejected(self) -> None:
        payload = _valid_payload()
        payload["outcome_appraisals"][0]["clinical_relevance"] = {}
        report = validate_scientific_appraisal(payload)
        self.assertFalse(report["valid"])
        self.assertTrue(any("efeito absoluto" in issue for issue in report["issues"]))


if __name__ == "__main__":
    unittest.main()
