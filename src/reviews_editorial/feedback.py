"""Comparação de versões e promoção controlada de feedback."""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Any

FEEDBACK_TYPES = {
    "factual-correction",
    "statistical-correction",
    "methodological-correction",
    "structural-correction",
    "style-correction",
    "native-portuguese-correction",
    "anti-ai-correction",
    "terminology-preference",
    "local-editorial-choice",
    "candidate-general-rule",
}


NUMERIC_TOKEN = re.compile(
    r"(?<![\w])(?:p\s*[<=>]\s*)?-?\d+(?:[.,]\d+)?(?:\s*(?:%|mg|g|kg|mmol/L|"
    r"mmHg|mL|L|anos?|meses?|dias?|participantes?))?(?![\w])",
    re.IGNORECASE,
)
REFERENCE_TOKEN = re.compile(
    r"\[[0-9,\s–—-]+\]|\((?:[A-ZÁ-Ú][^()]{1,70}),\s*(?:19|20)\d{2}\)"
)
INTERPRETATION_MARKERS = {
    "causalidade": ("causou", "provocou", "determinou", "levou a"),
    "associação": ("associado", "associação", "correlacionado"),
    "certeza_forte": ("demonstra", "comprova", "confirma", "sem dúvida"),
    "incerteza": ("pode", "sugere", "compatível", "incerto", "não permite concluir"),
    "relevância_clínica": ("clinicamente relevante", "benefício clínico", "efeito trivial"),
    "limitação": ("limitação", "viés", "ressalva", "intervalo de confiança"),
}


def _token_context(text: str, start: int, end: int, radius: int = 60) -> str:
    left = max(0, start - radius)
    right = min(len(text), end + radius)
    return re.sub(r"\s+", " ", text[left:right]).strip()


def _numeric_changes(original: str, revised: str) -> list[dict[str, Any]]:
    before = [
        {"value": match.group(0), "context": _token_context(original, *match.span())}
        for match in NUMERIC_TOKEN.finditer(original)
    ]
    after = [
        {"value": match.group(0), "context": _token_context(revised, *match.span())}
        for match in NUMERIC_TOKEN.finditer(revised)
    ]
    matcher = difflib.SequenceMatcher(
        a=[item["value"].casefold() for item in before],
        b=[item["value"].casefold() for item in after],
    )
    changes: list[dict[str, Any]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        changes.append(
            {
                "operation": tag,
                "before": before[i1:i2],
                "after": after[j1:j2],
                "requires_manual_verification": True,
            }
        )
    return changes


def _interpretation_changes(original: str, revised: str) -> list[dict[str, Any]]:
    original_key = original.casefold()
    revised_key = revised.casefold()
    changes: list[dict[str, Any]] = []
    for category, markers in INTERPRETATION_MARKERS.items():
        before = sorted(marker for marker in markers if marker in original_key)
        after = sorted(marker for marker in markers if marker in revised_key)
        if before != after:
            changes.append(
                {
                    "category": category,
                    "before_markers": before,
                    "after_markers": after,
                    "interpretation": "sinal heurístico; requer revisão humana",
                }
            )
    return changes


def compare_versions(original: str, revised: str) -> dict[str, Any]:
    before = original.splitlines()
    after = revised.splitlines()
    diff = list(
        difflib.unified_diff(before, after, fromfile="candidate", tofile="reviewed", lineterm="")
    )
    matcher = difflib.SequenceMatcher(a=original, b=revised)
    changes = []
    for index, (tag, i1, i2, j1, j2) in enumerate(matcher.get_opcodes(), start=1):
        if tag == "equal":
            continue
        changes.append(
            {
                "feedback_id": f"FDB-{index:04d}",
                "operation": tag,
                "original": original[i1:i2],
                "edited": revised[j1:j2],
                "feedback_type": None,
                "reason": None,
                "generalizable": False,
                "candidate_rule": None,
                "approval_status": "pending-editorial-classification",
            }
        )
    original_references = REFERENCE_TOKEN.findall(original)
    revised_references = REFERENCE_TOKEN.findall(revised)
    original_headings = [
        line.strip() for line in original.splitlines() if line.lstrip().startswith("#")
    ]
    revised_headings = [
        line.strip() for line in revised.splitlines() if line.lstrip().startswith("#")
    ]
    return {
        "similarity_ratio": matcher.ratio(),
        "unified_diff": diff,
        "changes": changes,
        "numeric_changes": _numeric_changes(original, revised),
        "reference_changes": {
            "removed": sorted(set(original_references) - set(revised_references)),
            "added": sorted(set(revised_references) - set(original_references)),
        },
        "structural_changes": {
            "headings_before": original_headings,
            "headings_after": revised_headings,
            "changed": original_headings != revised_headings,
        },
        "interpretation_changes": _interpretation_changes(original, revised),
    }


def _repository_file(
    value: Any,
    *,
    repository_root: Path,
    identity: str,
    field: str,
    issues: list[dict[str, Any]],
) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        issues.append({"feedback_id": identity, "message": f"{field} ausente"})
        return None
    candidate = Path(value)
    resolved = (
        candidate.resolve()
        if candidate.is_absolute()
        else (repository_root / candidate).resolve()
    )
    try:
        resolved.relative_to(repository_root)
    except ValueError:
        issues.append(
            {
                "feedback_id": identity,
                "message": f"{field} aponta para fora do repositório",
            }
        )
        return None
    if not resolved.is_file():
        issues.append(
            {
                "feedback_id": identity,
                "message": f"{field} não existe: {value}",
            }
        )
        return None
    return resolved


def validate_feedback(
    records: list[dict[str, Any]],
    *,
    repository_root: str | Path | None = None,
) -> dict[str, Any]:
    issues = []
    candidate_rules = []
    root = Path(repository_root).resolve() if repository_root is not None else None
    for record in records:
        identity = record.get("feedback_id", "feedback")
        if record.get("feedback_type") not in FEEDBACK_TYPES:
            issues.append({"feedback_id": identity, "message": "feedback_type ausente ou inválido"})
        if record.get("generalizable"):
            missing = [
                key
                for key in ("reason", "candidate_rule", "target_rule_file", "regression_test")
                if not record.get(key)
            ]
            if missing:
                issues.append({"feedback_id": identity, "message": f"regra candidata incompleta: {missing}"})
            if record.get("approval_status") != "approved-by-editor":
                issues.append({"feedback_id": identity, "message": "regra geral ainda não aprovada pelo editor"})
            regression = record.get("regression_test")
            if regression and not isinstance(regression, dict):
                issues.append(
                    {
                        "feedback_id": identity,
                        "message": "regression_test deve ser um objeto estruturado",
                    }
                )
            elif isinstance(regression, dict):
                if regression.get("passed_existing_cases") is not True:
                    issues.append(
                        {
                            "feedback_id": identity,
                            "message": "regressão não comprova que os casos existentes passaram",
                        }
                    )
                if not str(regression.get("test_id") or "").strip():
                    issues.append(
                        {
                            "feedback_id": identity,
                            "message": "regression_test.test_id ausente",
                        }
                    )
                if root is not None:
                    _repository_file(
                        regression.get("location"),
                        repository_root=root,
                        identity=identity,
                        field="regression_test.location",
                        issues=issues,
                    )
            if root is not None and record.get("target_rule_file"):
                _repository_file(
                    record.get("target_rule_file"),
                    repository_root=root,
                    identity=identity,
                    field="target_rule_file",
                    issues=issues,
                )
            record_issues = [
                issue for issue in issues if issue.get("feedback_id") == identity
            ]
            if not record_issues and record.get("approval_status") == "approved-by-editor":
                candidate_rules.append(record)
    return {
        "valid": not issues,
        "issues": issues,
        "approved_rule_proposals": candidate_rules,
        "automatic_rule_mutation_performed": False,
    }
