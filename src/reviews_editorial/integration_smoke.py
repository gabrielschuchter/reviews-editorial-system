"""End-to-end fixture for the executable Reviews editorial workflow.

The fixture is intentionally synthetic and isolated in a temporary directory.
It does not claim to be a clinical publication: it proves that the real gates,
contracts and specialized validators can carry one documented job through to a
candidate that still awaits human publication approval.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from .anti_ai import audit_text
from .assurance import (
    EDITORIAL_BRIEF_FIELDS,
    audit_inference_text,
    validate_editorial_brief,
    validate_source_roles,
    validate_table_rows,
)
from .claims import audit_draft_text, build_claim_ledger, verify_number_records
from .documents import normalize_job_documents
from .export_docx import export_markdown_to_docx
from .feedback import compare_versions, validate_feedback
from .framing import validate_framing_memo
from .humanizer import humanize_text
from .io import dump_data, load_data, write_text
from .jobs import confirm_document_validation, create_job, load_job, utc_now
from .orchestrator import run_preflight, select_capabilities
from .pipeline import advance_job, validate_pipeline
from .provenance import validate_claim_provenance
from .scientific_appraisal import validate_scientific_appraisal
from .skill_validation import REQUIRED_SKILLS


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def _require(report: dict[str, Any], label: str) -> None:
    if not report.get("valid", report.get("passed")):
        raise RuntimeError(f"{label} falhou: {report}")


def _brief() -> dict[str, Any]:
    values: dict[str, Any] = {
        "edition_type": "primary-study-deep-dive",
        "primary_source": "DOC-SMOKE-1",
        "central_question": "Qual resultado foi observado na fonte de demonstração?",
        "reader": "profissional que precisa interpretar uma decisão localizada",
        "clinical_or_intellectual_decision": "não extrapolar o resultado além da população descrita",
        "editorial_angle": "apresentar o resultado com seu limite explícito",
        "why_now": "fixture de integração dos gates editoriais",
        "what_changed": "não se aplica; a fonte é demonstrativa",
        "central_tension": "o número é verificável, mas a aplicação continua limitada",
        "strongest_supported_takeaway": "o desfecho ocorreu em 10% dos 100 participantes da fonte",
        "most_important_uncertainty": "a fixture não estima aplicabilidade externa",
        "must_include": ["população", "resultado", "limite"],
        "must_not_claim": ["benefício clínico além do texto-fonte"],
        "context_needed": "trata-se de uma fonte sintética de teste, não evidência clínica publicável",
        "numbers_that_need_context": ["100 participantes", "10%"],
        "counterevidence_or_disagreement": "nenhuma fonte adicional é usada nesta fixture",
        "source_incentives_or_conflicts": "não aplicável à fixture sintética",
        "omissions_to_avoid": "não ocultar a natureza sintética nem transformar o número em recomendação",
        "headline_constraints": "título descritivo, sem promessa, cura ou superioridade",
        "lead_strategy": "abrir pelo resultado e por sua limitação",
        "nut_graf": "explicar fonte, população e limite de inferência",
        "ending_function": "encerrar na incerteza de aplicabilidade, sem recapitulação vazia",
    }
    missing = set(EDITORIAL_BRIEF_FIELDS) - set(values)
    if missing:
        raise AssertionError(f"brief de fixture sem campos: {sorted(missing)}")
    return values


def _scientific_appraisal(job_id: str) -> dict[str, Any]:
    source = {"document_id": "DOC-SMOKE-1", "locator": "p. 1, Resultados", "excerpt": "10 de 100 participantes"}
    rob_domains = [
        {"domain": name, "judgement": "low", "rationale": "Fixture documenta o julgamento para teste de contrato.", "evidence_spans": [source]}
        for name in (
            "randomization-process",
            "deviations-from-intended-interventions",
            "missing-outcome-data",
            "measurement-of-outcome",
            "selection-of-reported-result",
        )
    ]
    grade_domains = [
        {"domain": name, "judgement": "not-serious", "rationale": "Campo preenchido para testar rastreabilidade, não para afirmar conclusão científica."}
        for name in ("risk-of-bias", "inconsistency", "indirectness", "imprecision", "publication-bias")
    ]
    cross_cutting = {
        name: {"status": "addressed", "rationale": "Registrado na fixture de integração.", "sources": [source]}
        for name in ("multiplicity", "subgroups", "missing_data", "surrogate_outcomes", "causality", "applicability")
    }
    return {
        "appraisal_id": "APP-SMOKE-1",
        "job_id": job_id,
        "study_id": "STUDY-SMOKE-1",
        "design": "randomized-trial",
        "outcome_appraisals": [{
            "outcome_id": "OUT-SMOKE-1",
            "outcome_name": "Desfecho demonstrativo",
            "claim_classification": ["data", "result", "evidence", "inference"],
            "risk_of_bias": {"domains": rob_domains},
            "certainty": {"overall": "moderate", "domains": grade_domains},
            "clinical_relevance": {"absolute_effect": "10 eventos por 100 participantes na fonte de demonstração"},
            "sources": [source],
        }],
        "cross_cutting": cross_cutting,
        "recommendation_boundaries": [{
            "recommendation_text": "Não converter o resultado demonstrativo em recomendação clínica.",
            "strength": "conditional",
            "conditions": "Somente no escopo da fixture de integração.",
            "certainty_relation": "Registro de teste; julgamento final permanece humano.",
            "source_claim_ids": ["CLM-SMOKE-1"],
        }],
        "human_judgment_required": True,
        "provenance": {"reviewer": "integration-smoke", "reviewed_at": utc_now()},
    }


def _write_extraction_package(root: Path, source_id: str) -> Path:
    common = {
        "extraction_status": "validated",
        "validated_by": "integration-smoke",
        "validated_at": utc_now(),
        "source_documents": [source_id],
        "missing_information": [],
    }
    package = {
        "artifacts": {
            "study-overview.json": {**common, "study_id": "STUDY-SMOKE-1", "design": "randomized-trial", "primary_outcome": "desfecho demonstrativo"},
            "population.json": {**common, "population": "100 participantes", "randomized": 100, "analyzed": 100, "groups": ["grupo único de demonstração"]},
            "interventions.json": {**common, "interventions": ["conduta descrita na fonte"], "comparators": ["comparador descrito na fonte"]},
            "outcomes.json": {**common, "outcomes": [{"name": "desfecho demonstrativo", "locator": "p. 1"}]},
            "results.json": {**common, "results": [{"value": "10%", "locator": "p. 1, Resultados"}]},
            "safety.json": {**common, "safety_outcomes": [{"status": "não reportado na fonte sintética", "locator": "p. 1"}]},
            "missing-information.json": {**common, "items": []},
        }
    }
    path = root / "extraction-package.json"
    return dump_data(path, package)


def _advance(root: Path, state: str) -> None:
    report = advance_job(root, state, actor="integration-smoke")
    _require(report, f"gate {state}")


def run_full_job(workspace: str | Path) -> dict[str, Any]:
    """Run an isolated complete job up to candidate_for_review.

    It deliberately stops before ``human_review``/``approved``. The candidate is
    therefore evidence that automation reaches the proper human gate, not proof
    that a synthetic fixture can self-approve publication.
    """

    root = Path(workspace).resolve()
    root.mkdir(parents=True, exist_ok=True)
    source = root / "fixture-source.md"
    write_text(
        source,
        "# Fonte demonstrativa\n\nA fonte registra 100 participantes. O desfecho ocorreu em 10% dos participantes.\n",
    )
    job_dir = create_job(root / "jobs", [source], topic="Integração editorial demonstrativa", year=2026)
    job = load_job(job_dir)
    source_hash = str(job["source_documents"][0]["sha256"])
    source_id = str(job["source_documents"][0]["source_id"])

    normalize_job_documents(job_dir, [str(source)])
    review_path = job_dir / "normalized" / "manual-document-review.json"
    manual_review = load_data(review_path)
    for check in manual_review["checks"].values():
        check["confirmed"] = True
        check["notes"] = "Confirmado para fixture de integração; não é revisão de artigo real."
    dump_data(review_path, manual_review)
    confirm_document_validation(job_dir, "integration-smoke")
    _advance(job_dir, "documents_validated")
    _advance(job_dir, "document_package_normalized")

    dump_data(job_dir / "analysis" / "study-classification.json", {
        "study_id": "STUDY-SMOKE-1", "design": "randomized-trial", "reviewed_by": "integration-smoke", "source_document": "DOC-SMOKE-1",
    })
    _advance(job_dir, "study_classified")

    package_path = _write_extraction_package(root, source_id)
    subprocess.run(
        [sys.executable, str(REPOSITORY_ROOT / "scripts" / "extract_evidence.py"), str(job_dir), "--input", str(package_path)],
        check=True,
        capture_output=True,
        text=True,
    )
    _advance(job_dir, "evidence_extracted")

    number_verification = verify_number_records([{
        "record_id": "NUM-SMOKE-1", "reported_value": "10", "source_document": "DOC-SMOKE-1",
        "locator": "p. 1, Resultados", "unit": "%", "direction": "reported", "derived": False,
        "verification_status": "verified",
    }])
    _require(number_verification, "verificação numérica")
    dump_data(job_dir / "extraction" / "number-verification.json", number_verification)
    _advance(job_dir, "numbers_verified")

    claim = {
        "claim_id": "CLM-SMOKE-1", "job_id": job["job_id"],
        "claim_text": "Em 100 participantes, o desfecho ocorreu em 10%.", "claim_type": "result",
        "source_document": "DOC-SMOKE-1", "page": 1, "table": None, "figure": None,
        "section": "Resultados", "source_excerpt": "O desfecho ocorreu em 10% dos participantes.",
        "verification_status": "verified", "allowed_in_public_draft": True, "notes": "Fonte de demonstração.",
        "provenance": {"extracted_at": utc_now(), "extracted_by": "integration-smoke", "method": "leitura normalizada", "source_hash": source_hash},
    }
    ledger = build_claim_ledger([claim])
    _require(ledger["validation"], "claim ledger")
    dump_data(job_dir / "extraction" / "claim-ledger.json", ledger)
    _advance(job_dir, "claim_ledger_complete")

    source_roles = {"sources": [{
        "source_id": "DOC-SMOKE-1", "source_role": "primary-evidence", "authority_rank": 1,
        "location": str(source), "rationale": "Fonte local imutável da fixture; usada somente para testar rastreabilidade.",
    }]}
    _require(validate_source_roles(source_roles), "source roles")
    provenance = validate_claim_provenance(ledger, source_roles)
    _require(provenance, "proveniência por claim")
    dump_data(job_dir / "analysis" / "source-roles.json", source_roles)
    dump_data(job_dir / "analysis" / "claim-provenance-report.json", provenance)

    appraisal = _scientific_appraisal(job["job_id"])
    appraisal_validation = validate_scientific_appraisal(appraisal)
    _require(appraisal_validation, "appraisal científico")
    dump_data(job_dir / "analysis" / "scientific-appraisal.json", appraisal)
    dump_data(job_dir / "analysis" / "methodological-review.json", {
        "passed": True, "appraisal_id": appraisal["appraisal_id"], "outcomes_checked": appraisal_validation["outcomes_checked"],
        "human_judgment_required": True, "note": "Contratos metodológicos exercitados; decisão científica não foi automatizada.",
    })
    write_text(job_dir / "analysis" / "inference-boundaries.md", "A fixture não autoriza inferência clínica ou recomendação além da fonte demonstrativa.\n")
    write_text(job_dir / "analysis" / "critical-issues.md", "Nenhum erro crítico aberto na fixture após validação dos contratos.\n")
    _advance(job_dir, "methodology_complete")

    write_text(job_dir / "research" / "search-log.md", "Fixture isolada: nenhuma pesquisa externa é alegada ou necessária para a demonstração de pipeline.\n")
    write_text(job_dir / "research" / "external-scrutiny.md", "Não aplicável à fonte sintética; não declarar ausência de críticas de fonte real.\n")
    write_text(job_dir / "research" / "corrections-and-retractions.md", "Não aplicável à fonte sintética; verificação real exigiria busca documentada.\n")
    _advance(job_dir, "external_research_complete")

    brief = _brief()
    _require(validate_editorial_brief(brief), "brief editorial")
    dump_data(job_dir / "planning" / "editorial-brief.json", brief)
    framing = {
        "central_tension": brief["central_tension"], "reader_decision": brief["clinical_or_intellectual_decision"],
        "headline_options": [{"headline": "Resultado demonstrativo com limite explícito", "why_proportionate": "Descreve a fonte sem promessa.", "source_claim_ids": [claim["claim_id"]], "counterpoint": "Não permite aplicação clínica fora da fixture."}],
        "selected_angle": "resultado antes da interpretação", "counterpoint": "A fonte é sintética e não sustenta recomendação.",
        "evidence_boundary": "Apenas o claim ledger da fixture pode aparecer na candidata.",
        "must_not_imply": ["benefício clínico", "generalização", "aprovação automática"],
    }
    _require(validate_framing_memo(framing, claim_ids={claim["claim_id"]}), "framing jornalístico")
    dump_data(job_dir / "planning" / "framing-memo.json", framing)
    write_text(job_dir / "planning" / "edition-selection.md", "Tipo selecionado: primary-study-deep-dive, restrito à fixture.\n")
    write_text(job_dir / "planning" / "editorial-outline.md", "1. Resultado. 2. Limite. 3. Encerramento sem recomendação clínica.\n")
    dump_data(job_dir / "planning" / "selected-exemplars.yml", {"selected": [], "reason": "Não usar exemplar para uma fixture sintética."})
    write_text(job_dir / "planning" / "content-selection.md", "Usar somente CLM-SMOKE-1 e a incerteza explícita.\n")
    _advance(job_dir, "editorial_plan_complete")

    original_draft = "# Resultado demonstrativo\n\nUma síntese crítica das principais recomendações atualizadas.\n\nEm 100 participantes, o desfecho ocorreu em 10%.\n\nA fonte é sintética; o resultado não autoriza recomendação clínica.\n"
    write_text(job_dir / "drafts" / "v1-content.md", original_draft)
    _advance(job_dir, "first_draft")

    factual = audit_draft_text(original_draft, ledger)
    _require(factual, "auditoria factual")
    dump_data(job_dir / "audits" / "factual-audit.json", factual)
    _advance(job_dir, "factual_audit_complete")

    inference = audit_inference_text(original_draft)
    _require(inference, "auditoria de inferência")
    dump_data(job_dir / "audits" / "statistical-audit.json", {"passed": True, "number_verification": number_verification, "scope": "número e unidade rastreáveis"})
    dump_data(job_dir / "audits" / "methodological-audit.json", {"passed": True, "appraisal": appraisal_validation, "scope": "limites por desfecho documentados"})
    write_text(job_dir / "audits" / "statistical-audit.md", "O número 10% permanece associado à população de 100 participantes.\n")
    write_text(job_dir / "audits" / "methodological-audit.md", "A fixture mantém julgamento humano obrigatório e não calcula recomendação.\n")
    _advance(job_dir, "statistical_methodological_audit_complete")

    table_audit = validate_table_rows([{
        "recommendation": "Não extrapolar o resultado", "population": "100 participantes da fixture",
        "condition": "somente no documento demonstrativo", "action": "manter limite explícito",
    }])
    _require(table_audit, "auditoria estrutural de tabela")
    dump_data(job_dir / "audits" / "structural-audit.json", {"passed": True, "table_audit": table_audit, "scope": "estrutura e contexto da tabela"})
    write_text(job_dir / "drafts" / "v2-structure.md", original_draft)
    _advance(job_dir, "structural_review_complete")

    anti_ai = audit_text(original_draft, artifact_id="v2-structure")
    if anti_ai.get("passed") is not True:
        raise RuntimeError(f"auditoria anti-IA bloqueou a fixture: {anti_ai}")
    finding = next((item for item in anti_ai["findings"] if item["category"] == "self-importance-announcement"), None)
    if finding is None:
        raise RuntimeError("fixture não produziu o finding anti-IA esperado")
    humanized = humanize_text(
        original_draft,
        anti_ai,
        [{"finding_id": finding["finding_id"], "status": "confirmed", "reviewed_by": "integration-human-editor"}],
        claim_ledger=ledger,
    )
    if humanized.get("status") != "completed" or not humanized.get("unified_diff"):
        raise RuntimeError(f"humanizer não produziu diff confirmado: {humanized}")
    revised_draft = str(humanized["revised_text"])
    factual_after = audit_draft_text(revised_draft, ledger)
    _require(factual_after, "reauditoria factual pós-humanizer")
    dump_data(job_dir / "audits" / "style-audit.json", {"passed": True, "scope": "edição mínima confirmada", "humanization_id": humanized["humanization_id"]})
    dump_data(job_dir / "audits" / "anti-ai-audit.json", anti_ai)
    dump_data(job_dir / "audits" / "humanization-diff.json", humanized)
    write_text(job_dir / "drafts" / "v3-style.md", revised_draft)
    _advance(job_dir, "style_review_complete")

    dump_data(job_dir / "audits" / "coherence-audit.json", {"passed": True, "scope": "progressão resultado-limite", "findings": []})
    write_text(job_dir / "audits" / "coherence-audit.md", "A edição termina no limite de aplicabilidade e não recapitula o texto.\n")
    write_text(job_dir / "drafts" / "v4-candidate.md", revised_draft)
    _advance(job_dir, "coherence_review_complete")

    dump_data(job_dir / "audits" / "final-audit.json", {"passed": True, "factual": factual_after, "inference": inference, "open_critical_findings": []})
    _advance(job_dir, "final_audit_complete")

    final_markdown = job_dir / "final" / "candidate.md"
    write_text(final_markdown, revised_draft)
    presentation = export_markdown_to_docx(final_markdown, job_dir / "final" / "candidate.docx")
    if presentation.get("passed") is not True:
        raise RuntimeError(f"DOCX não passou auditoria: {presentation}")
    dump_data(job_dir / "final" / "presentation-audit.json", presentation)
    write_text(job_dir / "final" / "editorial-report.md", "Candidata sintética: claims, incerteza e aprovação humana permanecem rastreáveis.\n")
    dump_data(job_dir / "final" / "source-map.json", {"claims": [{"claim_id": claim["claim_id"], "source": "DOC-SMOKE-1", "locator": "p. 1, Resultados"}]})
    dump_data(job_dir / "final" / "quality-report.json", {"passed": True, "factual_audit": factual_after, "human_review_required": True})
    write_text(job_dir / "final" / "visual-plan.md", "Sem asset decorativo; a tabela e o limite textual são a apresentação da fixture.\n")
    _advance(job_dir, "candidate_for_review")

    feedback = compare_versions(original_draft, revised_draft)
    feedback_record = {
        "feedback_id": "FDB-SMOKE-1", "feedback_type": "anti-ai-correction", "reason": "Retirar autoqualificação confirmada.",
        "generalizable": False, "candidate_rule": None, "approval_status": "local-only",
    }
    feedback_validation = validate_feedback([feedback_record], repository_root=REPOSITORY_ROOT)
    _require(feedback_validation, "feedback local")
    dump_data(job_dir / "feedback" / "version-comparison.json", feedback)
    dump_data(job_dir / "feedback" / "learning-proposals.json", {"validation": feedback_validation, "automatic_rule_mutation_performed": False})

    plan = select_capabilities({"stage": "full"})
    selected = [item["skill"] for item in plan["selected_capabilities"]]
    if selected[0] != "reviews-writer" or set(selected) != set(REQUIRED_SKILLS):
        raise RuntimeError(f"orquestrador não encadeou as 11 skills: {selected}")
    preflight = run_preflight({"stage": "full", "job_dir": str(job_dir)})
    if not preflight["preflight_passed"]:
        raise RuntimeError(f"preflight final bloqueado: {preflight}")
    final_pipeline = validate_pipeline(job_dir)
    _require(final_pipeline, "pipeline final")
    validation_cli = subprocess.run(
        [sys.executable, str(REPOSITORY_ROOT / "scripts" / "validate_job.py"), str(job_dir)],
        check=False,
        capture_output=True,
        text=True,
    )
    if validation_cli.returncode != 0:
        raise RuntimeError(f"CLI validate_job bloqueou a candidata: {validation_cli.stderr or validation_cli.stdout}")
    completed_job = load_job(job_dir)
    if completed_job["state"] != "candidate_for_review":
        raise RuntimeError(f"estado inesperado: {completed_job['state']}")
    if completed_job["status"] != "AGUARDANDO REVISÃO EDITORIAL":
        raise RuntimeError("a fixture não preservou o gate de revisão humana")
    return {
        "passed": True,
        "job_dir": str(job_dir),
        "job_id": completed_job["job_id"],
        "state": completed_job["state"],
        "status": completed_job["status"],
        "states_completed": [entry["state"] for entry in completed_job["history"]],
        "skills_routed": selected,
        "humanizer": {"status": humanized["status"], "changes": humanized["summary"]["applied"], "diff": bool(humanized["unified_diff"])},
        "docx": presentation,
        "validate_job_cli": True,
        "pipeline": final_pipeline,
    }
