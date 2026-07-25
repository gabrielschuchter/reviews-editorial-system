"""Inventário reprodutível de fontes locais, ZIPs e snapshots do Drive."""

from __future__ import annotations

import csv
import io
import re
import unicodedata
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from xml.etree.ElementTree import ParseError

from .constants import SOURCE_LEVELS
from .documents import DocumentNormalizationError, extract_docx
from .io import dump_data, load_data, sha256_bytes, sha256_file

INVENTORY_FIELDS = (
    "record_id",
    "source_system",
    "source_container",
    "item_path",
    "item_name",
    "item_kind",
    "format",
    "size_bytes",
    "created_at",
    "modified_at",
    "source_id",
    "web_url",
    "sha256",
    "text_sha256",
    "classification_level",
    "classification_label",
    "classification_status",
    "proposed_category",
    "editorial_status",
    "duplicate_of",
    "article_association",
    "inspection_scope",
    "rationale",
    "warnings",
)


def normalized_text_hash(text: str) -> str | None:
    normalized = unicodedata.normalize("NFKC", text).casefold()
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return sha256_bytes(normalized.encode("utf-8")) if normalized else None


def _name_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return value.casefold().replace("\\", "/")


def propose_level(path: str, *, item_kind: str = "file", category: str = "") -> tuple[str, str]:
    """Propor nível conservador; nunca promover automaticamente a A ou B."""

    key = _name_key(path)
    category_key = _name_key(category)
    if item_kind == "folder":
        return "F", "Pasta estrutural; não é conteúdo editorial."
    if any(token in key for token in ("testes-antigos", "testes/antigos", "versoes antigas")):
        return "E", "Localização explicitamente histórica ou de teste."
    if any(
        token in key
        for token in (
            "prompt antigo",
            "meta-prompt coringa teste",
            "memorias chatgpt",
            "preferencias claude",
            "teste 1",
        )
    ):
        return "E", "Nome identifica teste, memória de ferramenta ou versão antiga."
    if "archive" in category_key or "archived" in category_key:
        return "E", "Snapshot do Drive propõe referência arquivada; requer confirmação editorial."
    if "[publicad" in key:
        return "C", "Nome marca publicação, mas o material permanece histórico até curadoria."
    if "/publicados/" in f"/{key}/" and "revisando" not in key:
        return "D", "Está na área Publicados, que contém status mistos; publicação não foi presumida."
    if any(token in key for token in (".png", ".jpg", ".jpeg", ".mp4")):
        return "D", "Ativo visual ou gravação potencialmente útil, ainda não aprovado como regra."
    return "D", "Material fornecido para descoberta; influência normativa depende de aprovação humana."


def _zip_timestamp(info: zipfile.ZipInfo) -> str:
    try:
        return datetime(*info.date_time).isoformat()
    except (TypeError, ValueError):
        return ""


def scan_zip(path: str | Path) -> list[dict[str, Any]]:
    archive_path = Path(path).resolve()
    archive_hash = sha256_file(archive_path)
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(archive_path) as archive:
        for index, info in enumerate(archive.infolist(), start=1):
            if info.is_dir():
                continue
            payload = archive.read(info)
            suffix = Path(info.filename).suffix.lower().lstrip(".")
            text_hash: str | None = None
            warnings: list[str] = []
            inspection_scope = "metadata-and-binary-hash"
            review_signals: dict[str, Any] = {}
            if suffix == "docx":
                try:
                    extracted = extract_docx(payload)
                    text_hash = normalized_text_hash(extracted["text"])
                    review_signals = extracted.get("review_signals", {})
                    inspection_scope = "metadata-hash-and-docx-text"
                    if review_signals.get("comments"):
                        warnings.append(f"{review_signals['comments']} comentário(s) Word")
                    if review_signals.get("red_runs"):
                        warnings.append("contém trechos com formatação vermelha")
                    if review_signals.get("tracked_insertions") or review_signals.get("tracked_deletions"):
                        warnings.append("contém alterações rastreadas")
                except (zipfile.BadZipFile, DocumentNormalizationError, ParseError) as exc:
                    warnings.append(f"texto DOCX não extraído: {exc}")
            level, rationale = propose_level(info.filename)
            rows.append(
                {
                    "record_id": f"zip:{archive_hash[:12]}:{index:04d}",
                    "source_system": "local-zip",
                    "source_container": str(archive_path),
                    "item_path": info.filename.replace("\\", "/"),
                    "item_name": Path(info.filename).name,
                    "item_kind": "file",
                    "format": suffix,
                    "size_bytes": info.file_size,
                    "created_at": "",
                    "modified_at": _zip_timestamp(info),
                    "source_id": f"{archive_hash}:{info.CRC:08x}",
                    "web_url": "",
                    "sha256": sha256_bytes(payload),
                    "text_sha256": text_hash or "",
                    "classification_level": level,
                    "classification_label": SOURCE_LEVELS[level],
                    "classification_status": "proposed",
                    "proposed_category": "local-archive-item",
                    "editorial_status": "unknown",
                    "duplicate_of": "",
                    "article_association": "unresolved-no-source-article-confirmed",
                    "inspection_scope": inspection_scope,
                    "rationale": rationale,
                    "warnings": "; ".join(warnings),
                }
            )
    return rows
def scan_local_file(path: str | Path) -> dict[str, Any]:
    source = Path(path).resolve()
    suffix = source.suffix.lower().lstrip(".")
    level, rationale = propose_level(source.name)
    return {
        "record_id": f"local:{sha256_file(source)[:16]}",
        "source_system": "local-file",
        "source_container": str(source.parent),
        "item_path": str(source),
        "item_name": source.name,
        "item_kind": "file",
        "format": suffix,
        "size_bytes": source.stat().st_size,
        "created_at": "",
        "modified_at": datetime.fromtimestamp(source.stat().st_mtime).isoformat(),
        "source_id": "",
        "web_url": "",
        "sha256": sha256_file(source),
        "text_sha256": "",
        "classification_level": level,
        "classification_label": SOURCE_LEVELS[level],
        "classification_status": "proposed",
        "proposed_category": "design-system-documentation" if "design" in _name_key(source.name) else "local-file",
        "editorial_status": "unknown",
        "duplicate_of": "",
        "article_association": "not-applicable",
        "inspection_scope": "metadata-and-binary-hash",
        "rationale": rationale,
        "warnings": "",
    }


def rows_from_drive_snapshot(path: str | Path) -> list[dict[str, Any]]:
    snapshot = load_data(path)
    rows: list[dict[str, Any]] = []
    for item in snapshot.get("items", []):
        proposed = item.get("proposed_classification") or {}
        category = str(proposed.get("category") or "drive-item")
        level, rationale = propose_level(
            str(item.get("path") or item.get("name") or ""),
            item_kind=str(item.get("item_kind") or "file"),
            category=category,
        )
        if proposed.get("rationale"):
            rationale = f"{rationale} Snapshot: {proposed['rationale']}"
        rows.append(
            {
                "record_id": f"drive:{item.get('id')}",
                "source_system": "google-drive",
                "source_container": item.get("source_root_name", ""),
                "item_path": item.get("path", ""),
                "item_name": item.get("name", ""),
                "item_kind": item.get("item_kind", "file"),
                "format": item.get("mime_type", ""),
                "size_bytes": item.get("size_bytes") if item.get("size_bytes") is not None else "",
                "created_at": item.get("created_time", ""),
                "modified_at": item.get("modified_time", ""),
                "source_id": item.get("id", ""),
                "web_url": item.get("web_url", ""),
                "sha256": "",
                "text_sha256": "",
                "classification_level": level,
                "classification_label": SOURCE_LEVELS[level],
                "classification_status": "proposed",
                "proposed_category": category,
                "editorial_status": "published-name-marker" if "[publicad" in _name_key(item.get("name", "")) else "unverified",
                "duplicate_of": "",
                "article_association": "unresolved-metadata-only",
                "inspection_scope": "drive-metadata" + ("-and-selected-text" if category in {
                    "design_system_documentation",
                    "editorial_taxonomy_and_planning",
                    "governance_document_current_candidate",
                    "operational_procedure_current_candidate",
                } else ""),
                "rationale": rationale,
                "warnings": "; ".join(item.get("metadata_missing_from_connector_result") or []),
            }
        )
    return rows


def mark_duplicates(rows: list[dict[str, Any]]) -> None:
    """Marcar duplicatas exatas e textuais sem apagar nenhum registro."""

    for key in ("sha256", "text_sha256"):
        seen: dict[str, str] = {}
        for row in sorted(rows, key=lambda item: (item["source_system"], item["item_path"])):
            fingerprint = str(row.get(key) or "")
            if not fingerprint:
                continue
            if fingerprint in seen:
                row["duplicate_of"] = seen[fingerprint]
                row["classification_level"] = "F"
                row["classification_label"] = SOURCE_LEVELS["F"]
                row["rationale"] = (
                    f"Duplicata {'binária' if key == 'sha256' else 'textual'} de "
                    f"{seen[fingerprint]}; mantida apenas para rastreabilidade."
                )
            else:
                seen[fingerprint] = row["record_id"]


def write_inventory(
    rows: Iterable[dict[str, Any]], csv_path: str | Path, manifest_path: str | Path
) -> dict[str, Any]:
    materialized = list(rows)
    mark_duplicates(materialized)
    target = Path(csv_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=INVENTORY_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(materialized)
    counts: dict[str, int] = {level: 0 for level in SOURCE_LEVELS}
    for row in materialized:
        counts[row["classification_level"]] += 1
    manifest = {
        "manifest_version": "0.1.0",
        "classification_status": "proposed-awaiting-editorial-approval",
        "canonical_items": [],
        "exemplar_items": [],
        "holdout_items": [],
        "curated_catalogs": [],
        "counts_by_level": counts,
        "record_count": len(materialized),
        "records": materialized,
        "notes": [
            "Nenhum item foi promovido automaticamente a A ou B.",
            "Associação entre edição e artigo permanece não resolvida quando o artigo-fonte não foi fornecido.",
            "Duplicatas são preservadas no inventário e classificadas como F para evitar influência editorial.",
        ],
    }
    dump_data(manifest_path, manifest)
    return manifest
