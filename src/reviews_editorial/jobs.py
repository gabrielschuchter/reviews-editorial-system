"""Criação, validação e isolamento de jobs editoriais."""

from __future__ import annotations

import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .constants import (
    EDITORIAL_CONSTITUTION_VERSION,
    HUMAN_REVIEW_STATUS,
    PIPELINE_STATES,
    SKILL_VERSION,
    SYSTEM_VERSION,
)
from .io import dump_data, load_data, sha256_file
from .schema_validation import validate

JOB_PATTERN = re.compile(r"^JOB-(\d{4})-(\d{3})$")
JOB_SUBDIRECTORIES = (
    "input",
    "normalized",
    "extraction",
    "analysis",
    "research",
    "planning",
    "drafts",
    "audits",
    "visuals",
    "feedback",
    "final",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def allocate_job_id(jobs_root: str | Path, year: int | None = None) -> str:
    root = Path(jobs_root)
    chosen_year = year or datetime.now().year
    maximum = 0
    if root.exists():
        for child in root.iterdir():
            match = JOB_PATTERN.match(child.name)
            if match and int(match.group(1)) == chosen_year:
                maximum = max(maximum, int(match.group(2)))
    if maximum >= 999:
        raise RuntimeError(f"Limite anual de jobs atingido para {chosen_year}")
    return f"JOB-{chosen_year}-{maximum + 1:03d}"


def _source_record(path: Path, copy_path: Path | None = None) -> dict[str, Any]:
    return {
        "source_id": f"local:{sha256_file(path)[:16]}",
        "kind": "local-file",
        "original_name": path.name,
        "location": str(path.resolve()),
        "job_copy": str(copy_path.resolve()) if copy_path else None,
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "immutable_source": True,
    }


def create_job(
    jobs_root: str | Path,
    source_paths: list[str | Path],
    *,
    topic: str,
    requested_edition_type: str | None = None,
    source_folder: str | None = None,
    editor: str | None = None,
    notes: str | None = None,
    copy_inputs: bool = False,
    year: int | None = None,
) -> Path:
    """Criar um job sem alterar os documentos originais."""

    root = Path(jobs_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    if not topic.strip():
        raise ValueError("O tema do job não pode ser vazio")
    resolved_sources = [Path(path).resolve() for path in source_paths]
    missing = [str(path) for path in resolved_sources if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Fontes não encontradas: {missing}")
    if not resolved_sources:
        raise ValueError("Informe ao menos um documento-fonte")
    if copy_inputs:
        names = [source.name.casefold() for source in resolved_sources]
        if len(names) != len(set(names)):
            raise FileExistsError(
                "Fontes com o mesmo nome não podem ser copiadas para o mesmo input/"
            )

    job_id = allocate_job_id(root, year=year)
    job_dir = root / job_id
    job_dir.mkdir()
    for directory in JOB_SUBDIRECTORIES:
        (job_dir / directory).mkdir()

    source_records: list[dict[str, Any]] = []
    for source in resolved_sources:
        copied: Path | None = None
        if copy_inputs:
            copied = job_dir / "input" / source.name
            if copied.exists():
                raise FileExistsError(f"Colisão de nome em input/: {copied.name}")
            shutil.copy2(source, copied)
        source_records.append(_source_record(source, copied))

    now = utc_now()
    job = {
        "job_id": job_id,
        "schema_version": "0.2.0",
        "created_at": now,
        "updated_at": now,
        "state": "received",
        "status": "EM PROCESSAMENTO",
        "request": {
            "topic": topic.strip(),
            "requested_edition_type": requested_edition_type,
            "source_folder": source_folder,
            "editor": editor,
            "notes": notes,
        },
        "source_documents": source_records,
        "versions": {
            "system_version": SYSTEM_VERSION,
            "skill_version": SKILL_VERSION,
            "editorial_constitution_version": EDITORIAL_CONSTITUTION_VERSION,
            "edition_contract_version": "0.1.0-provisional",
            "methodology_rules_version": "0.1.0-provisional",
            "style_profile_version": "candidate-testes-0.1.0",
            "anti_ai_rules_version": "0.1.0-provisional",
            "corpus_version": "0.1.0-plus-testes-catalog",
            "design_system_version": "1.0.0-candidate-unverified",
            "model": None,
            "generation_date": now,
            "source_documents_hash": [record["sha256"] for record in source_records],
        },
        "gates": {
            "critical_errors": [],
            "document_validation_confirmed_by": None,
            "human_approval_required": True,
        },
        "history": [{"state": "received", "at": now, "actor": "system"}],
    }
    dump_data(job_dir / "job.yml", job)
    from .registry import sync_job_to_registry

    sync_job_to_registry(
        job_dir,
        actor_id="reviews-system",
        role="agent",
    )
    return job_dir


def load_job(job_dir: str | Path) -> dict[str, Any]:
    return load_data(Path(job_dir) / "job.yml")


def confirm_document_validation(job_dir: str | Path, reviewer: str) -> Path:
    """Registrar revisão humana dos documentos sem reescrever o resultado automático."""

    if not reviewer.strip():
        raise ValueError("Informe o responsável pela confirmação documental")
    root = Path(job_dir)
    validation_path = root / "normalized" / "document-validation.json"
    validation = load_data(validation_path)
    if validation.get("critical_errors"):
        raise RuntimeError("Há erros críticos de normalização; a validação não pode ser confirmada")
    manual_review_path = root / "normalized" / "manual-document-review.json"
    manual_review = load_data(manual_review_path)
    expected_inventory_hash = validation.get("document_inventory_sha256")
    if manual_review.get("document_inventory_sha256") != expected_inventory_hash:
        raise RuntimeError(
            "A revisão manual não corresponde ao inventário documental atual"
        )
    checks = manual_review.get("checks")
    if not isinstance(checks, dict):
        raise RuntimeError("manual-document-review.json não contém checks válidos")
    required_ids = {
        item["id"]
        for item in validation.get("manual_checks_required", [])
        if isinstance(item, dict) and item.get("id")
    }
    missing_confirmations = sorted(
        check_id
        for check_id in required_ids
        if not isinstance(checks.get(check_id), dict)
        or checks[check_id].get("confirmed") is not True
    )
    if missing_confirmations:
        raise RuntimeError(
            "Confirmações documentais pendentes: " + ", ".join(missing_confirmations)
        )
    now = utc_now()
    manual_review["review_status"] = "passed"
    manual_review["reviewer"] = reviewer.strip()
    manual_review["reviewed_at"] = now
    dump_data(manual_review_path, manual_review)
    validation["status"] = "passed"
    validation["confirmed_by"] = reviewer.strip()
    validation["confirmed_at"] = now
    dump_data(validation_path, validation)
    job = load_job(root)
    job["gates"]["document_validation_confirmed_by"] = reviewer.strip()
    job["updated_at"] = utc_now()
    dump_data(root / "job.yml", job)
    from .registry import sync_job_to_registry

    sync_job_to_registry(
        root,
        actor_id=reviewer.strip(),
        role="methodological_reviewer",
    )
    return validation_path


def validate_job_shape(job: dict[str, Any]) -> list[str]:
    schema_path = Path(__file__).resolve().parents[2] / "schemas" / "job.schema.json"
    schema = load_data(schema_path)
    errors = [
        f"{issue.path}: {issue.message}"
        for issue in validate(job, schema)
    ]
    if not JOB_PATTERN.match(str(job.get("job_id", ""))):
        errors.append("job_id inválido")
    if job.get("state") not in PIPELINE_STATES:
        errors.append("state inválido")
    request = job.get("request")
    if not isinstance(request, dict) or not str(request.get("topic", "")).strip():
        errors.append("request.topic ausente")
    sources = job.get("source_documents")
    if not isinstance(sources, list) or not sources:
        errors.append("source_documents deve conter ao menos uma fonte")
    else:
        for index, source in enumerate(sources):
            if not source.get("sha256") or not source.get("location"):
                errors.append(f"source_documents[{index}] sem location ou sha256")
    if not isinstance(job.get("history"), list):
        errors.append("history ausente")
    elif job["history"] and job["history"][-1].get("state") != job.get("state"):
        errors.append("history não termina no estado atual")
    return errors


def set_review_status(job_dir: str | Path, reviewer: str) -> Path:
    if not reviewer.strip():
        raise ValueError("Informe o revisor editorial")
    root = Path(job_dir)
    status_path = root / "final" / "review-status.json"
    dump_data(
        status_path,
        {"status": HUMAN_REVIEW_STATUS, "reviewer": reviewer.strip(), "recorded_at": utc_now()},
    )
    from .registry import sync_job_to_registry

    sync_job_to_registry(
        root,
        actor_id=reviewer.strip(),
        role="editorial_reviewer",
    )
    return status_path
