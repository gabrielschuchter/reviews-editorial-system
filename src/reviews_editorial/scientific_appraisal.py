"""Contracts for evidence appraisal that preserve human methodological judgment.

The validator checks whether an appraisal makes its evidence and uncertainty
auditable. It never infers risk of bias, GRADE certainty, causality or a
recommendation from prose automatically.
"""

from __future__ import annotations

from typing import Any


CLAIM_CLASSES = {"data", "result", "evidence", "inference", "hypothesis"}
ROB2_DOMAINS = {
    "randomization-process",
    "deviations-from-intended-interventions",
    "missing-outcome-data",
    "measurement-of-outcome",
    "selection-of-reported-result",
}
GRADE_DOMAINS = {
    "risk-of-bias",
    "inconsistency",
    "indirectness",
    "imprecision",
    "publication-bias",
}
REQUIRED_CROSS_CUTTING = {
    "multiplicity",
    "subgroups",
    "missing_data",
    "surrogate_outcomes",
    "causality",
    "applicability",
}


def _nonempty(value: Any) -> bool:
    return value not in (None, "", [])


def _validate_sources(value: Any, path: str, issues: list[str]) -> None:
    if not isinstance(value, list) or not value:
        issues.append(f"{path}: fontes/localizadores ausentes")
        return
    for index, source in enumerate(value, start=1):
        if not isinstance(source, dict):
            issues.append(f"{path}[{index}]: deve ser objeto")
            continue
        for field in ("document_id", "locator", "excerpt"):
            if not _nonempty(source.get(field)):
                issues.append(f"{path}[{index}].{field}: ausente")


def validate_scientific_appraisal(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate an appraisal record without pretending to make its judgments."""

    issues: list[str] = []
    for field in ("appraisal_id", "job_id", "study_id", "design", "outcome_appraisals", "cross_cutting", "human_judgment_required", "provenance"):
        if not _nonempty(payload.get(field)):
            issues.append(f"{field}: ausente")
    if payload.get("human_judgment_required") is not True:
        issues.append("human_judgment_required deve ser true")
    outcomes = payload.get("outcome_appraisals")
    if not isinstance(outcomes, list) or not outcomes:
        issues.append("outcome_appraisals deve conter ao menos um desfecho")
        outcomes = []
    for outcome_index, outcome in enumerate(outcomes, start=1):
        prefix = f"outcome_appraisals[{outcome_index}]"
        if not isinstance(outcome, dict):
            issues.append(f"{prefix}: deve ser objeto")
            continue
        for field in ("outcome_id", "outcome_name", "claim_classification", "risk_of_bias", "certainty", "clinical_relevance", "sources"):
            if not _nonempty(outcome.get(field)):
                issues.append(f"{prefix}.{field}: ausente")
        classes = outcome.get("claim_classification", [])
        if not isinstance(classes, list) or not set(classes).issubset(CLAIM_CLASSES) or not classes:
            issues.append(f"{prefix}.claim_classification: usar apenas {sorted(CLAIM_CLASSES)}")
        _validate_sources(outcome.get("sources"), f"{prefix}.sources", issues)
        risk = outcome.get("risk_of_bias")
        if not isinstance(risk, dict):
            issues.append(f"{prefix}.risk_of_bias: deve ser objeto")
        else:
            domains = risk.get("domains")
            if not isinstance(domains, list) or not domains:
                issues.append(f"{prefix}.risk_of_bias.domains: ausente")
                domains = []
            seen_domains = set()
            for domain_index, domain in enumerate(domains, start=1):
                domain_prefix = f"{prefix}.risk_of_bias.domains[{domain_index}]"
                if not isinstance(domain, dict):
                    issues.append(f"{domain_prefix}: deve ser objeto")
                    continue
                domain_name = domain.get("domain")
                seen_domains.add(domain_name)
                for field in ("domain", "judgement", "rationale", "evidence_spans"):
                    if not _nonempty(domain.get(field)):
                        issues.append(f"{domain_prefix}.{field}: ausente")
                _validate_sources(domain.get("evidence_spans"), f"{domain_prefix}.evidence_spans", issues)
            if payload.get("design") == "randomized-trial" and not ROB2_DOMAINS.issubset(seen_domains):
                issues.append(f"{prefix}: ensaio randomizado sem os cinco domínios RoB 2")
        certainty = outcome.get("certainty")
        if not isinstance(certainty, dict):
            issues.append(f"{prefix}.certainty: deve ser objeto")
        else:
            domains = certainty.get("domains")
            if not isinstance(domains, list) or not domains:
                issues.append(f"{prefix}.certainty.domains: ausente")
                domains = []
            seen_domains = set()
            for domain_index, domain in enumerate(domains, start=1):
                domain_prefix = f"{prefix}.certainty.domains[{domain_index}]"
                if not isinstance(domain, dict):
                    issues.append(f"{domain_prefix}: deve ser objeto")
                    continue
                seen_domains.add(domain.get("domain"))
                for field in ("domain", "judgement", "rationale"):
                    if not _nonempty(domain.get(field)):
                        issues.append(f"{domain_prefix}.{field}: ausente")
            if not GRADE_DOMAINS.issubset(seen_domains):
                issues.append(f"{prefix}: certeza sem os cinco domínios GRADE")
            if certainty.get("overall") not in {"high", "moderate", "low", "very-low", "not-graded"}:
                issues.append(f"{prefix}.certainty.overall: valor inválido")
        relevance = outcome.get("clinical_relevance")
        if not isinstance(relevance, dict):
            issues.append(f"{prefix}.clinical_relevance: deve ser objeto")
        elif not _nonempty(relevance.get("absolute_effect")) and not _nonempty(relevance.get("absolute_effect_missing_reason")):
            issues.append(f"{prefix}.clinical_relevance: efeito absoluto ou motivo de ausência é obrigatório")
    cross_cutting = payload.get("cross_cutting")
    if not isinstance(cross_cutting, dict):
        issues.append("cross_cutting deve ser objeto")
        cross_cutting = {}
    for key in sorted(REQUIRED_CROSS_CUTTING):
        item = cross_cutting.get(key)
        if not isinstance(item, dict):
            issues.append(f"cross_cutting.{key}: ausente")
            continue
        for field in ("status", "rationale", "sources"):
            if not _nonempty(item.get(field)):
                issues.append(f"cross_cutting.{key}.{field}: ausente")
        _validate_sources(item.get("sources"), f"cross_cutting.{key}.sources", issues)
    recommendations = payload.get("recommendation_boundaries", [])
    if not isinstance(recommendations, list):
        issues.append("recommendation_boundaries deve ser lista")
    else:
        for index, item in enumerate(recommendations, start=1):
            prefix = f"recommendation_boundaries[{index}]"
            if not isinstance(item, dict):
                issues.append(f"{prefix}: deve ser objeto")
                continue
            for field in ("recommendation_text", "strength", "conditions", "certainty_relation", "source_claim_ids"):
                if not _nonempty(item.get(field)):
                    issues.append(f"{prefix}.{field}: ausente")
    return {
        "valid": not issues,
        "issues": issues,
        "outcomes_checked": len(outcomes),
        "decision_boundary": "O relatório é estrutural; julgamentos de risco de viés, certeza, relevância e recomendação permanecem humanos e documentados.",
    }
