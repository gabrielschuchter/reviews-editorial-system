"""Bloqueios editoriais rígidos do Reviews.

Este módulo implementa regras canônicas definidas pela autoridade editorial:
1. antíteses e construções equivalentes são proibidas;
2. traços e hífens são proibidos em texto corrido.

As ocorrências são bloqueantes e não admitem disposição como falso positivo.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Iterable

AUDIT_VERSION = "1.0.0"
_DASH_CHARS = "-–—−"

_DIRECT_ANTITHESIS = re.compile(
    r"\bnão\s+(?:apenas|só|somente)?[^.!?\n]{0,180}?"
    r"\b(?:mas(?:\s+sim|\s+também)?|e\s+sim)\b",
    re.IGNORECASE,
)
_CONTRASTIVE_CONNECTOR = re.compile(
    r"\b(?:mas|porém|contudo|entretanto|todavia|no entanto|ainda assim|"
    r"em contrapartida|por outro lado|ao contrário|em vez de|em lugar de)\b",
    re.IGNORECASE,
)
_CONCESSIVE_CONNECTOR = re.compile(
    r"\b(?:embora|apesar de|ainda que|mesmo que|mesmo sem|se bem que)\b",
    re.IGNORECASE,
)
_CORRECTIVE_NEGATION = re.compile(
    r"\bnão\s+(?:é|são|era|eram|foi|foram|será|serão|"
    r"se\s+resume|se\s+resumem|se\s+limita|se\s+limitam|"
    r"equivale|equivalem|implica|implicam|significa|significam|"
    r"representa|representam|constitui|constituem|"
    r"funciona\s+como|funcionam\s+como|substitui|substituem|"
    r"ocupa|ocupam|serve|servem|basta|bastam|garante|garantem|"
    r"depende|dependem|decide|decidem|resolve|resolvem|"
    r"exige|exigem)\b",
    re.IGNORECASE,
)

_URL_OR_IDENTIFIER = re.compile(
    r"https?://\S+|\bdoi:\s*\S+|\b10\.\d{4,9}/\S+|\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class _Line:
    text: str
    start: int
    end: int
    number: int
    nonblank_order: int | None


def _lines(text: str) -> list[_Line]:
    result: list[_Line] = []
    offset = 0
    nonblank_order = 0
    for number, raw in enumerate(text.splitlines(keepends=True), start=1):
        value = raw.rstrip("\r\n")
        order: int | None = None
        if value.strip():
            nonblank_order += 1
            order = nonblank_order
        result.append(_Line(value, offset, offset + len(value), number, order))
        offset += len(raw)
    if not result and text == "":
        return []
    if text and (not result or result[-1].end < len(text)):
        number = len(result) + 1
        order = nonblank_order + 1 if text[result[-1].end if result else 0 :].strip() else None
        start = result[-1].end if result else 0
        result.append(_Line(text[start:], start, len(text), number, order))
    return result


def _organizational_line(line: _Line) -> bool:
    stripped = line.text.strip()
    if not stripped:
        return True
    if line.nonblank_order == 1:
        return True
    if re.match(r"^#{1,6}\s+", stripped):
        return True
    if re.match(r"^(?:Seção\s+[IVXLCDM0-9]+\.?|Tabela\s+\d+\.?|Quadro\s+\d+\.?|Figura\s+\d+\.?|Referências|Anexo|Apêndice)\b", stripped, re.IGNORECASE):
        return True
    if re.fullmatch(r"[-:|\s]+", stripped):
        return True
    return False


def _inside_identifier(line: str, position: int) -> bool:
    return any(match.start() <= position < match.end() for match in _URL_OR_IDENTIFIER.finditer(line))


def _excerpt(text: str, start: int, end: int, limit: int = 300) -> str:
    value = " ".join(text[start:end].split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _finding(
    findings: list[dict[str, Any]],
    text: str,
    *,
    category: str,
    rule_id: str,
    start: int,
    end: int,
    line: int,
    reason: str,
    required_action: str,
) -> None:
    key = (category, start, end)
    if any((item["category"], item["location"]["start"], item["location"]["end"]) == key for item in findings):
        return
    findings.append(
        {
            "finding_id": f"RSS-{len(findings) + 1:03d}",
            "rule_id": rule_id,
            "category": category,
            "severity": "critical",
            "excerpt": _excerpt(text, start, end),
            "location": {"line": line, "start": start, "end": end},
            "reason": reason,
            "required_action": required_action,
            "disposition_allowed": False,
        }
    )


def _scan_pattern(
    findings: list[dict[str, Any]],
    text: str,
    lines: Iterable[_Line],
    pattern: re.Pattern[str],
    *,
    category: str,
    rule_id: str,
    reason: str,
    required_action: str,
) -> None:
    for line in lines:
        for match in pattern.finditer(line.text):
            _finding(
                findings,
                text,
                category=category,
                rule_id=rule_id,
                start=line.start + match.start(),
                end=line.start + match.end(),
                line=line.number,
                reason=reason,
                required_action=required_action,
            )


def audit_strict_style(text: str, *, artifact_id: str = "draft") -> dict[str, Any]:
    """Auditar as proibições rígidas e bloquear qualquer ocorrência."""

    if not isinstance(text, str):
        raise TypeError("text deve ser uma string")

    lines = _lines(text)
    findings: list[dict[str, Any]] = []

    _scan_pattern(
        findings,
        text,
        lines,
        _DIRECT_ANTITHESIS,
        category="antithesis",
        rule_id="REV-STYLE-HARD-001",
        reason="A frase constrói sentido por negação seguida de substituição ou oposição.",
        required_action="Reescrever em afirmações diretas, sem estrutura de oposição.",
    )
    _scan_pattern(
        findings,
        text,
        lines,
        _CONTRASTIVE_CONNECTOR,
        category="antithesis",
        rule_id="REV-STYLE-HARD-001",
        reason="O conector organiza a ideia por contraste retórico.",
        required_action="Separar as informações e declarar cada uma diretamente, sem contraste.",
    )
    _scan_pattern(
        findings,
        text,
        lines,
        _CONCESSIVE_CONNECTOR,
        category="antithesis",
        rule_id="REV-STYLE-HARD-001",
        reason="A construção concessiva apresenta uma ideia pela oposição com outra.",
        required_action="Reorganizar a relação em frases diretas e independentes.",
    )
    _scan_pattern(
        findings,
        text,
        lines,
        _CORRECTIVE_NEGATION,
        category="antithesis",
        rule_id="REV-STYLE-HARD-001",
        reason="A negação define o argumento por contraste com uma formulação alternativa.",
        required_action="Afirmar diretamente o conteúdo pretendido e remover a negação corretiva.",
    )

    for line in lines:
        if _organizational_line(line):
            continue
        for position, char in enumerate(line.text):
            if char not in _DASH_CHARS:
                continue
            if _inside_identifier(line.text, position):
                continue
            if char == "-" and position == len(line.text) - len(line.text.lstrip()) and line.text[position : position + 2] == "- ":
                continue
            _finding(
                findings,
                text,
                category="dash-in-running-text",
                rule_id="REV-STYLE-HARD-002",
                start=line.start + position,
                end=line.start + position + 1,
                line=line.number,
                reason="Traços e hífens são proibidos em texto corrido do Reviews.",
                required_action="Reescrever a frase com pontuação simples ou expressão por extenso.",
            )

    source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "report_id": f"RSS-{source_hash[:12].upper()}",
        "audit_version": AUDIT_VERSION,
        "artifact_id": artifact_id,
        "artifact_sha256": source_hash,
        "policy": "proibições rígidas de estilo do Reviews",
        "passed": not findings,
        "blocking": bool(findings),
        "findings": findings,
        "rules": [
            {
                "rule_id": "REV-STYLE-HARD-001",
                "description": "Proibição absoluta de antítese e estruturas equivalentes.",
            },
            {
                "rule_id": "REV-STYLE-HARD-002",
                "description": "Proibição de traço, travessão, meia risca, sinal de menos ou hífen em texto corrido.",
            },
        ],
    }
