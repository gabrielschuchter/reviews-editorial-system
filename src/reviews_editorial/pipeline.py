"""Máquina de estados e gates do fluxo editorial."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .constants import (
    APPROVED_STATUS,
    CRITICAL_AUDIT_STATUSES,
    HUMAN_REVIEW_STATUS,
    PIPELINE_STATES,
    REQUIRED_OUTPUTS_BY_STATE,
)
from .guideline_attribution import audit_guideline_attribution
from .guideline_intro import audit_guideline_introduction
from .io import dump_data, load_data
from .jobs import load_job, utc_now, validate_job_shape
from .strict_style import audit_strict_style


def state_index(state: str) -> int:
    try:
        return PIPELINE_STATES.index(state)
    except ValueError as exc:
        raise ValueError(f"Estado desconhecido: {state}") from exc


def required_outputs_through(state: str) -> list[str]:
    index = state_index(state)
    result: list[str] = []
    for completed_state in PIPELINE_STATES[: index + 1]:
        result.extend(REQUIRED_OUTPUTS_BY_STATE.get(completed_state, ()))
    return result


def _collect_critical_issues(payload: Any) -> list[str]:
    issues: list[str] = []
    if isinstance(payload, dict):
        severity = str(payload.get("severity", "")).casefold()
        status = str(payload.get("status", "")).casefold()
        if severity == "critical" or status in CRITICAL_AUDIT_STATUSES:
            identifier = payload.get("issue_id") or payload.get("finding_id") or payload.get("message") or status
            issues.append(str(identifier))
        for value in payload.values():
            issues.extend(_collect_critical_issues(value))
    elif isinstance(payload, list):
        for value in payload:
            issues.extend(_collect_critical_issues(value))
    return issues


def _require_boolean_gate(
    root: Path,
    relative: str,
    keys: tuple[str, ...],
    errors: list[str],
) -> None:
    path = root / relative
    if not path.is_file():
        return
    payload: Any = load_data(path)
    for key in keys:
        if not isinstance(payload, dict) or key not in payload:
            errors.append(f"{relative} não contém o gate obrigatório {'.'.join(keys)}")
            return
        payload = payload[key]
    if payload is not True:
        errors.append(f"{relative} não passou o gate {'.'.join(keys)}")


def _strict_style_artifact(root: Path, state: str) -> tuple[Path, Path] | None:
    """Selecionar a versão pública vigente e o relatório correspondente."""

    index = state_index(state)
    candidates: list[tuple[str, str, str]] = [
        ("candidate_for_review", "final/candidate.md", "audits/strict-style-final.json"),
        ("coherence_review_complete", "drafts/v4-candidate.md", "audits/strict-style-final.json" if index >= state_index("final_audit_complete") else "audits/strict-style-v4.json"),
        ("style_review_complete", "drafts/v3-style.md", "audits/strict-style-audit.json"),
        ("structural_review_complete", "drafts/v2-structure.md", "audits/strict-style-v2.json"),
        ("first_draft", "drafts/v1-content.md", "audits/strict-style-v1.json"),
    ]
    for minimum_state, artifact, report in candidates:
        path = root / artifact
        if index >= state_index(minimum_state) and path.is_file():
            return path, root / report
    return None


def _run_strict_style_gate(root: Path, state: str, errors: list[str]) -> None:
    selected = _strict_style_artifact(root, state)
    if selected is None:
        return
    artifact_path, report_path = selected
    report = audit_strict_style(
        artifact_path.read_text(encoding="utf-8-sig"),
        artifact_id=str(artifact_path.relative_to(root)),
    )
    dump_data(report_path, report)
    if report.get("passed") is not True:
        categories = sorted({str(item.get("category")) for item in report.get("findings", [])})
        errors.append(
            f"gate rígido de estilo bloqueou {artifact_path.relative_to(root)}: {categories}"
        )


def _is_guideline_job(root: Path) -> bool:
    brief_path = root / "planning" / "editorial-brief.json"
    if not brief_path.is_file():
        return False
    brief = load_data(brief_path)
    edition_type = str(brief.get("edition_type") or "").casefold()
    return "guideline" in edition_type or "diretriz" in edition_type


def _run_guideline_introduction_gate(root: Path, state: str, errors: list[str]) -> None:
    if not _is_guideline_job(root):
        return
    selected = _strict_style_artifact(root, state)
    if selected is None:
        return
    artifact_path, _ = selected
    final_stage = state_index(state) >= state_index("final_audit_complete")
    report_path = root / "audits" / (
        "guideline-introduction-final.json"
        if final_stage
        else "guideline-introduction-audit.json"
    )
    report = audit_guideline_introduction(
        artifact_path.read_text(encoding="utf-8-sig"),
        artifact_id=str(artifact_path.relative_to(root)),
    )
    dump_data(report_path, report)
    if report.get("passed") is not True:
        rules = sorted({str(item.get("rule_id")) for item in report.get("findings", [])})
        errors.append(
            f"gate de introdução de diretriz bloqueou {artifact_path.relative_to(root)}: {rules}"
        )


def _run_guideline_attribution_gate(root: Path, state: str, errors: list[str]) -> None:
    if not _is_guideline_job(root):
        return
    selected = _strict_style_artifact(root, state)
    if selected is None:
        return
    artifact_path, _ = selected
    final_stage = state_index(state) >= state_index("final_audit_complete")
    report_path = root / "audits" / (
        "guideline-attribution-final.json"
        if final_stage
        else "guideline-attribution-audit.json"
    )
    report = audit_guideline_attribution(
        artifact_path.read_text(encoding="utf-8-sig"),
        artifact_id=str(artifact_path.relative_to(root)),
    )
    dump_data(report_path, report)
    if report.get("passed") is not True:
        rules = sorted({str(item.get("rule_id")) for item in report.get("findings", [])})
        errors.append(
            f"gate de atribuição em diretriz bloqueou {artifact_path.relative_to(root)}: {rules}"
        )


def validate_pipeline(job_dir: str | Path, target_state: str | None = None) -> dict[str, Any]:
    root = Path(job_dir).resolve()
    job = load_job(root)
    state = target_state or job.get("state")
    errors = validate_job_shape(job)
    warnings: list[str] = []

    if state_index(state) >= state_index("first_draft"):
        _run_strict_style_gate(root, state, errors)
        _run_guideline_introduction_gate(root, state, errors)
        _run_guideline_attribution_gate(root, state, errors)

    missing_outputs = [
        relative for relative in required_outputs_through(state) if not (root / relative).is_file()
    ]
    if missing_outputs:
        errors.append(f"outputs obrigatórios ausentes: {missing_outputs}")

    if state_index(state) >= state_index("documents_validated"):
        validation_path = root / "normalized" / "document-validation.json"
        if validation_path.is_file():
            validation = load_data(validation_path)
            if validation.get("status") != "passed":
                errors.append("document-validation.json ainda não foi confirmado como passed")
        manual_review_path = root / "normalized" / "manual-document-review.json"
        if manual_review_path.is_file():
            manual_review = load_data(manual_review_path)
            if manual_review.get("review_status") != "passed":
                errors.append("manual-document-review.json ainda não foi confirmado")
            if validation_path.is_file() and (
                manual_review.get("document_inventory_sha256")
                != validation.get("document_inventory_sha256")
            ):
                errors.append("revisão manual pertence a outro inventário documental")

    if state_index(state) >= state_index("document_package_normalized"):
        inventory_path = root / "normalized" / "document-inventory.json"
        if inventory_path.is_file():
            inventory = load_data(inventory_path)
            expected_hashes = sorted(
                str(source.get("sha256") or "")
                for source in job.get("source_documents", [])
            )
            observed_hashes = sorted(
                str(document.get("source_sha256") or "")
                for document in inventory.get("documents", [])
            )
            if expected_hashes != observed_hashes:
                errors.append(
                    "hashes do inventário normalizado divergem das fontes registradas no job"
                )

    if state_index(state) >= state_index("evidence_extracted"):
        _require_boolean_gate(
            root,
            "extraction/extraction-validation.json",
            ("valid",),
            errors,
        )

    if state_index(state) >= state_index("numbers_verified"):
        _require_boolean_gate(
            root,
            "extraction/number-verification.json",
            ("valid",),
            errors,
        )

    if state_index(state) >= state_index("claim_ledger_complete"):
        _require_boolean_gate(
            root,
            "extraction/claim-ledger.json",
            ("validation", "valid"),
            errors,
        )
        ledger_path = root / "extraction" / "claim-ledger.json"
        if ledger_path.is_file() and not load_data(ledger_path).get("claims"):
            errors.append("claim-ledger.json está vazio")

    structured_audit_gates = (
        ("factual_audit_complete", "audits/factual-audit.json"),
        (
            "statistical_methodological_audit_complete",
            "audits/statistical-audit.json",
        ),
        (
            "statistical_methodological_audit_complete",
            "audits/methodological-audit.json",
        ),
        ("structural_review_complete", "audits/structural-audit.json"),
        ("style_review_complete", "audits/style-audit.json"),
        ("style_review_complete", "audits/anti-ai-audit.json"),
        ("style_review_complete", "audits/strict-style-audit.json"),
        ("coherence_review_complete", "audits/coherence-audit.json"),
        ("final_audit_complete", "audits/strict-style-final.json"),
        ("final_audit_complete", "audits/final-audit.json"),
    )
    for gate_state, relative in structured_audit_gates:
        if state_index(state) >= state_index(gate_state):
            _require_boolean_gate(root, relative, ("passed",), errors)

    critical_issues = list(job.get("gates", {}).get("critical_errors", []))
    for audit_path in (root / "audits").glob("*.json") if (root / "audits").exists() else []:
        critical_issues.extend(_collect_critical_issues(load_data(audit_path)))
    if critical_issues:
        errors.append(f"erros críticos abertos: {sorted(set(critical_issues))}")

    if state_index(state) >= state_index("human_review"):
        review_path = root / "final" / "review-status.json"
        if review_path.is_file() and load_data(review_path).get("status") != HUMAN_REVIEW_STATUS:
            errors.append("status de revisão humana inválido")

    if state == "approved":
        approval_path = root / "final" / "publication-approval.json"
        if approval_path.is_file() and load_data(approval_path).get("status") != APPROVED_STATUS:
            errors.append("aprovação de publicação inválida")

    if state_index(state) < state_index("external_research_complete"):
        warnings.append("pesquisa externa ainda não concluída")
    return {
        "job_id": job.get("job_id"),
        "state": state,
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "missing_outputs": missing_outputs,
    }


def advance_job(
    job_dir: str | Path,
    target_state: str,
    *,
    actor: str,
    human_approval: bool = False,
) -> dict[str, Any]:
    """Avançar exatamente um estado após validar outputs e gates."""

    root = Path(job_dir).resolve()
    if not actor.strip():
        raise ValueError("actor é obrigatório para registrar a transição")
    job = load_job(root)
    current_index = state_index(job["state"])
    target_index = state_index(target_state)
    if target_index != current_index + 1:
        raise ValueError("O avanço deve ocorrer para o estado imediatamente seguinte")
    if target_state == "approved" and not human_approval:
        raise PermissionError("A aprovação final exige human_approval=True e registro documental")
    report = validate_pipeline(root, target_state=target_state)
    if not report["valid"]:
        raise RuntimeError("Gate bloqueado: " + " | ".join(report["errors"]))
    now = utc_now()
    job["state"] = target_state
    if target_state == "candidate_for_review":
        job["status"] = HUMAN_REVIEW_STATUS
    elif target_state == "approved":
        job["status"] = APPROVED_STATUS
    else:
        job["status"] = "EM PROCESSAMENTO"
    job["updated_at"] = now
    job["history"].append({"state": target_state, "at": now, "actor": actor.strip()})
    dump_data(root / "job.yml", job)
    from .registry import sync_job_to_registry

    sync_job_to_registry(root, actor_id=actor.strip(), role="editor")
    return report
