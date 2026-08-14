from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.guideline_attribution import audit_guideline_attribution
from reviews_editorial.io import load_data
from reviews_editorial.schema_validation import validate


DIRECT = """# Diretriz clínica

Introdução

Publicada em 2026, a diretriz da ASPEN aborda o cuidado nutricional de adultos. A ASPEN utilizou GRADE e consenso Delphi na elaboração.

Resumo das recomendações

Recomenda-se triagem nutricional na primeira apresentação e ao longo do tratamento.

Pode ser considerada gastrostomia quando a duração esperada do suporte justificar essa via.

Não adicionar glutamina parenteral até que novas pesquisas confirmem sua segurança.
"""


class GuidelineAttributionTests(unittest.TestCase):
    def test_direct_recommendations_pass(self) -> None:
        report = audit_guideline_attribution(DIRECT)
        self.assertTrue(report["passed"], report["findings"])
        self.assertEqual(report["finding_count"], 0)

    def test_institution_as_subject_is_blocked(self) -> None:
        report = audit_guideline_attribution("A ASPEN recomenda triagem nutricional na primeira consulta.")
        self.assertFalse(report["passed"])
        self.assertEqual(report["findings"][0]["pattern"], "institution-as-recommendation-subject")

    def test_document_and_authors_as_subject_are_blocked(self) -> None:
        for sentence in (
            "A diretriz recomenda consulta semanal com nutricionista.",
            "O documento orienta manter acompanhamento durante a recuperação.",
            "Os autores sugerem iniciar suporte nutricional em até 24 horas.",
            "O painel recomenda avaliação nutricional abrangente.",
        ):
            with self.subTest(sentence=sentence):
                self.assertFalse(audit_guideline_attribution(sentence)["passed"])

    def test_attribution_prefix_before_recommendation_is_blocked(self) -> None:
        for sentence in (
            "Segundo a ACG, recomenda-se colonoscopia após estabilização.",
            "De acordo com a ESC, o tratamento deve ser iniciado após confirmação diagnóstica.",
            "Conforme a APA, deve-se integrar pesquisa, expertise clínica e preferências.",
        ):
            with self.subTest(sentence=sentence):
                report = audit_guideline_attribution(sentence)
                self.assertFalse(report["passed"])
                self.assertEqual(
                    report["findings"][0]["pattern"],
                    "attribution-prefix-before-recommendation",
                )

    def test_reporting_verb_with_recommendation_is_blocked(self) -> None:
        report = audit_guideline_attribution("A ASPEN diz que pacientes devem ser triados regularmente.")
        self.assertFalse(report["passed"])
        self.assertEqual(report["findings"][0]["pattern"], "institution-reporting-recommendation")

    def test_recommendation_owned_by_institution_is_blocked(self) -> None:
        report = audit_guideline_attribution("A recomendação da ASPEN é realizar consulta semanal durante a radioterapia.")
        self.assertFalse(report["passed"])
        self.assertEqual(report["findings"][0]["pattern"], "recommendation-owned-by-institution")

    def test_contextual_institution_mentions_are_allowed(self) -> None:
        for sentence in (
            "Publicada em 2026, a diretriz da ASPEN se aplica a adultos em tratamento oncológico.",
            "A ASPEN utilizou GRADE e consenso Delphi na elaboração da diretriz.",
            "A ACG publicou a atualização em 2023.",
            "Tabela 1. Recomendações formais da ASPEN para o cuidado nutricional.",
            "Segundo a ASPEN, a busca incluiu ensaios randomizados e estudos quase experimentais.",
        ):
            with self.subTest(sentence=sentence):
                self.assertTrue(audit_guideline_attribution(sentence)["passed"])

    def test_report_validates_against_schema(self) -> None:
        report = audit_guideline_attribution("A ASPEN recomenda triagem nutricional.")
        schema = load_data(ROOT / "schemas" / "guideline-attribution-report.schema.json")
        self.assertEqual(validate(report, schema), [])


class GuidelineAttributionCliTests(unittest.TestCase):
    def test_cli_blocks_attributed_recommendation(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reviews-guideline-attribution-") as temporary:
            root = Path(temporary)
            draft = root / "draft.md"
            output = root / "audit.json"
            draft.write_text("A ASPEN recomenda triagem nutricional.", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "audit_guideline_attribution.py"),
                    "--input",
                    str(draft),
                    "--output",
                    str(output),
                    "--artifact-id",
                    "fixture",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertFalse(load_data(output)["passed"])


if __name__ == "__main__":
    unittest.main()
