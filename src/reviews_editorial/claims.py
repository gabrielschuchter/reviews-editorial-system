"""Claim ledger, verificação numérica e segurança factual."""

from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from .io import dump_data, load_data
from .schema_validation import validate

CLAIM_TYPES = {
    "direct-fact",
    "result",
    "derived-calculation",
    "interpretation",
    "inference",
    "hypothesis",
    "external-criticism",
    "missing-information",
}
VERIFICATION_STATUSES = {
    "verified",
    "partially-verified",
    "unsupported",
    "ambiguous",
    "divergent",
    "extrapolative",
    "pending",
}
NUMBER_RE = re.compile(r"(?<![\w])(?:\d{1,3}(?:[.,]\d+)?|\d{4})(?:\s*%)?(?![\w])")


@lru_cache(maxsize=1)
def _claim_schema() -> dict[str, Any]:
    path = Path(__file__).resolve().parents[2] / "schemas" / "claim.schema.json"
    return load_data(path)


def _number_tokens(text: str) -> set[str]:
    return {
        re.sub(r"\s+", "", token).replace(",", ".")
        for token in NUMBER_RE.findall(text)
    }


def _has_locator(claim: dict[str, Any]) -> bool:
    return any(claim.get(key) not in (None, "") for key in ("page", "table", "figure", "section"))


def validate_claim(claim: dict[str, Any], index: int) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    prefix = claim.get("claim_id") or f"claim[{index}]"
    for schema_issue in validate(claim, _claim_schema(), path=f"$.claims[{index - 1}]"):
        issues.append(
            {
                "issue_id": prefix,
                "severity": "critical",
                "message": f"{schema_issue.path}: {schema_issue.message}",
            }
        )
    for field in (
        "job_id",
        "claim_text",
        "claim_type",
        "source_document",
        "source_excerpt",
        "verification_status",
        "allowed_in_public_draft",
        "provenance",
    ):
        if field not in claim:
            issues.append({"issue_id": prefix, "severity": "critical", "message": f"campo ausente: {field}"})
    if claim.get("claim_type") not in CLAIM_TYPES:
        issues.append({"issue_id": prefix, "severity": "critical", "message": "claim_type inválido"})
    if claim.get("verification_status") not in VERIFICATION_STATUSES:
        issues.append({"issue_id": prefix, "severity": "critical", "message": "verification_status inválido"})

    public = claim.get("allowed_in_public_draft") is True
    quantitative = bool(NUMBER_RE.search(str(claim.get("claim_text") or "")))
    if public and claim.get("verification_status") != "verified":
        issues.append(
            {
                "issue_id": prefix,
                "severity": "critical",
                "message": "claim público deve estar integralmente verificado",
            }
        )
    if public and claim.get("claim_type") != "missing-information":
        if not claim.get("source_document") or not claim.get("source_excerpt") or not _has_locator(claim):
            issues.append(
                {
                    "issue_id": prefix,
                    "severity": "critical",
                    "message": "claim público sem fonte, excerto ou localizador",
                }
            )
    if quantitative and public and not claim.get("source_document"):
        issues.append({"issue_id": prefix, "severity": "critical", "message": "número público sem fonte"})
    if claim.get("claim_type") == "derived-calculation" and not claim.get("calculation_method"):
        issues.append({"issue_id": prefix, "severity": "major", "message": "cálculo derivado sem método"})
    return issues


def build_claim_ledger(claims: list[dict[str, Any]]) -> dict[str, Any]:
    normalized: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    if not claims:
        issues.append(
            {
                "issue_id": "ledger-empty",
                "severity": "critical",
                "message": "claim ledger vazio; nenhum texto factual pode avançar",
            }
        )
    seen_ids: set[str] = set()
    for index, raw in enumerate(claims, start=1):
        claim = dict(raw)
        claim.setdefault("claim_id", f"CLM-{index:04d}")
        claim.setdefault("page", None)
        claim.setdefault("table", None)
        claim.setdefault("figure", None)
        claim.setdefault("section", None)
        claim.setdefault("notes", None)
        if claim["claim_id"] in seen_ids:
            issues.append(
                {
                    "issue_id": claim["claim_id"],
                    "severity": "critical",
                    "message": "claim_id duplicado",
                }
            )
        seen_ids.add(claim["claim_id"])
        normalized.append(claim)
        issues.extend(validate_claim(claim, index))
    return {
        "ledger_version": "0.1.0",
        "claims": normalized,
        "validation": {
            "valid": not any(issue["severity"] == "critical" for issue in issues),
            "issues": issues,
        },
    }


def verify_number_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    if not isinstance(records, list):
        return {
            "records": records,
            "valid": False,
            "issues": [
                {
                    "issue_id": "number-records",
                    "severity": "critical",
                    "message": "registros numéricos devem ser uma lista",
                }
            ],
        }
    for index, record in enumerate(records, start=1):
        identity = record.get("record_id") or f"number[{index}]"
        for field in ("reported_value", "source_document", "locator", "unit", "direction"):
            if record.get(field) in (None, ""):
                issues.append({"issue_id": identity, "severity": "critical", "message": f"campo numérico ausente: {field}"})
        if record.get("derived") and not record.get("calculation_method"):
            issues.append({"issue_id": identity, "severity": "critical", "message": "cálculo derivado sem método"})
        verification_status = record.get("verification_status")
        if verification_status != "verified":
            message = (
                "divergência numérica não resolvida"
                if verification_status == "divergent"
                else "número ambíguo ou não verificado"
            )
            issues.append(
                {"issue_id": identity, "severity": "critical", "message": message}
            )
    return {
        "records": records,
        "valid": not any(issue["severity"] == "critical" for issue in issues),
        "issues": issues,
    }


def audit_draft_text(draft: str, ledger: dict[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    claims = ledger.get("claims", [])
    if not ledger.get("validation", {}).get("valid"):
        issues.append({"issue_id": "ledger", "severity": "critical", "message": "claim ledger inválido"})
    for claim in claims:
        text = str(claim.get("claim_text") or "").strip()
        if text and text in draft and claim.get("allowed_in_public_draft") is not True:
            issues.append(
                {"issue_id": claim.get("claim_id"), "severity": "critical", "message": "claim não autorizado apareceu no draft"}
            )
    public_number_tokens: set[str] = set()
    for claim in claims:
        if claim.get("allowed_in_public_draft") is True:
            public_number_tokens.update(_number_tokens(str(claim.get("claim_text") or "")))
    draft_numbers = sorted(_number_tokens(draft))
    uncovered = [token for token in draft_numbers if token not in public_number_tokens]
    for token in uncovered:
        issues.append(
            {
                "issue_id": f"unmapped-number:{token}",
                "severity": "critical",
                "message": "número no draft não localizado em claim público verificado",
            }
        )
    return {
        "audit_version": "0.1.0",
        "passed": not any(issue["severity"] == "critical" for issue in issues),
        "draft_number_tokens": draft_numbers,
        "issues": issues,
    }


def build_ledger_file(
    input_path: str | Path,
    output_path: str | Path,
    *,
    job_id: str | None = None,
) -> dict[str, Any]:
    payload = load_data(input_path)
    claims = payload.get("claims", payload) if isinstance(payload, dict) else payload
    if not isinstance(claims, list):
        raise ValueError("A entrada do claim ledger deve ser uma lista ou objeto com claims")
    if job_id:
        claims = [
            {**claim, "job_id": claim.get("job_id") or job_id}
            if isinstance(claim, dict)
            else claim
            for claim in claims
        ]
    ledger = build_claim_ledger(claims)
    dump_data(output_path, ledger)
    return ledger
