"""Capability selection and preflight for the Reviews editorial workflow.

The orchestrator does not generate or approve a publication.  It creates an
explicit, inspectable chain for a job and runs only deterministic preflight
checks that can be evidenced locally.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .assurance import validate_editorial_brief, validate_source_roles
from .edition_router import recommend_edition_type
from .io import load_data
from .pipeline import validate_pipeline


CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "skill": "reviews-source-provenance",
        "stage": "evidence",
        "consumes": ("source_documents",),
        "produces": ("normalized/document-inventory.json", "extraction/claim-ledger.json"),
        "stop_on": ("source unreadable", "source identity mismatch", "claim without locator"),
    },
    {
        "skill": "reviews-scientific-appraisal",
        "stage": "evidence",
        "consumes": ("extraction/claim-ledger.json", "analysis/study-classification.json"),
        "produces": ("analysis/methodological-review.json", "analysis/inference-boundaries.md"),
        "stop_on": ("critical risk of bias unresolved", "effect direction uncertain"),
    },
    {
        "skill": "reviews-editorial-brief",
        "stage": "planning",
        "consumes": ("claim ledger", "study classification", "editor request"),
        "produces": ("planning/editorial-brief.json",),
        "stop_on": ("central decision undefined", "must-not-claim absent"),
    },
    {
        "skill": "reviews-journalistic-framing",
        "stage": "planning",
        "consumes": ("planning/editorial-brief.json", "analysis/inference-boundaries.md"),
        "produces": ("planning/framing-memo.json", "planning/headline-options.json"),
        "stop_on": ("headline stronger than evidence", "counterpoint omitted"),
    },
    {
        "skill": "reviews-edition-writing",
        "stage": "writing",
        "consumes": ("planning/editorial-outline.md", "extraction/claim-ledger.json"),
        "produces": ("drafts/v1-content.md",),
        "stop_on": ("unsupported claim", "unresolved critical issue"),
    },
    {
        "skill": "reviews-anti-ai-writing",
        "stage": "style",
        "consumes": ("draft candidate",),
        "produces": ("audits/anti-ai-audit.json",),
        "stop_on": ("tool-token leak", "editorial contamination", "unreviewed critical finding"),
    },
    {
        "skill": "reviews-humanizer-ptbr",
        "stage": "style",
        "consumes": ("confirmed anti-AI findings", "claim ledger", "draft candidate"),
        "produces": ("audits/humanization-diff.json", "audits/humanization-claim-reaudit.json"),
        "stop_on": ("protected factual token would change", "change is not localized"),
    },
    {
        "skill": "reviews-audit",
        "stage": "audit",
        "consumes": ("draft candidate", "claim ledger", "methodological review"),
        "produces": ("audits/factual-audit.json", "audits/final-audit.json"),
        "stop_on": ("critical finding", "audit evidence missing"),
    },
    {
        "skill": "reviews-document-presentation",
        "stage": "presentation",
        "consumes": ("final/candidate.md", "visual plan"),
        "produces": ("final/candidate.docx", "final/presentation-audit.json"),
        "stop_on": ("rendering unavailable", "table condition lost", "mobile layout unreadable"),
    },
    {
        "skill": "reviews-feedback-learning",
        "stage": "learning",
        "consumes": ("candidate", "human revision", "feedback classification"),
        "produces": ("feedback/version-comparison.json", "feedback/learning-proposals.json"),
        "stop_on": ("attempted automatic promotion", "regression missing"),
    },
)

STAGE_ALIASES = {
    "full": {"evidence", "planning", "writing", "style", "audit", "presentation", "learning"},
    "evidence": {"evidence"},
    "planning": {"evidence", "planning"},
    "writing": {"evidence", "planning", "writing"},
    "audit": {"audit", "style"},
    "presentation": {"presentation"},
    "learning": {"learning"},
}


def select_capabilities(context: dict[str, Any]) -> dict[str, Any]:
    """Return an ordered, inspectable capability chain for one request."""

    requested_stage = str(context.get("stage") or "full").casefold()
    if requested_stage not in STAGE_ALIASES:
        raise ValueError(f"stage desconhecido: {requested_stage}")
    selected_stages = STAGE_ALIASES[requested_stage]
    explicit = context.get("only_skills")
    if explicit is not None and not isinstance(explicit, list):
        raise ValueError("only_skills deve ser lista quando informado")
    explicit_set = {str(item) for item in explicit or []}
    known = {item["skill"] for item in CAPABILITIES}
    unknown = sorted(explicit_set - known)
    if unknown:
        raise ValueError(f"skill desconhecida: {unknown}")
    selected = [
        item for item in CAPABILITIES
        if item["stage"] in selected_stages and (not explicit_set or item["skill"] in explicit_set)
    ]
    if requested_stage == "full":
        selected.insert(
            0,
            {
                "skill": "reviews-writer",
                "stage": "orchestration",
                "consumes": ("request", "job.yml"),
                "produces": ("planning/capability-plan.json",),
                "stop_on": ("required source missing", "preflight gate failed"),
            },
        )
    return {
        "orchestrator_version": "1.0.0",
        "stage": requested_stage,
        "selected_capabilities": selected,
        "selection_rationale": "Ordem fixa: evidência antes de framing e redação; auditoria independente antes de apresentação; aprendizado nunca promove regra automaticamente.",
        "human_approval_required": True,
    }


def _load_optional(path_value: Any) -> Any | None:
    if not path_value:
        return None
    path = Path(str(path_value))
    if not path.is_file():
        raise FileNotFoundError(f"artefato de preflight não encontrado: {path}")
    return load_data(path)


def run_preflight(context: dict[str, Any]) -> dict[str, Any]:
    """Run deterministic preflight checks without generating editorial prose."""

    plan = select_capabilities(context)
    checks: list[dict[str, Any]] = []
    blocked: list[str] = []
    brief = _load_optional(context.get("editorial_brief"))
    if brief is not None:
        result = validate_editorial_brief(brief)
        checks.append({"check": "editorial-brief", **result})
        if not result["valid"]:
            blocked.append("editorial brief incompleto")
    roles = _load_optional(context.get("source_roles"))
    if roles is not None:
        result = validate_source_roles(roles)
        checks.append({"check": "source-roles", **result})
        if not result["valid"]:
            blocked.append("papéis de fonte inválidos")
    routing_context = context.get("routing_context")
    if routing_context is not None:
        if not isinstance(routing_context, dict):
            raise ValueError("routing_context deve ser objeto")
        result = recommend_edition_type(routing_context)
        checks.append({"check": "edition-routing", "valid": not result["requires_editor_review"], "result": result})
        if result["requires_editor_review"]:
            blocked.append("tipo de edição solicitado é incompatível com a fonte")
    job_dir = context.get("job_dir")
    if job_dir:
        report = validate_pipeline(job_dir)
        checks.append({"check": "job-pipeline", **report})
        if not report["valid"]:
            blocked.extend(report["errors"])
    return {
        **plan,
        "preflight_passed": not blocked,
        "blocked_reasons": sorted(set(blocked)),
        "checks": checks,
        "next_action": "criar os artefatos da próxima capability" if not blocked else "resolver os gates antes de redigir",
    }
