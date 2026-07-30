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
from .io import dump_data, load_data
from .jobs import load_job, utc_now, validate_job_shape


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
            issues.append(str(payload.get("issue_id") or payload.get("message") or status))
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


def validate_pipeline(job_dir: str | Path, target_state: str | None = None) -> dict[str, Any]:
    root = Path(job_dir).resolve()
    job = load_job(root)
    state = target_state or job.get("state")
    errors = validate_job_shape(job)
    warnings: list[str] = []
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
        ("coherence_review_complete", "audits/coherence-audit.json"),
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
