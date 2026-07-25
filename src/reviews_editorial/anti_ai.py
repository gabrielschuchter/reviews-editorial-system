"""Linter heurístico de padrões artificiais em português brasileiro."""

from __future__ import annotations

import re
from collections import Counter
from typing import Any

REFERENCE_URL = "https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing"

PHRASES = (
    "é importante destacar",
    "vale ressaltar",
    "nesse contexto",
    "de maneira geral",
    "além disso",
    "em suma",
    "em conclusão",
    "não apenas",
    "mas também",
    "desempenha um papel crucial",
    "cenário em constante evolução",
    "evidência sugere",
)


def lint_text(text: str) -> dict[str, Any]:
    lowered = text.casefold()
    findings: list[dict[str, Any]] = []
    counts = Counter({phrase: lowered.count(phrase) for phrase in PHRASES})
    for phrase, count in counts.items():
        if count:
            severity = "warning" if count == 1 else "major"
            findings.append(
                {"rule": "formulaic-phrase", "severity": severity, "phrase": phrase, "count": count}
            )

    em_dash_count = text.count("—")
    if em_dash_count >= 4:
        findings.append({"rule": "em-dash-density", "severity": "warning", "count": em_dash_count})
    headings = len(re.findall(r"(?m)^#{1,6}\s+", text))
    bullet_lines = len(re.findall(r"(?m)^\s*[-*+]\s+", text))
    paragraphs = [item for item in re.split(r"\n\s*\n", text) if item.strip()]
    if headings > 0 and headings >= max(3, len(paragraphs) // 2):
        findings.append({"rule": "excessive-headings", "severity": "warning", "count": headings})
    if bullet_lines >= 12 and bullet_lines > len(paragraphs):
        findings.append({"rule": "list-dominant-structure", "severity": "warning", "count": bullet_lines})
    if re.search(r"(?i)\b(aqui está|como modelo de linguagem|até minha última atualização)\b", text):
        findings.append({"rule": "chatbot-address", "severity": "critical"})
    if re.search(r"(?i)\b(?:turn\d+(?:search|view)\d+|oaicite|contentReference)\b", text):
        findings.append({"rule": "tool-token-leak", "severity": "critical"})

    return {
        "linter_version": "0.1.0",
        "reference": REFERENCE_URL,
        "reference_role": "descriptive-field-guide-not-detector",
        "passed": not any(item["severity"] == "critical" for item in findings),
        "findings": findings,
        "manual_review_required": True,
        "note": (
            "Os sinais são heurísticos e podem ocorrer em escrita humana. Revise o problema subjacente: "
            "generalidade, falta de evidência, repetição, estrutura artificial ou ausência de voz editorial."
        ),
    }
