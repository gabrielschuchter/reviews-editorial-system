"""Roteamento conservador e explicável de tipos de edição."""

from __future__ import annotations

from typing import Any

from .constants import EDITION_TYPES


def recommend_edition_type(context: dict[str, Any]) -> dict[str, Any]:
    requested = context.get("requested_edition_type")
    design = str(context.get("study_design") or "undetermined")
    article_count = int(context.get("article_count") or 1)
    objective = str(context.get("objective") or "clinical-answer")
    complexity = str(context.get("methodological_complexity") or "standard")
    conduct_supported = bool(context.get("conduct_level_supported"))
    critical_emphasis = bool(context.get("critical_analysis_priority"))

    incompatibility: str | None = None
    if requested:
        if requested not in EDITION_TYPES:
            raise ValueError(f"Tipo solicitado desconhecido: {requested}")
        if requested == "guideline-summary" and design != "clinical-guideline":
            incompatibility = "guideline-summary exige uma diretriz clínica confirmada"
        elif requested == "systematic-review-critical" and design not in {
            "systematic-review",
            "meta-analysis",
        }:
            incompatibility = "systematic-review-critical exige revisão sistemática ou metanálise"
        elif requested == "clinical-protocol" and not conduct_supported:
            incompatibility = "clinical-protocol exige fontes que sustentem orientação de conduta"
        if incompatibility is None:
            return {
                "selected_type": requested,
                "decision": "editor-explicit-choice",
                "rationale": "O tipo informado pelo editor foi respeitado.",
                "requires_editor_review": False,
                "override_allowed": True,
            }

    if design == "clinical-guideline":
        recommended = "guideline-summary"
        reason = "O documento central foi classificado como diretriz clínica."
    elif objective == "clinical-conduct" and conduct_supported:
        recommended = "clinical-protocol"
        reason = "O objetivo é orientar decisões e as fontes foram marcadas como suficientes para conduta."
    elif design in {"systematic-review", "meta-analysis"} and (
        critical_emphasis or complexity == "high"
    ):
        recommended = "systematic-review-critical"
        reason = "A síntese requer análise crítica aprofundada de revisão sistemática ou metanálise."
    elif article_count > 1 and design in {"undetermined", "narrative-review", "other"}:
        recommended = "thematic-narrative"
        reason = "Há múltiplas fontes sem um único estudo central confirmado."
    elif design in {
        "randomized-trial",
        "nonrandomized-trial",
        "cohort",
        "case-control",
        "cross-sectional",
        "diagnostic",
        "prognostic",
    } and complexity == "high":
        recommended = "primary-study-deep-dive"
        reason = "Um estudo primário central exige espaço metodológico maior."
    elif objective == "classic-clinical-answer":
        recommended = "clinical-answer-classic"
        reason = "O briefing solicitou a organização clássica de pergunta e resposta clínica."
    else:
        recommended = "clinical-answer-analytical"
        reason = "O modelo analítico reduz redundância e preserva métodos, achados e crítica em sequência."

    return {
        "selected_type": recommended,
        "decision": "system-recommendation",
        "rationale": reason,
        "requested_type_incompatibility": incompatibility,
        "requires_editor_review": bool(incompatibility),
        "override_allowed": True,
    }
