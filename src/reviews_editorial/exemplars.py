"""Recuperação limitada de exemplares aprovados do corpus."""

from __future__ import annotations

from typing import Any


def select_exemplars(
    manifest: dict[str, Any],
    *,
    edition_type: str,
    study_design: str | None = None,
    section: str | None = None,
    limit: int = 5,
) -> dict[str, Any]:
    candidates: list[tuple[int, dict[str, Any]]] = []
    for item in manifest.get("records", []):
        if item.get("classification_level") not in {"A", "B"}:
            continue
        if item.get("classification_status") != "approved":
            continue
        if item.get("holdout") is True:
            continue
        metadata = item.get("editorial_metadata") or {}
        score = 0
        if metadata.get("edition_type") == edition_type:
            score += 5
        if study_design and metadata.get("study_design") == study_design:
            score += 3
        if section and section in (metadata.get("sections") or []):
            score += 2
        if score:
            candidates.append((score, item))
    candidates.sort(key=lambda pair: (-pair[0], str(pair[1].get("record_id"))))
    selected = [item for _, item in candidates[: max(0, limit)]]
    return {
        "edition_type": edition_type,
        "study_design": study_design,
        "section": section,
        "selected": selected,
        "warning": None if selected else "Nenhum exemplar A/B aprovado corresponde aos filtros.",
        "selection_policy": (
            "Somente A/B aprovados, nunca holdout; limitações conhecidas acompanham cada "
            "exemplar e nenhum item é presumido perfeito."
        ),
    }
