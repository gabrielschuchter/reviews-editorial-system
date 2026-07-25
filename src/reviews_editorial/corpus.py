"""Curadoria explícita do corpus sem promoção silenciosa."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .constants import SOURCE_LEVELS
from .io import load_data


def load_manifest_with_catalogs(path: str | Path) -> dict[str, Any]:
    """Carregar o manifesto e anexar catálogos curados sem duplicar registros."""

    manifest_path = Path(path).resolve()
    result = deepcopy(load_data(manifest_path))
    records = list(result.get("records", []))
    known_ids = {str(record.get("record_id")) for record in records}
    loaded_catalogs: list[str] = []
    for relative in result.get("curated_catalogs", []):
        catalog_path = (manifest_path.parent / str(relative)).resolve()
        catalog = load_data(catalog_path)
        for record in catalog.get("records", []):
            record_id = str(record.get("record_id") or "")
            if not record_id:
                raise ValueError(f"registro sem record_id em {catalog_path}")
            if record_id in known_ids:
                raise ValueError(f"record_id duplicado entre manifesto e catálogos: {record_id}")
            records.append(record)
            known_ids.add(record_id)
        loaded_catalogs.append(str(catalog_path))
    result["records"] = records
    result["loaded_curated_catalogs"] = loaded_catalogs
    result["effective_record_count"] = len(records)
    return result


def apply_classification_overrides(
    manifest: dict[str, Any], overrides: list[dict[str, Any]]
) -> dict[str, Any]:
    result = deepcopy(manifest)
    by_id = {record["record_id"]: record for record in result.get("records", [])}
    change_log = list(result.get("classification_changes", []))
    seen_override_ids: set[str] = set()
    for override in overrides:
        record_id = override.get("record_id")
        level = override.get("classification_level")
        if not isinstance(record_id, str) or not record_id:
            raise ValueError("todo override exige record_id")
        if record_id in seen_override_ids:
            raise ValueError(f"record_id repetido no mesmo lote de overrides: {record_id}")
        seen_override_ids.add(record_id)
        if record_id not in by_id:
            raise KeyError(f"record_id não encontrado: {record_id}")
        if level not in SOURCE_LEVELS:
            raise ValueError(f"nível inválido para {record_id}: {level}")
        approved_by = str(override.get("approved_by_editor") or "").strip()
        if level in {"A", "B"} and not approved_by:
            raise PermissionError(f"promoção de {record_id} para {level} exige approved_by_editor")
        if not str(override.get("reason") or "").strip():
            raise ValueError(f"override de {record_id} exige justificativa")
        if level == "B":
            quality_status = str(override.get("quality_status") or "").strip()
            limitations = override.get("known_limitations")
            if not quality_status:
                raise ValueError(f"referência B {record_id} exige quality_status")
            if not isinstance(limitations, list) or not all(
                isinstance(item, str) and item.strip() for item in limitations
            ):
                raise ValueError(
                    f"referência B {record_id} exige known_limitations como lista de textos"
                )
        record = by_id[record_id]
        previous = record.get("classification_level")
        record["classification_level"] = level
        record["classification_label"] = SOURCE_LEVELS[level]
        record["classification_status"] = "approved" if approved_by else "proposed"
        record["classification_approved_by"] = approved_by or None
        record["classification_approved_at"] = override.get("approved_at")
        record["rationale"] = override["reason"]
        if "quality_status" in override:
            record["quality_status"] = override["quality_status"]
        if "known_limitations" in override:
            record["known_limitations"] = list(override["known_limitations"])
        if "holdout" in override:
            record["holdout"] = bool(override["holdout"])
        if "editorial_metadata" in override:
            if not isinstance(override["editorial_metadata"], dict):
                raise ValueError(f"editorial_metadata inválido para {record_id}")
            record["editorial_metadata"] = deepcopy(override["editorial_metadata"])
        change_log.append(
            {
                "record_id": record_id,
                "from": previous,
                "to": level,
                "reason": override["reason"],
                "approved_by": approved_by or None,
                "approved_at": override.get("approved_at"),
                "holdout": bool(override.get("holdout", record.get("holdout", False))),
            }
        )
    result["classification_changes"] = change_log
    result["canonical_items"] = [
        record["record_id"]
        for record in result.get("records", [])
        if record.get("classification_level") == "A" and record.get("classification_status") == "approved"
    ]
    result["exemplar_items"] = [
        record["record_id"]
        for record in result.get("records", [])
        if record.get("classification_level") == "B" and record.get("classification_status") == "approved"
    ]
    result.pop("gold_items", None)
    result["holdout_items"] = [
        record["record_id"]
        for record in result.get("records", [])
        if record.get("holdout") is True
    ]
    result["counts_by_level"] = {
        level: sum(
            record.get("classification_level") == level
            for record in result.get("records", [])
        )
        for level in SOURCE_LEVELS
    }
    result["record_count"] = len(result.get("records", []))
    result["classification_status"] = (
        "partially-approved"
        if result["canonical_items"] or result["exemplar_items"]
        else "proposed-awaiting-editorial-approval"
    )
    return result
