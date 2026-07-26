"""Validation for proportionate Reviews journalistic framing."""

from __future__ import annotations

import re
from typing import Any


PROMOTIONAL_TERMS = re.compile(
    r"\b(?:revolucion[aá]ri[oa]|definitiv[oa]|transforma tudo|cura|garant[eia]|sem precedentes)\b",
    flags=re.IGNORECASE,
)


def validate_framing_memo(payload: dict[str, Any], *, claim_ids: set[str] | None = None) -> dict[str, Any]:
    """Validate traceability and counterpoint without judging the headline for the editor."""

    issues: list[str] = []
    for field in ("central_tension", "reader_decision", "headline_options", "selected_angle", "counterpoint", "evidence_boundary", "must_not_imply"):
        if payload.get(field) in (None, "", []):
            issues.append(f"{field}: ausente")
    options = payload.get("headline_options")
    if not isinstance(options, list) or not options:
        issues.append("headline_options deve conter ao menos uma opção")
        options = []
    for index, option in enumerate(options, start=1):
        prefix = f"headline_options[{index}]"
        if not isinstance(option, dict):
            issues.append(f"{prefix}: deve ser objeto")
            continue
        for field in ("headline", "why_proportionate", "source_claim_ids", "counterpoint"):
            if option.get(field) in (None, "", []):
                issues.append(f"{prefix}.{field}: ausente")
        headline = str(option.get("headline") or "")
        if len(headline.split()) > 18:
            issues.append(f"{prefix}.headline: excede 18 palavras; reduzir ou justificar no editor")
        if PROMOTIONAL_TERMS.search(headline):
            issues.append(f"{prefix}.headline: contém linguagem promocional desproporcional")
        references = option.get("source_claim_ids")
        if claim_ids is not None and isinstance(references, list):
            unknown = sorted(set(str(item) for item in references) - claim_ids)
            if unknown:
                issues.append(f"{prefix}.source_claim_ids: claims desconhecidos {unknown}")
    return {
        "valid": not issues,
        "issues": issues,
        "options_checked": len(options),
        "boundary": "A validação confere rastreabilidade e proporcionalidade declarada; a decisão editorial sobre interesse, tom e título continua humana.",
    }
