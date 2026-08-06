"""Constantes versionadas do pipeline editorial."""

from __future__ import annotations

SYSTEM_VERSION = "0.4.1"
SKILL_VERSION = "0.3.1"
EDITORIAL_CONSTITUTION_VERSION = "0.1.0-provisional"

SOURCE_LEVELS = {
    "A": "canônico atual",
    "B": "referência próxima do ideal, com limitações conhecidas",
    "C": "publicado, mas histórico",
    "D": "material de discussão",
    "E": "legado ou desatualizado",
    "F": "excluído",
}

EDITION_TYPES = (
    "clinical-answer-classic",
    "clinical-answer-analytical",
    "guideline-summary",
    "systematic-review-critical",
    "clinical-protocol",
    "thematic-narrative",
    "primary-study-deep-dive",
)

STUDY_DESIGNS = (
    "randomized-trial",
    "nonrandomized-trial",
    "cohort",
    "case-control",
    "cross-sectional",
    "diagnostic",
    "prognostic",
    "systematic-review",
    "meta-analysis",
    "clinical-guideline",
    "narrative-review",
    "protocol",
    "other",
    "undetermined",
)

PIPELINE_STATES = (
    "received",
    "documents_validated",
    "document_package_normalized",
    "study_classified",
    "evidence_extracted",
    "numbers_verified",
    "claim_ledger_complete",
    "methodology_complete",
    "external_research_complete",
    "editorial_plan_complete",
    "first_draft",
    "factual_audit_complete",
    "statistical_methodological_audit_complete",
    "structural_review_complete",
    "style_review_complete",
    "coherence_review_complete",
    "final_audit_complete",
    "candidate_for_review",
    "human_review",
    "approved",
)

REQUIRED_OUTPUTS_BY_STATE = {
    "received": ("job.yml",),
    "documents_validated": (
        "normalized/document-validation.json",
        "normalized/manual-document-review.json",
    ),
    "document_package_normalized": (
        "normalized/document-inventory.json",
        "normalized/page-map.json",
        "normalized/table-map.json",
        "normalized/figure-map.json",
        "normalized/missing-materials.md",
    ),
    "study_classified": ("analysis/study-classification.json",),
    "evidence_extracted": (
        "extraction/study-overview.json",
        "extraction/population.json",
        "extraction/interventions.json",
        "extraction/outcomes.json",
        "extraction/results.json",
        "extraction/safety.json",
        "extraction/missing-information.json",
        "extraction/extraction-validation.json",
    ),
    "numbers_verified": ("extraction/number-verification.json",),
    "claim_ledger_complete": ("extraction/claim-ledger.json",),
    "methodology_complete": (
        "analysis/methodological-review.json",
        "analysis/inference-boundaries.md",
        "analysis/critical-issues.md",
    ),
    "external_research_complete": (
        "research/search-log.md",
        "research/external-scrutiny.md",
        "research/corrections-and-retractions.md",
    ),
    "editorial_plan_complete": (
        "planning/edition-selection.md",
        "planning/editorial-outline.md",
        "planning/selected-exemplars.yml",
        "planning/content-selection.md",
    ),
    "first_draft": ("drafts/v1-content.md",),
    "factual_audit_complete": ("audits/factual-audit.json",),
    "statistical_methodological_audit_complete": (
        "audits/statistical-audit.md",
        "audits/statistical-audit.json",
        "audits/methodological-audit.md",
        "audits/methodological-audit.json",
    ),
    "structural_review_complete": (
        "audits/structural-audit.json",
        "drafts/v2-structure.md",
    ),
    "style_review_complete": (
        "audits/style-audit.json",
        "audits/anti-ai-audit.json",
        "audits/strict-style-audit.json",
        "drafts/v3-style.md",
    ),
    "coherence_review_complete": (
        "audits/coherence-audit.md",
        "audits/coherence-audit.json",
        "drafts/v4-candidate.md",
    ),
    "final_audit_complete": (
        "audits/strict-style-final.json",
        "audits/final-audit.json",
    ),
    "candidate_for_review": (
        "final/candidate.md",
        "final/candidate.docx",
        "final/editorial-report.md",
        "final/source-map.json",
        "final/quality-report.json",
        "final/visual-plan.md",
    ),
    "human_review": ("final/review-status.json",),
    "approved": ("final/publication-approval.json",),
}

CRITICAL_AUDIT_STATUSES = {
    "unsupported",
    "divergent",
    "critical-error",
    "wrong-source",
    "wrong-effect-direction",
    "fabricated-reference",
}

HUMAN_REVIEW_STATUS = "AGUARDANDO REVISÃO EDITORIAL"
APPROVED_STATUS = "APROVADA PARA PUBLICAÇÃO"

MISSING_INFORMATION = "Informação não localizada nos materiais consultados."
AMBIGUOUS_INFORMATION = (
    "Informação ambígua ou insuficientemente descrita no material disponível."
)
