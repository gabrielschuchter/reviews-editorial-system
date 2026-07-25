"""Extração e normalização conservadora de documentos locais."""

from __future__ import annotations

import html
import io
import re
import zipfile
from pathlib import Path
from typing import Any, BinaryIO
from xml.etree import ElementTree as ET

from .io import dump_data, load_data, sha256_file, write_text

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
CP = "{http://schemas.openxmlformats.org/package/2006/metadata/core-properties}"
DC = "{http://purl.org/dc/elements/1.1/}"
DCTERMS = "{http://purl.org/dc/terms/}"


class DocumentNormalizationError(RuntimeError):
    """Falha explícita de normalização."""


def _xml_text(element: ET.Element) -> str:
    parts: list[str] = []
    for node in element.iter():
        if node.tag == f"{W}t" and node.text:
            parts.append(node.text)
        elif node.tag == f"{W}tab":
            parts.append("\t")
        elif node.tag == f"{W}br" and node.attrib.get(f"{W}type") != "page":
            parts.append("\n")
    return "".join(parts).strip()


def _core_properties(package: zipfile.ZipFile) -> dict[str, str | None]:
    result = {"title": None, "creator": None, "created": None, "modified": None}
    try:
        root = ET.fromstring(package.read("docProps/core.xml"))
    except (KeyError, ET.ParseError):
        return result
    mapping = {
        "title": f"{DC}title",
        "creator": f"{DC}creator",
        "created": f"{DCTERMS}created",
        "modified": f"{DCTERMS}modified",
    }
    for key, tag in mapping.items():
        node = root.find(tag)
        if node is not None and node.text:
            result[key] = node.text.strip() or None
    return result


def extract_docx(source: str | Path | bytes | BinaryIO) -> dict[str, Any]:
    """Extrair texto, estrutura e sinais de revisão sem estimar páginas inexistentes."""

    if isinstance(source, bytes):
        stream: str | Path | BinaryIO = io.BytesIO(source)
    else:
        stream = source
    with zipfile.ZipFile(stream) as package:
        try:
            root = ET.fromstring(package.read("word/document.xml"))
        except KeyError as exc:
            raise DocumentNormalizationError("DOCX sem word/document.xml") from exc
        body = root.find(f"{W}body")
        if body is None:
            raise DocumentNormalizationError("DOCX sem corpo legível")

        paragraphs: list[dict[str, Any]] = []
        tables: list[dict[str, Any]] = []
        text_blocks: list[str] = []
        explicit_breaks = 0
        red_runs = 0

        for child in body:
            if child.tag == f"{W}p":
                text = _xml_text(child)
                has_page_break = any(
                    node.tag in {f"{W}lastRenderedPageBreak", f"{W}br"}
                    and (
                        node.tag == f"{W}lastRenderedPageBreak"
                        or node.attrib.get(f"{W}type") == "page"
                    )
                    for node in child.iter()
                )
                if has_page_break:
                    explicit_breaks += 1
                for color in child.iter(f"{W}color"):
                    value = (color.attrib.get(f"{W}val") or "").upper()
                    if value in {"FF0000", "C00000", "E60000"}:
                        red_runs += 1
                paragraph = {
                    "paragraph": len(paragraphs) + 1,
                    "text": text,
                    "explicit_page_break_after": has_page_break,
                }
                paragraphs.append(paragraph)
                if text:
                    text_blocks.append(text)
            elif child.tag == f"{W}tbl":
                rows: list[list[str]] = []
                for row in child.findall(f"{W}tr"):
                    rows.append([_xml_text(cell) for cell in row.findall(f"{W}tc")])
                tables.append({"table": len(tables) + 1, "rows": rows})
                rendered = "\n".join("\t".join(cells) for cells in rows if any(cells))
                if rendered:
                    text_blocks.append(rendered)

        media = [name for name in package.namelist() if name.startswith("word/media/")]
        comments = 0
        try:
            comments_root = ET.fromstring(package.read("word/comments.xml"))
            comments = len(comments_root.findall(f"{W}comment"))
        except (KeyError, ET.ParseError):
            pass
        tracked_insertions = len(root.findall(f".//{W}ins"))
        tracked_deletions = len(root.findall(f".//{W}del"))

        return {
            "text": "\n\n".join(text_blocks).strip(),
            "paragraphs": paragraphs,
            "tables": tables,
            "figures": [
                {"figure": index + 1, "package_path": name}
                for index, name in enumerate(media)
            ],
            "core_properties": _core_properties(package),
            "pagination": {
                "status": "explicit-breaks-only" if explicit_breaks else "not-available",
                "explicit_break_count": explicit_breaks,
                "warning": (
                    "DOCX não preserva paginação confiável sem renderização; use índice de parágrafo "
                    "ou renderize antes de atribuir página a uma afirmação."
                ),
            },
            "review_signals": {
                "comments": comments,
                "tracked_insertions": tracked_insertions,
                "tracked_deletions": tracked_deletions,
                "red_runs": red_runs,
            },
        }


def _extract_pdf(path: Path) -> dict[str, Any]:
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise DocumentNormalizationError(
            "PDF requer o extra opcional: pip install -e .[documents]"
        ) from exc

    reader = PdfReader(str(path))
    pages: list[dict[str, Any]] = []
    blocks: list[str] = []
    warnings: list[str] = []
    for index, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if not text:
            warnings.append(f"Página {index} sem texto extraível; inspeção visual obrigatória.")
        pages.append({"page": index, "text": text})
        blocks.append(f"[[PAGE {index}]]\n{text}")
    return {
        "text": "\n\n".join(blocks).strip(),
        "pages": pages,
        "tables": [],
        "figures": [],
        "warnings": warnings,
        "pagination": {"status": "source-pages", "page_count": len(pages)},
    }


def _read_text(path: Path) -> str:
    payload = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252"):
        try:
            return payload.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise DocumentNormalizationError(f"Codificação textual não reconhecida: {path}")


def normalize_document(path: str | Path, output_dir: str | Path) -> dict[str, Any]:
    """Normalizar um documento e devolver metadados auditáveis."""

    source = Path(path).resolve()
    if not source.is_file():
        raise DocumentNormalizationError(f"Fonte não encontrada: {source}")
    suffix = source.suffix.lower()
    warnings: list[str] = []
    if suffix == ".docx":
        extracted = extract_docx(source)
        warnings.append(extracted["pagination"]["warning"])
    elif suffix == ".pdf":
        extracted = _extract_pdf(source)
        warnings.extend(extracted.get("warnings", []))
    elif suffix in {".md", ".mdx", ".txt"}:
        text = _read_text(source)
        extracted = {
            "text": text,
            "pages": [{"page": None, "text": text}],
            "tables": [],
            "figures": [],
            "pagination": {"status": "not-applicable"},
        }
    elif suffix in {".html", ".htm"}:
        raw = _read_text(source)
        text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        text = re.sub(r"[ \t]+", " ", text)
        extracted = {
            "text": text.strip(),
            "pages": [{"page": None, "text": text.strip()}],
            "tables": [],
            "figures": [],
            "pagination": {"status": "not-applicable"},
        }
    else:
        raise DocumentNormalizationError(f"Formato não suportado para normalização: {suffix}")

    destination = Path(output_dir)
    source_hash = sha256_file(source)
    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "-", source.stem).strip("-") or "document"
    normalized_path = destination / f"{safe_stem}-{source_hash[:12]}.txt"
    write_text(normalized_path, extracted["text"] + "\n")
    return {
        "source_path": str(source),
        "source_name": source.name,
        "source_sha256": source_hash,
        "format": suffix.lstrip("."),
        "normalized_path": str(normalized_path.resolve()),
        "pagination": extracted.get("pagination", {"status": "unknown"}),
        "paragraphs": extracted.get("paragraphs", []),
        "pages": extracted.get("pages", []),
        "tables": extracted.get("tables", []),
        "figures": extracted.get("figures", []),
        "core_properties": extracted.get("core_properties", {}),
        "review_signals": extracted.get("review_signals", {}),
        "warnings": warnings,
    }


def normalize_job_documents(job_dir: str | Path, source_paths: list[str]) -> dict[str, Any]:
    """Normalizar fontes e gerar todos os mapas obrigatórios do estado 3."""

    root = Path(job_dir).resolve()
    normalized_dir = root / "normalized"
    expected_by_path: dict[str, str] = {}
    job_path = root / "job.yml"
    if job_path.is_file():
        job = load_data(job_path)
        for source in job.get("source_documents", []):
            registered_path = source.get("job_copy") or source.get("location")
            if registered_path:
                expected_by_path[str(Path(registered_path).resolve())] = str(
                    source.get("sha256") or ""
                )
    records: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for raw_path in source_paths:
        resolved = str(Path(raw_path).resolve())
        if expected_by_path:
            expected_hash = expected_by_path.get(resolved)
            if not expected_hash:
                failures.append(
                    {
                        "source_path": raw_path,
                        "error": "fonte não registrada no job; normalização recusada",
                    }
                )
                continue
            try:
                current_hash = sha256_file(resolved)
            except OSError as exc:
                failures.append({"source_path": raw_path, "error": str(exc)})
                continue
            if current_hash != expected_hash:
                failures.append(
                    {
                        "source_path": raw_path,
                        "error": (
                            "hash da fonte diverge do registro imutável do job "
                            f"(esperado {expected_hash}, encontrado {current_hash})"
                        ),
                    }
                )
                continue
        try:
            records.append(normalize_document(raw_path, normalized_dir))
        except (OSError, DocumentNormalizationError, zipfile.BadZipFile) as exc:
            failures.append({"source_path": raw_path, "error": str(exc)})

    inventory = {
        "documents": [
            {
                key: record[key]
                for key in (
                    "source_path",
                    "source_name",
                    "source_sha256",
                    "format",
                    "normalized_path",
                    "pagination",
                    "core_properties",
                    "review_signals",
                    "warnings",
                )
            }
            for record in records
        ],
        "failures": failures,
    }
    page_map = {
        "documents": [
            {
                "source_name": record["source_name"],
                "pagination": record["pagination"],
                "pages": [
                    {"page": page.get("page"), "character_count": len(page.get("text", ""))}
                    for page in record.get("pages", [])
                ],
                "paragraphs": [
                    {
                        "paragraph": paragraph["paragraph"],
                        "explicit_page_break_after": paragraph["explicit_page_break_after"],
                    }
                    for paragraph in record.get("paragraphs", [])
                ],
            }
            for record in records
        ]
    }
    table_map = {
        "documents": [
            {"source_name": record["source_name"], "tables": record.get("tables", [])}
            for record in records
        ]
    }
    figure_map = {
        "documents": [
            {"source_name": record["source_name"], "figures": record.get("figures", [])}
            for record in records
        ]
    }
    validation = {
        "status": "requires_manual_review" if records else "blocked",
        "machine_checks": {
            "at_least_one_supported_document": bool(records),
            "all_requested_documents_normalized": not failures,
            "unreadable_pages_flagged": all(
                not any("sem texto extraível" in warning for warning in record["warnings"])
                for record in records
            ),
        },
        "manual_checks_required": [
            {"id": "complete_correct_article", "label": "artigo completo e versão correta"},
            {"id": "title_correspondence", "label": "correspondência de título entre materiais"},
            {"id": "supplement_protocol_registry", "label": "suplemento, protocolo e registro"},
            {"id": "tables_figures_legible", "label": "legibilidade das tabelas e figuras principais"},
            {"id": "duplicates_study_mix", "label": "duplicatas e mistura de estudos"},
            {
                "id": "pico_primary_outcome_identifiable",
                "label": "desfecho primário, intervenção e comparador identificáveis",
            },
        ],
        "critical_errors": failures,
    }

    inventory_path = dump_data(normalized_dir / "document-inventory.json", inventory)
    inventory_hash = sha256_file(inventory_path)
    validation["document_inventory_sha256"] = inventory_hash
    validation["manual_review_file"] = "normalized/manual-document-review.json"
    dump_data(normalized_dir / "page-map.json", page_map)
    dump_data(normalized_dir / "table-map.json", table_map)
    dump_data(normalized_dir / "figure-map.json", figure_map)
    dump_data(normalized_dir / "document-validation.json", validation)
    manual_review_path = normalized_dir / "manual-document-review.json"
    prior_review: dict[str, Any] = {}
    if manual_review_path.is_file():
        loaded = load_data(manual_review_path)
        if isinstance(loaded, dict):
            prior_review = loaded
    if prior_review.get("document_inventory_sha256") != inventory_hash:
        dump_data(
            manual_review_path,
            {
                "review_status": "pending",
                "document_inventory_sha256": inventory_hash,
                "checks": {
                    item["id"]: {
                        "confirmed": False,
                        "notes": None,
                    }
                    for item in validation["manual_checks_required"]
                },
                "reviewer": None,
                "reviewed_at": None,
            },
        )
    missing_lines = ["# Materiais ausentes ou pendentes", ""]
    if failures:
        missing_lines.extend(
            f"- `{item['source_path']}`: {item['error']}" for item in failures
        )
    else:
        missing_lines.append(
            "- Nenhuma falha automática de leitura. A presença de suplemento, protocolo, registro, "
            "errata e materiais de apoio ainda exige confirmação manual."
        )
    write_text(normalized_dir / "missing-materials.md", "\n".join(missing_lines) + "\n")
    return {"inventory": inventory, "validation": validation}
