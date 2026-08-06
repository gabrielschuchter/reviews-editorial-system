from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.guideline_intro import audit_guideline_introduction
from reviews_editorial.io import load_data
from reviews_editorial.schema_validation import validate


DEFECTIVE = """# Nutrição em câncer

Introdução

Em câncer de cabeça e pescoço, o risco nutricional muda ao longo do cuidado. Tumor e tratamento afetam ingestão e deglutição.

A diretriz da ASPEN, publicada em 2026, incluiu 92 estudos. A busca cobriu publicações desde 2001 e usou GRADE e Delphi.

A diretriz separa força da recomendação e certeza da evidência. O painel formulou recomendações para profissionais.

Resumo das recomendações
"""

CONTEXTUAL = """# Nutrição em câncer

Introdução

Os cânceres de cabeça e pescoço formam um grupo de tumores da cavidade oral, laringe, faringe e outras estruturas. Em 2021, ocuparam a sétima posição entre os cânceres mais frequentes no mundo, com centenas de milhares de diagnósticos e mortes.

A relação com a nutrição é estreita. Tumor, cirurgia, radioterapia e terapia sistêmica podem comprometer mastigação, deglutição, salivação, paladar e apetite, com redução da ingestão de energia e proteína.

A desnutrição e a perda de massa muscular estão associadas a complicações, pior cicatrização, internações mais longas, pior qualidade de vida e dificuldade para concluir o tratamento.

O cuidado reúne decisões sobre triagem, avaliação, metas nutricionais, alimentação oral, nutrição enteral e atuação interdisciplinar. Essa complexidade sustenta a necessidade de uma orientação específica.

Publicada em 2026, a diretriz da ASPEN orienta o cuidado nutricional de adultos e concentra suas recomendações em estudos específicos de câncer de cabeça e pescoço. Esta edição examina recomendações, certeza e implicações práticas.

Resumo das recomendações
"""


class GuidelineIntroductionTests(unittest.TestCase):
    def test_defective_method_heavy_introduction_is_blocked(self) -> None:
        report = audit_guideline_introduction(DEFECTIVE)
        self.assertFalse(report["passed"])
        self.assertGreater(len(report["findings"]), 0)
        self.assertLess(report["introduction"]["context_paragraphs_before_guideline"], 2)
        self.assertGreater(report["introduction"]["guideline_or_method_share"], 0.25)

    def test_contextual_introduction_passes(self) -> None:
        report = audit_guideline_introduction(CONTEXTUAL)
        self.assertTrue(report["passed"], report["findings"])
        self.assertEqual(report["findings"], [])
        self.assertGreaterEqual(report["introduction"]["context_paragraphs_before_guideline"], 2)
        self.assertLessEqual(report["introduction"]["guideline_or_method_share"], 0.25)
        self.assertTrue(all(report["introduction"]["coverage"].values()))

    def test_missing_epidemiology_is_blocking(self) -> None:
        text = CONTEXTUAL.replace(
            "Em 2021, ocuparam a sétima posição entre os cânceres mais frequentes no mundo, com centenas de milhares de diagnósticos e mortes.",
            "A população apresenta tumores em diferentes estruturas anatômicas.",
        )
        report = audit_guideline_introduction(text)
        self.assertFalse(report["passed"])
        self.assertFalse(report["introduction"]["coverage"]["epidemiology_or_burden"])

    def test_multiple_method_paragraphs_are_blocking(self) -> None:
        text = CONTEXTUAL.replace(
            "Publicada em 2026, a diretriz da ASPEN orienta o cuidado nutricional de adultos e concentra suas recomendações em estudos específicos de câncer de cabeça e pescoço. Esta edição examina recomendações, certeza e implicações práticas.",
            "Publicada em 2026, a diretriz da ASPEN orienta o cuidado nutricional de adultos.\n\nA busca usou PubMed, EMBASE, GRADE e consenso Delphi para formular recomendações.",
        )
        report = audit_guideline_introduction(text)
        self.assertFalse(report["passed"])
        self.assertGreater(len(report["introduction"]["guideline_or_method_paragraphs"]), 1)

    def test_report_validates_against_schema(self) -> None:
        report = audit_guideline_introduction(CONTEXTUAL)
        schema = load_data(ROOT / "schemas" / "guideline-introduction-report.schema.json")
        self.assertEqual(validate(report, schema), [])


class GuidelineIntroductionCliTests(unittest.TestCase):
    def test_cli_blocks_defective_introduction(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reviews-guideline-intro-") as temporary:
            root = Path(temporary)
            draft = root / "draft.md"
            output = root / "audit.json"
            draft.write_text(DEFECTIVE, encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "audit_guideline_intro.py"),
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
