from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.io import load_data
from reviews_editorial.schema_validation import validate
from reviews_editorial.strict_style import audit_strict_style


class StrictStyleAuditTests(unittest.TestCase):
    def categories(self, text: str) -> list[str]:
        return [item["category"] for item in audit_strict_style(text)["findings"]]

    def test_direct_antithesis_is_blocking(self) -> None:
        text = "O resultado não é definitivo, mas orienta a decisão."
        report = audit_strict_style(text)
        self.assertFalse(report["passed"])
        self.assertTrue(report["blocking"])
        self.assertIn("antithesis", self.categories(text))

    def test_corrective_negation_is_blocking_without_connector(self) -> None:
        report = audit_strict_style(
            "A avaliação não se resume ao peso. Ela inclui sintomas e função muscular."
        )
        self.assertFalse(report["passed"])
        finding = next(
            item for item in report["findings"] if item["category"] == "antithesis"
        )
        self.assertEqual(finding["rule_id"], "REV-STYLE-HARD-001")
        self.assertFalse(finding["disposition_allowed"])

    def test_concessive_structure_is_blocking(self) -> None:
        report = audit_strict_style(
            "Apesar da certeza baixa, o painel emitiu recomendação forte."
        )
        self.assertFalse(report["passed"])
        self.assertIn(
            "antithesis",
            {item["category"] for item in report["findings"]},
        )

    def test_direct_clinical_negative_recommendation_is_allowed(self) -> None:
        report = audit_strict_style(
            "Não adicionar glutamina parenteral à terapia nutricional."
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["findings"], [])

    def test_direct_factual_negative_is_allowed(self) -> None:
        report = audit_strict_style(
            "Não foram encontrados estudos elegíveis para esta pergunta."
        )
        self.assertTrue(report["passed"])
        self.assertEqual(report["findings"], [])

    def test_dash_and_hyphen_in_running_text_are_blocking(self) -> None:
        report = audit_strict_style(
            "O acompanhamento ocorre no pós-operatório por 4–6 semanas."
        )
        findings = [
            item
            for item in report["findings"]
            if item["category"] == "dash-in-running-text"
        ]
        self.assertGreaterEqual(len(findings), 2)
        self.assertFalse(report["passed"])

    def test_organizational_heading_may_contain_dash(self) -> None:
        report = audit_strict_style(
            "# Seção clínica — acompanhamento\n\nO acompanhamento ocorre por seis semanas."
        )
        self.assertTrue(report["passed"])

    def test_report_validates_against_schema(self) -> None:
        report = audit_strict_style("A frase usa contraste, porém permanece direta.")
        schema = load_data(ROOT / "schemas" / "strict-style-report.schema.json")
        self.assertEqual(validate(report, schema), [])


class StrictStyleCliTests(unittest.TestCase):
    def test_cli_returns_nonzero_for_blocking_occurrence(self) -> None:
        with tempfile.TemporaryDirectory(prefix="reviews-strict-style-") as temporary:
            root = Path(temporary)
            draft = root / "draft.md"
            output = root / "strict-style-report.json"
            draft.write_text(
                "O valor não é fixo, mas serve como referência.",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "audit_strict_style.py"),
                    "--input",
                    str(draft),
                    "--output",
                    str(output),
                    "--artifact-id",
                    "strict-cli",
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
