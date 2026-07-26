from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _bootstrap import REPO_ROOT
from reviews_editorial.constants import MISSING_INFORMATION
from reviews_editorial.io import dump_data, load_data
from reviews_editorial.jobs import load_job


# Each item is a real editorial artifact, never a generated blank shell.  The
# script imports only a structured extraction that names the source spans and
# a responsible reviewer.
FILES = {
    "study-overview.json": {"study_id", "design", "primary_outcome"},
    "population.json": {"population", "randomized", "analyzed", "groups"},
    "interventions.json": {"interventions", "comparators"},
    "outcomes.json": {"outcomes"},
    "results.json": {"results"},
    "safety.json": {"safety_outcomes"},
    "missing-information.json": {"items"},
}


def _content_complete(filename: str, payload: dict[str, Any]) -> bool:
    missing = payload.get("missing_information")
    has_missing_record = isinstance(missing, list) and any(
        isinstance(item, str) and item.strip() for item in missing
    )
    if filename == "study-overview.json":
        return bool(payload.get("study_id")) and (
            payload.get("design") not in (None, "", "undetermined") or has_missing_record
        )
    if filename == "population.json":
        return payload.get("population") not in (None, "") or has_missing_record
    if filename == "interventions.json":
        return bool(payload.get("interventions") or payload.get("comparators")) or has_missing_record
    if filename == "outcomes.json":
        return bool(payload.get("outcomes")) or has_missing_record
    if filename == "results.json":
        return bool(payload.get("results")) or has_missing_record
    if filename == "safety.json":
        return bool(payload.get("safety_outcomes")) or has_missing_record
    if filename == "missing-information.json":
        return isinstance(payload.get("items"), list)
    return False


def _source_ids(payload: dict[str, Any]) -> set[str]:
    records = payload.get("source_documents")
    if not isinstance(records, list):
        return set()
    return {str(item) for item in records if isinstance(item, str) and item.strip()}


def validate_extraction_package(
    package: dict[str, Any], *, known_source_ids: set[str]
) -> dict[str, Any]:
    """Validate curated extraction before copying it into a job directory."""

    artifacts = package.get("artifacts", package)
    if not isinstance(artifacts, dict):
        return {"valid": False, "errors": ["pacote de extração deve ser objeto"], "artifacts": {}}
    errors: list[str] = []
    normalized: dict[str, dict[str, Any]] = {}
    for filename, required_fields in FILES.items():
        payload = artifacts.get(filename)
        if not isinstance(payload, dict):
            errors.append(f"{filename}: artefato ausente ou inválido")
            continue
        missing_fields = sorted(field for field in required_fields if field not in payload)
        if missing_fields:
            errors.append(f"{filename}: campos obrigatórios ausentes: {missing_fields}")
        if payload.get("extraction_status") != "validated":
            errors.append(f"{filename}: extraction_status deve ser validated")
        if not str(payload.get("validated_by") or "").strip():
            errors.append(f"{filename}: validated_by ausente")
        if not str(payload.get("validated_at") or "").strip():
            errors.append(f"{filename}: validated_at ausente")
        sources = _source_ids(payload)
        if not sources:
            errors.append(f"{filename}: source_documents vazio")
        elif not sources.issubset(known_source_ids):
            errors.append(f"{filename}: cita fonte que não pertence ao job")
        if not _content_complete(filename, payload):
            errors.append(
                f"{filename}: conteúdo factual vazio sem missing_information explícito ({MISSING_INFORMATION})"
            )
        normalized[filename] = payload
    return {"valid": not errors, "errors": errors, "artifacts": normalized}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Importar e validar extração factual curada; não cria placeholders."
    )
    parser.add_argument("job_dir")
    parser.add_argument(
        "--input",
        required=True,
        type=Path,
        help="JSON/YAML-JSON com artifacts por nome de arquivo e evidência localizada.",
    )
    args = parser.parse_args()
    root = Path(args.job_dir)
    job = load_job(root)
    payload = load_data(args.input)
    if not isinstance(payload, dict):
        parser.error("--input deve conter objeto JSON/YAML-JSON")
    report = validate_extraction_package(
        payload,
        known_source_ids={str(source["source_id"]) for source in job["source_documents"]},
    )
    extraction = root / "extraction"
    if report["valid"]:
        for filename, artifact in report["artifacts"].items():
            dump_data(extraction / filename, artifact)
    validation = {
        "valid": report["valid"],
        "missing_files": [],
        "pending_validation": [],
        "content_issues": report["errors"],
        "source_input": str(args.input.resolve()),
        "note": "O pacote foi aceito somente após conter extração real, fonte pertencente ao job e validação humana identificada.",
    }
    dump_data(extraction / "extraction-validation.json", validation)
    print(json.dumps(validation, ensure_ascii=False, indent=2))
    return 0 if validation["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
