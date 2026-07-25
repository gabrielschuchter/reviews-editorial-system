"""Comparação de versões e promoção controlada de feedback."""

from __future__ import annotations

import difflib
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
    return {"similarity_ratio": matcher.ratio(), "unified_diff": diff, "changes": changes}


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
