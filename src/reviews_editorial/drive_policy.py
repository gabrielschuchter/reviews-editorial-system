"""Contrato local para preparar entregas ao conector do Google Drive."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import load_data, sha256_file


TRANSFERABLE_JOB_STATES = frozenset(
    {"candidate_for_review", "human_review", "approved"}
)


def prepare_drive_transfer(
    candidate: str | Path,
    *,
    job_dir: str | Path,
    destination_folder_id: str,
    authorized_production_folder_ids: list[str],
    source_archive_folder_ids: list[str],
    job_id: str,
    version: str,
) -> dict[str, Any]:
    path = Path(candidate).resolve()
    root = Path(job_dir).resolve()
    if not path.is_file():
        raise FileNotFoundError(path)
    if not root.is_dir():
        raise NotADirectoryError(root)

    final_dir = (root / "final").resolve()
    try:
        path.relative_to(final_dir)
    except ValueError as exc:
        raise PermissionError(
            f"O candidato deve estar dentro de {final_dir}"
        ) from exc

    job_manifest_path = root / "job.yml"
    if not job_manifest_path.is_file():
        raise FileNotFoundError(job_manifest_path)
    job = load_data(job_manifest_path)
    if not isinstance(job, dict):
        raise ValueError(f"{job_manifest_path} deve conter um objeto")

    requested_job_id = job_id.strip()
    manifest_job_id = str(job.get("job_id") or "").strip()
    if not requested_job_id:
        raise ValueError("job_id é obrigatório")
    if manifest_job_id != requested_job_id or root.name != requested_job_id:
        raise ValueError(
            "job_id não confere com job.yml e com o diretório do job"
        )

    job_state = str(job.get("state") or "").strip()
    if job_state not in TRANSFERABLE_JOB_STATES:
        allowed = ", ".join(sorted(TRANSFERABLE_JOB_STATES))
        raise PermissionError(
            f"O estado {job_state or '<vazio>'!r} não permite transferência; "
            f"use um destes: {allowed}"
        )

    destination = destination_folder_id.strip()
    if not destination:
        raise ValueError("destination_folder_id é obrigatório")
    authorized_destinations = {
        folder_id.strip()
        for folder_id in authorized_production_folder_ids
        if folder_id.strip()
    }
    if destination not in authorized_destinations:
        raise PermissionError(
            "O destino não está em authorized_production_folder_ids"
        )
    forbidden_sources = {
        folder_id.strip()
        for folder_id in source_archive_folder_ids
        if folder_id.strip()
    }
    if destination in forbidden_sources:
        raise PermissionError("O destino coincide com uma pasta-fonte histórica")
    return {
        "operation": "connector-import-required",
        "performed": False,
        "source_file": str(path),
        "source_sha256": sha256_file(path),
        "destination_folder_id": destination,
        "authorized_production_folder_ids": sorted(authorized_destinations),
        "forbidden_source_archive_folder_ids": sorted(forbidden_sources),
        "job_id": requested_job_id,
        "job_state": job_state,
        "requested_title": f"{requested_job_id} - candidata - {version}",
        "upload_mode": "native_google_docs" if path.suffix.lower() == ".docx" else "raw-file",
        "overwrite_existing": False,
        "post_write_verification_required": True,
        "connector_instructions": [
            "Importar como novo arquivo; nunca substituir documento histórico.",
            "Mover/adicionar o arquivo somente à pasta de produção autorizada.",
            "Reler metadados e registrar o ID/URL realmente retornado.",
            "Manter status AGUARDANDO REVISÃO EDITORIAL.",
        ],
    }
