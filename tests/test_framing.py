from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.framing import validate_framing_memo


def _memo(headline: str = "Quando a recomendação muda a decisão clínica") -> dict[str, object]:
    return {
        "central_tension": "A recomendação depende da condição clínica.",
        "reader_decision": "Definir quando indicar o exame.",
        "headline_options": [{
            "headline": headline,
            "why_proportionate": "Resume a decisão sem prometer benefício além da fonte.",
            "source_claim_ids": ["CLM-1"],
            "counterpoint": "A evidência é condicional para parte da população.",
        }],
        "selected_angle": "Decisão condicionada à gravidade.",
        "counterpoint": "A evidência não elimina necessidade de avaliação individual.",
        "evidence_boundary": "Não inferir benefício fora da população estudada.",
        "must_not_imply": ["Causalidade não demonstrada"],
    }


class FramingTests(unittest.TestCase):
    def test_traced_proportionate_framing_passes(self) -> None:
        report = validate_framing_memo(_memo(), claim_ids={"CLM-1"})
        self.assertTrue(report["valid"], report["issues"])

    def test_promotional_headline_is_rejected(self) -> None:
        report = validate_framing_memo(_memo("Tratamento revolucionário cura todos os pacientes"), claim_ids={"CLM-1"})
        self.assertFalse(report["valid"])
        self.assertTrue(any("promocional" in issue for issue in report["issues"]))

    def test_unknown_claim_cannot_anchor_headline(self) -> None:
        report = validate_framing_memo(_memo(), claim_ids={"CLM-2"})
        self.assertFalse(report["valid"])
        self.assertTrue(any("desconhecidos" in issue for issue in report["issues"]))


if __name__ == "__main__":
    unittest.main()
