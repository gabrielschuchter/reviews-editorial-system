from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.constants import MISSING_INFORMATION
from reviews_editorial.io import dump_data, load_data
from reviews_editorial.jobs import load_job

FILES = {
    "study-overview.json": {"study_id": None, "design": "undetermined", "primary_outcome": None},
    "population.json": {"population": None, "randomized": None, "analyzed": None, "groups": []},
    "interventions.json": {"interventions": [], "comparators": []},
    "outcomes.json": {"outcomes": []},
    "results.json": {"results": []},
    "safety.json": {"safety_outcomes": []},
    "missing-information.json": {"items": [MISSING_INFORMATION]},
}


def _content_complete(filename: str, payload: dict) -> bool:
    missing = payload.get("missing_information")
    has_missing_record = isinstance(missing, list) and any(
        isinstance(item, str) and item.strip() for item in missing
    )
    if filename == "study-overview.json":
        return bool(payload.get("study_id")) and (
            payload.get("design") not in (None, "", "undetermined")
            or has_missing_record
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
        items = payload.get("items")
        return isinstance(items, list)
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description="Inicializar ou validar o pacote de extração factual.")
    parser.add_argument("job_dir")
    parser.add_argument("--initialize", action="store_true")
    args = parser.parse_args()
    root = Path(args.job_dir)
    extraction = root / "extraction"
    job = load_job(root)
    if args.initialize:
        for filename, template in FILES.items():
            path = extraction / filename
            if path.exists():
                continue
            payload = {
                "extraction_status": "not-extracted",
                "source_documents": [source["source_id"] for source in job["source_documents"]],
                "validated_by": None,
                "validated_at": None,
                **template,
            }
            dump_data(path, payload)
    missing = [filename for filename in FILES if not (extraction / filename).is_file()]
    pending = []
    content_issues = []
    for filename in FILES:
        path = extraction / filename
        if not path.is_file():
            continue
        payload = load_data(path)
        if not isinstance(payload, dict):
            content_issues.append(f"{filename}: conteúdo deve ser um objeto")
            continue
        if payload.get("extraction_status") != "validated":
            pending.append(filename)
            continue
        if not payload.get("source_documents"):
            content_issues.append(f"{filename}: source_documents vazio")
        if not str(payload.get("validated_by") or "").strip():
            content_issues.append(f"{filename}: validated_by ausente")
        if not str(payload.get("validated_at") or "").strip():
            content_issues.append(f"{filename}: validated_at ausente")
        if not _content_complete(filename, payload):
            content_issues.append(
                f"{filename}: conteúdo factual vazio sem missing_information explícito"
            )
    report = {
        "valid": not missing and not pending and not content_issues,
        "missing_files": missing,
        "pending_validation": pending,
        "content_issues": content_issues,
        "note": (
            "Este gate verifica completude estrutural mínima; contratos unitários devem ser "
            "validados com scripts/validate_schema.py e o suporte semântico exige revisão."
        ),
    }
    dump_data(extraction / "extraction-validation.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
