"""Gate de atribuição para recomendações em edições baseadas em diretrizes.

A política editorial do Reviews exige que a recomendação pública seja apresentada
diretamente, sem usar a instituição, o documento, o painel ou os autores como
sujeito retórico da recomendação. A instituição continua permitida em contexto,
proveniência, escopo e metodologia.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


AUDIT_VERSION = "1.0.0"
RULE_ID = "REV-STRUCT-HARD-004"

_DIRECT_VERB = re.compile(
    r"\b(?:recomenda(?:m)?|sugere(?:m)?|orienta(?:m)?|aconselha(?:m)?|"
    r"indica(?:m)?|prop[oõ]e(?:m)?|determina(?:m)?)\b",
    re.IGNORECASE,
)
_REPORTING_VERB = re.compile(r"\b(?:diz|dizem|afirma|afirmam|declara|declaram)\b", re.IGNORECASE)
_MODAL_OR_ACTION = re.compile(
    r"\b(?:recomenda-se|sugere-se|orienta-se|deve(?:m)?|deveria(?:m)?|"
    r"pode(?:m)?\s+ser\s+considerad[oa]s?|[ée]\s+recomendad[oa]s?|"
    r"[ée]\s+sugerid[oa]s?|realizar|iniciar|manter|evitar|considerar|"
    r"utilizar|usar|oferecer|encaminhar|avaliar|monitorar|não\s+adicionar|"
    r"não\s+utilizar|não\s+usar)\b",
    re.IGNORECASE,
)
_ATTRIBUTION_PREFIX = re.compile(
    r"\b(?:segundo|conforme|de\s+acordo\s+com|para)\s+"
    r"(?P<source>[^,;:.]{2,120})[,;:]\s*(?P<tail>.+)",
    re.IGNORECASE,
)
_SUBJECT_ACTION = re.compile(
    r"^\s*(?:[|>*•-]\s*)?(?:a|o|as|os)\s+(?P<source>.{2,120}?)\s+"
    r"(?P<verb>recomenda(?:m)?|sugere(?:m)?|orienta(?:m)?|aconselha(?:m)?|"
    r"indica(?:m)?|prop[oõ]e(?:m)?|determina(?:m)?|diz(?:em)?|afirma(?:m)?|"
    r"declara(?:m)?)\b(?P<tail>.*)$",
    re.IGNORECASE,
)
_RECOMMENDATION_OF_SOURCE = re.compile(
    r"\b(?:a|as)\s+recomenda[cç][aã]o(?:ões)?\s+d(?:a|o|as|os)\s+"
    r"(?P<source>[^,;:.]{2,120}?)\s+(?:[ée]|inclui(?:em)?|consiste(?:m)?|"
    r"orienta(?:m)?|prev[eê](?:m)?)\b",
    re.IGNORECASE,
)

_SOURCE_WORDS = {
    "diretriz",
    "guideline",
    "documento",
    "painel",
    "autor",
    "autores",
    "sociedade",
    "associação",
    "associacao",
    "organização",
    "organizacao",
    "organization",
    "society",
    "academy",
    "academia",
    "college",
    "colégio",
    "colegio",
    "instituto",
    "institute",
    "conselho",
    "council",
    "comissão",
    "comissao",
    "committee",
    "task force",
    "american",
    "european",
    "brasileira",
    "brasileiro",
    "mundial",
    "world",
    "international",
    "internacional",
}


def _looks_like_source(text: str) -> bool:
    compact = " ".join(text.strip().split())
    folded = compact.casefold()
    if any(word in folded for word in _SOURCE_WORDS):
        return True
    tokens = re.findall(r"\b[\wÀ-ÿ.&/-]+\b", compact)
    return any(
        len(token) >= 2
        and re.fullmatch(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9][A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9.&/-]+", token)
        for token in tokens
    )


def _sentences_with_lines(text: str) -> list[tuple[int, str]]:
    result: list[tuple[int, str]] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = " ".join(raw_line.split())
        if not line:
            continue
        parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ])", line)
        for part in parts:
            sentence = part.strip()
            if sentence:
                result.append((line_no, sentence))
    return result


def _match_sentence(sentence: str) -> tuple[str, str] | None:
    """Retornar (pattern, source) quando a frase viola a política."""

    subject = _SUBJECT_ACTION.search(sentence)
    if subject and _looks_like_source(subject.group("source")):
        verb = subject.group("verb")
        tail = subject.group("tail") or ""
        if _DIRECT_VERB.search(verb):
            return "institution-as-recommendation-subject", subject.group("source").strip()
        if _REPORTING_VERB.search(verb) and _MODAL_OR_ACTION.search(tail):
            return "institution-reporting-recommendation", subject.group("source").strip()

    attributed = _ATTRIBUTION_PREFIX.search(sentence)
    if attributed and _looks_like_source(attributed.group("source")):
        if _MODAL_OR_ACTION.search(attributed.group("tail")):
            return "attribution-prefix-before-recommendation", attributed.group("source").strip()

    recommendation_of = _RECOMMENDATION_OF_SOURCE.search(sentence)
    if recommendation_of and _looks_like_source(recommendation_of.group("source")):
        return "recommendation-owned-by-institution", recommendation_of.group("source").strip()

    return None


def audit_guideline_attribution(text: str, *, artifact_id: str = "draft") -> dict[str, Any]:
    """Bloquear atribuição institucional dentro da formulação de recomendações."""

    if not isinstance(text, str):
        raise TypeError("text deve ser uma string")

    findings: list[dict[str, Any]] = []
    for line_no, sentence in _sentences_with_lines(text):
        matched = _match_sentence(sentence)
        if matched is None:
            continue
        pattern, source = matched
        findings.append(
            {
                "finding_id": f"RGA-{len(findings) + 1:03d}",
                "rule_id": RULE_ID,
                "severity": "high",
                "status": "confirmed",
                "line": line_no,
                "pattern": pattern,
                "source_expression": source,
                "evidence": sentence,
                "issue": "A recomendação foi formulada por atribuição à instituição, ao documento, ao painel ou aos autores.",
                "required_action": (
                    "Apresentar a recomendação diretamente, preservando população, condição, ação, "
                    "força, modalidade, exceções e certeza da evidência."
                ),
                "disposition_allowed": False,
            }
        )

    source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "report_id": f"RGA-{source_hash[:12].upper()}",
        "audit_version": AUDIT_VERSION,
        "artifact_id": artifact_id,
        "artifact_sha256": source_hash,
        "policy": "recomendações de diretrizes sem atribuição institucional",
        "passed": not findings,
        "blocking": bool(findings),
        "finding_count": len(findings),
        "findings": findings,
    }
