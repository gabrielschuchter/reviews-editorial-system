"""Claim-level provenance validation for the Reviews workflow."""

from __future__ import annotations

from typing import Any


DIRECT_SOURCE_ROLES = {"primary-evidence", "method-authority"}
CLAIM_KINDS = {"direct-fact", "result", "derived-calculation", "interpretation", "inference", "hypothesis", "external-criticism", "missing-information"}


def validate_claim_provenance(
    ledger: dict[str, Any], source_roles: dict[str, Any]
) -> dict[str, Any]:
    """Require every public claim to be traceable to a registered source span.

    This validates the chain of custody. It does not decide whether a claim is
    true or whether an inference is warranted; those remain scientific and
    editorial judgments with separate gates.
    """

    issues: list[dict[str, str]] = []
    records = source_roles.get("sources") if isinstance(source_roles, dict) else None
    role_map = {
        str(item.get("source_id")): item
        for item in records or []
        if isinstance(item, dict) and item.get("source_id")
    }
    if not role_map:
        issues.append({"claim_id": "source-roles", "message": "mapa de papéis de fonte vazio"})
    claims = ledger.get("claims") if isinstance(ledger, dict) else None
    if not isinstance(claims, list) or not claims:
        issues.append({"claim_id": "ledger", "message": "claim ledger vazio"})
        claims = []
    public_checked = 0
    for index, claim in enumerate(claims, start=1):
        claim_id = str(claim.get("claim_id") or f"claim[{index}]") if isinstance(claim, dict) else f"claim[{index}]"
        if not isinstance(claim, dict):
            issues.append({"claim_id": claim_id, "message": "claim deve ser objeto"})
            continue
        if claim.get("claim_type") not in CLAIM_KINDS:
            issues.append({"claim_id": claim_id, "message": "tipo de claim desconhecido"})
        if claim.get("allowed_in_public_draft") is not True:
            continue
        public_checked += 1
        source_id = str(claim.get("source_document") or "")
        source = role_map.get(source_id)
        if source is None:
            issues.append({"claim_id": claim_id, "message": "fonte do claim não está registrada em source_roles"})
            continue
        if source.get("source_role") not in DIRECT_SOURCE_ROLES:
            issues.append({"claim_id": claim_id, "message": "claim público não usa fonte de evidência ou autoridade metodológica"})
        if not str(claim.get("source_excerpt") or "").strip():
            issues.append({"claim_id": claim_id, "message": "excerto localizado ausente"})
        if not any(claim.get(key) not in (None, "") for key in ("page", "table", "figure", "section")):
            issues.append({"claim_id": claim_id, "message": "localizador ausente"})
        provenance = claim.get("provenance")
        if not isinstance(provenance, dict) or not all(provenance.get(key) for key in ("extracted_at", "extracted_by", "method", "source_hash")):
            issues.append({"claim_id": claim_id, "message": "proveniência de extração incompleta"})
        if claim.get("claim_type") in {"inference", "hypothesis"} and claim.get("verification_status") != "verified":
            issues.append({"claim_id": claim_id, "message": "inferência/hipótese pública sem verificação explícita"})
    return {
        "valid": not issues,
        "claims_checked": len(claims),
        "public_claims_checked": public_checked,
        "issues": issues,
        "boundary": "Proveniência confirma fonte, localizador e cadeia de extração; não substitui auditoria factual ou julgamento científico.",
    }
