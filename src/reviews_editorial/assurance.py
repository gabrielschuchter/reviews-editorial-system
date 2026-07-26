"""Validadores determinísticos para a arquitetura editorial modular.

Estes verificadores não fazem julgamento científico autônomo. Eles identificam
invariantes, padrões que exigem revisão e contratos incompletos.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


EDITORIAL_BRIEF_FIELDS = (
    "edition_type", "primary_source", "central_question", "reader",
    "clinical_or_intellectual_decision", "editorial_angle", "why_now",
    "what_changed", "central_tension", "strongest_supported_takeaway",
    "most_important_uncertainty", "must_include", "must_not_claim",
    "context_needed", "numbers_that_need_context", "counterevidence_or_disagreement",
    "source_incentives_or_conflicts", "omissions_to_avoid", "headline_constraints",
    "lead_strategy", "nut_graf", "ending_function",
)

SOURCE_ROLES = {
    "primary-evidence", "method-authority", "editorial-authority", "human-correction",
    "exemplar-structure", "exemplar-style", "external-scrutiny", "context-only",
    "tooling-reference", "excluded",
}

_INFERENCE_RULES = (
    ("surrogate-clinical-overclaim",
     r"\b(hba1c|biomarcador|escore|massa gorda|imagem|medida fisiol[oó]gica)\b.*\b(benef[ií]cio cl[ií]nico|melhora (?:global|funcional)|reduz(?:iu|ir)? (?:morbidade|mortalidade))\b"),
    ("association-causality-overclaim",
     r"\b(associa(?:ç|c)[aã]o|associad[ao])\b.*\b(causou|provou|determinou|leva a|reduz(?:iu|ir)?)\b"),
    ("significance-clinical-relevance-overclaim",
     r"\b(estatisticamente significativ[oa]|p\s*[<≤])\b.*\b(clinicamente (?:relevante|importante)|benef[ií]cio cl[ií]nico)\b"),
    ("absence-is-equivalence",
     r"\b(p\s*>\s*0[,.]0?5|n[aã]o (?:houve|foi observada) diferen[çc]a)\b.*\b(equivalen|sem efeito|n[aã]o funciona)\b"),
    ("subgroup-generalization",
     r"\b(subgrupo|entre os pacientes com)\b.*\b(efeito geral|funciona para todos|benef[ií]cio geral)\b"),
    ("imprecise-interval-overclaim",
     r"\b(intervalo de confian[çc]a|ic\s*95)\b.*\b(sem efeito|aus[eê]ncia de efeito)\b"),
)


def audit_inference_text(text: str) -> dict[str, Any]:
    """Sinalizar saltos inferenciais; cada achado exige leitura humana."""

    normalized = " ".join(text.casefold().split())
    findings = []
    for rule, pattern in _INFERENCE_RULES:
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            findings.append({
                "rule": rule,
                "severity": "critical",
                "status": "suspected",
                "message": "Padrão textual exige conferência contra o claim ledger e a fonte.",
            })
    return {
        "audit_version": "0.3.0",
        "mode": "claim-calibration",
        "passed": not findings,
        "findings": findings,
        "manual_review_required": bool(findings),
        "note": "O linter não decide causalidade, relevância ou certeza; ele bloqueia a alegação até a revisão humana documentada.",
    }


def validate_table_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Exigir recomendações autossuficientes quando uma tabela declara conduta."""

    findings = []
    for index, row in enumerate(rows, start=1):
        recommendation = str(row.get("recommendation") or "").strip()
        population = str(row.get("population") or "").strip()
        condition = str(row.get("condition") or "").strip()
        action = str(row.get("action") or "").strip()
        if not recommendation or not population or not condition or not action:
            findings.append({
                "rule": "table-row-not-self-contained",
                "severity": "critical",
                "row": index,
                "message": "A linha deve declarar população, condição e ação; não pode depender do cabeçalho para preservar exceções.",
            })
    return {"passed": not findings, "findings": findings, "rows_checked": len(rows)}


def validate_editorial_brief(payload: dict[str, Any]) -> dict[str, Any]:
    missing = [field for field in EDITORIAL_BRIEF_FIELDS if field not in payload]
    empty = [field for field in EDITORIAL_BRIEF_FIELDS if field in payload and payload[field] in (None, "", [])]
    return {
        "valid": not missing and not empty,
        "missing_fields": missing,
        "empty_fields": empty,
        "required_fields": list(EDITORIAL_BRIEF_FIELDS),
    }


def validate_source_roles(payload: dict[str, Any]) -> dict[str, Any]:
    records = payload.get("sources") if isinstance(payload, dict) else None
    issues = []
    if not isinstance(records, list) or not records:
        return {"valid": False, "issues": ["sources deve conter ao menos um registro"]}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            issues.append(f"sources[{index}] não é objeto")
            continue
        for field in ("source_id", "source_role", "authority_rank", "location", "rationale"):
            if record.get(field) in (None, ""):
                issues.append(f"sources[{index}].{field} ausente")
        if record.get("source_role") not in SOURCE_ROLES:
            issues.append(f"sources[{index}].source_role inválido")
        rank = record.get("authority_rank")
        if not isinstance(rank, int) or not 1 <= rank <= 9:
            issues.append(f"sources[{index}].authority_rank deve estar entre 1 e 9")
    return {"valid": not issues, "issues": issues, "records_checked": len(records)}


def validate_audit_report(payload: dict[str, Any]) -> dict[str, Any]:
    required = ("audit_id", "job_id", "mode", "findings", "coverage", "provenance")
    issues = [f"{field} ausente" for field in required if payload.get(field) in (None, "")]
    findings = payload.get("findings")
    if not isinstance(findings, list):
        issues.append("findings deve ser lista")
        findings = []
    finding_fields = ("id", "mode", "severity", "confidence", "status", "evidence", "issue", "why_it_matters", "recommended_fix")
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            issues.append(f"findings[{index}] não é objeto")
            continue
        for field in finding_fields:
            if finding.get(field) in (None, ""):
                issues.append(f"findings[{index}].{field} ausente")
        if finding.get("status") not in {"confirmed", "suspected", "unresolved"}:
            issues.append(f"findings[{index}].status inválido")
    return {"valid": not issues, "issues": issues, "findings_checked": len(findings)}


def scan_skill_tree(skills_root: str | Path) -> dict[str, Any]:
    """Inspect instructions and bundled code for high-risk behavior.

    This local scanner is a deterministic, defence-in-depth equivalent to a
    third-party skill scanner. It rejects hazardous content; a clean result is
    not a certification of safety and does not replace human review.
    """

    patterns = {
        "prompt-injection": (
            r"\b(?:ignore|disregard|override|bypass)\b.{0,100}\b(?:previous|prior|system|developer)\b.{0,100}\b(?:instruction|prompt|rule)\b",
            "critical",
        ),
        "secret-exfiltration": (
            r"\b(?:print|echo|upload|send|post|exfiltrat\w*)\b.{0,100}\b(?:api[_ -]?key|access[_ -]?token|secret|password|credential)\b",
            "critical",
        ),
        "unsafe-pipe": (
            r"\b(?:curl|wget|invoke-webrequest|irm)\b.{0,160}\|\s*(?:sh|bash|zsh|powershell|iex)\b",
            "critical",
        ),
        "remote-code-execution": (
            r"\b(?:invoke-expression|iex)\s*\(?\s*(?:\$\(|&\s*\(?\s*invoke-webrequest|irm)\b",
            "critical",
        ),
        "credential-file-read": (
            r"\b(?:cat|type|get-content|readfile)\b.{0,100}(?:\.env(?:\.|\b)|id_rsa|credentials\.json|\.aws[/\\]credentials)",
            "major",
        ),
        "destructive-unscoped-command": (
            r"\b(?:rm\s+-rf|remove-item)\b.{0,120}(?:\$home|~|\*|/)(?:\s|$)",
            "critical",
        ),
    }
    root = Path(skills_root)
    paths = [
        path for path in sorted(root.rglob("*"))
        if path.is_file() and path.suffix.casefold() in {".md", ".py", ".sh", ".ps1", ".yaml", ".yml", ".json"}
    ]
    findings: list[dict[str, Any]] = []
    for path in paths:
        content = path.read_text(encoding="utf-8-sig", errors="replace")
        for rule, (pattern, severity) in patterns.items():
            match = re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
            if match:
                findings.append(
                    {
                        "rule": rule,
                        "severity": severity,
                        "path": str(path),
                        "line": content.count("\n", 0, match.start()) + 1,
                        "status": "suspected",
                        "evidence": match.group(0)[:240],
                    }
                )
    critical = [item for item in findings if item["severity"] == "critical"]
    return {
        "passed": not critical,
        "scanner_version": "1.0.0-local-equivalent",
        "scope": "SKILL.md, references, eval manifests and bundled executable scripts",
        "limitations": "Ausência de achados não certifica segurança; dependências externas continuam sujeitas a revisão humana.",
        "findings": findings,
        "files_checked": len(paths),
    }
