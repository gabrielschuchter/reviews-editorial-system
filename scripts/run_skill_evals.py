from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from _bootstrap import REPO_ROOT
from reviews_editorial.orchestrator import select_capabilities
from reviews_editorial.skill_validation import REQUIRED_SKILLS, validate_skill_tree
from run_evals import evaluate_cases


DECLARATIVE_CASE_FIELDS = (
    "case_id",
    "kind",
    "prompt",
    "input",
    "expected_artifact",
    "acceptance_criteria",
)
DECLARATIVE_KINDS = frozenset({"positive", "negative", "boundary", "regression"})
OUTPUT_PATH_RE = re.compile(r"(?:^|\s)(?:[\w.-]+/)+[\w.-]+\.(?:json|md|docx)(?:\b|$)")

# A manifest can describe a runtime artifact that does not exist until a job is
# run. These local paths are the real, versioned contract/producer evidence for
# that artifact family. The evaluator verifies them without pretending to run
# an LLM or manufacture a document.
SKILL_CONTRACTS: dict[str, dict[str, tuple[str, ...]]] = {
    "reviews-writer": {
        "paths": ("scripts/orchestrate_reviews.py", "src/reviews_editorial/orchestrator.py"),
        "artifact_markers": ("capability-plan", "handoff"),
    },
    "reviews-source-provenance": {
        "paths": ("schemas/claim-provenance-report.schema.json", "scripts/validate_provenance.py"),
        "artifact_markers": ("claim-provenance-report", "missing-materials", "source-map", "critical-issues"),
    },
    "reviews-scientific-appraisal": {
        "paths": ("schemas/scientific-appraisal.schema.json", "scripts/validate_scientific_appraisal.py"),
        "artifact_markers": ("scientific-appraisal", "inference-boundaries", "methodological-review"),
    },
    "reviews-editorial-brief": {
        "paths": ("schemas/editorial-brief.schema.json", "scripts/edition_router.py"),
        "artifact_markers": ("editorial-brief", "title-options", "edition-routing", "selection-rationale"),
    },
    "reviews-journalistic-framing": {
        "paths": ("schemas/framing-memo.schema.json", "scripts/validate_framing.py"),
        "artifact_markers": ("framing-memo", "context-source-log", "journalistic-framing", "framing-handoff"),
    },
    "reviews-edition-writing": {
        "paths": ("scripts/audit_inference.py", "scripts/verify_numbers.py"),
        "artifact_markers": ("claim-coverage", "missing-information", "sensitive-claims", "tabela", "handoff"),
    },
    "reviews-anti-ai-writing": {
        "paths": ("schemas/anti-ai-report.schema.json", "scripts/audit_anti_ai.py"),
        "artifact_markers": ("anti-ai-report",),
    },
    "reviews-humanizer-ptbr": {
        "paths": ("schemas/humanization-diff.schema.json", "scripts/humanize_ptbr.py"),
        "artifact_markers": ("humanization-diff", "diff", "rejeição"),
    },
    "reviews-audit": {
        "paths": ("schemas/audit-report.schema.json", "scripts/audit_draft.py"),
        "artifact_markers": ("factual-audit", "finding", "coverage", "exceção"),
    },
    "reviews-document-presentation": {
        "paths": ("scripts/export_docx.py", "scripts/validate_tables.py"),
        "artifact_markers": ("candidate.docx", "presentation-audit", "presentation audit", "visual plan", "seletividade"),
    },
    "reviews-feedback-learning": {
        "paths": ("schemas/feedback.schema.json", "schemas/learning-pattern.schema.json", "scripts/incorporate_feedback.py"),
        "artifact_markers": ("version-comparison", "feedback-record", "feedback record", "learning-proposals", "regressão"),
    },
}


def _present(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return bool(value)
    return True


def _artifact_reference_is_declared(expected_artifact: object, markers: tuple[str, ...]) -> bool:
    if not isinstance(expected_artifact, str) or not expected_artifact.strip():
        return False
    lowered = expected_artifact.casefold()
    return bool(OUTPUT_PATH_RE.search(expected_artifact)) or any(marker.casefold() in lowered for marker in markers)


def _validate_contract_paths(repo_root: Path, paths: tuple[str, ...]) -> tuple[list[str], list[str]]:
    valid: list[str] = []
    issues: list[str] = []
    resolved_root = repo_root.resolve()
    for relative_path in paths:
        candidate = (resolved_root / relative_path).resolve()
        try:
            candidate.relative_to(resolved_root)
        except ValueError:
            issues.append(f"contrato fora do repositório: {relative_path}")
            continue
        if not candidate.is_file():
            issues.append(f"contrato/artefato de implementação inexistente: {relative_path}")
            continue
        valid.append(relative_path)
    return valid, issues


def evaluate_declarative_manifests(
    skills_root: str | Path,
    *,
    repo_root: str | Path = REPO_ROOT,
) -> dict[str, Any]:
    """Execute validações determinísticas dos manifests, sem executar geração por LLM.

    A unidade de execução é o contrato declarativo de cada caso: campos,
    categoria, critérios, referência de artefato e produtores/schemas locais.
    Isso prova que os 44 casos são utilizáveis como especificação de avaliação,
    mas não afirma que um modelo produziu a saída editorial esperada.
    """

    root = Path(skills_root).resolve()
    repository = Path(repo_root).resolve()
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    manifest_count = 0

    for skill_name in REQUIRED_SKILLS:
        skill_root = root / skill_name
        manifest_path = skill_root / "evals" / "cases.json"
        contract = SKILL_CONTRACTS.get(skill_name)
        skill_issues: list[str] = []
        cases: list[object] = []
        if contract is None:
            skill_issues.append("contrato determinístico não cadastrado para a skill")
            contract_paths: tuple[str, ...] = ()
            markers: tuple[str, ...] = ()
        else:
            contract_paths = contract["paths"]
            markers = contract["artifact_markers"]
        valid_paths, contract_issues = _validate_contract_paths(repository, contract_paths)
        skill_issues.extend(contract_issues)
        payload: dict[str, Any] | None = None
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
            if not isinstance(raw, dict):
                skill_issues.append("manifest deve ser um objeto JSON")
            else:
                payload = raw
                raw_cases = raw.get("cases")
                if not isinstance(raw_cases, list):
                    skill_issues.append("manifest.cases deve ser uma lista")
                else:
                    cases = raw_cases
        except (OSError, json.JSONDecodeError) as exc:
            skill_issues.append(f"manifest indisponível ou inválido: {exc}")

        if payload is not None:
            if payload.get("skill") != skill_name:
                skill_issues.append(f"manifest.skill esperado={skill_name!r}, obtido={payload.get('skill')!r}")
            if not _present(payload.get("version")):
                skill_issues.append("manifest.version ausente")

        kinds: set[str] = set()
        case_results: list[dict[str, Any]] = []
        for index, case in enumerate(cases, start=1):
            issues: list[str] = []
            if not isinstance(case, dict):
                case_results.append(
                    {
                        "case_index": index,
                        "case_id": None,
                        "passed": False,
                        "issues": ["caso deve ser um objeto JSON"],
                        "contract_paths": valid_paths,
                    }
                )
                continue
            case_id = str(case.get("case_id") or "")
            for field in DECLARATIVE_CASE_FIELDS:
                if not _present(case.get(field)):
                    issues.append(f"{field} ausente")
            kind = str(case.get("kind") or "")
            kinds.add(kind)
            if kind not in DECLARATIVE_KINDS:
                issues.append(f"kind inválido: {kind!r}")
            if not case_id:
                issues.append("case_id ausente")
            elif case_id in seen_ids:
                issues.append(f"case_id duplicado entre skills: {case_id}")
            else:
                seen_ids.add(case_id)
            criteria = case.get("acceptance_criteria")
            if not isinstance(criteria, list) or not criteria or not all(isinstance(item, str) and item.strip() for item in criteria):
                issues.append("acceptance_criteria deve ser lista não vazia de strings")
            if not _artifact_reference_is_declared(case.get("expected_artifact"), markers):
                issues.append("expected_artifact não referencia o contrato/artefato declarado pela skill")
            if not valid_paths:
                issues.append("nenhum produtor/schema local válido para o artefato esperado")
            case_results.append(
                {
                    "case_index": index,
                    "case_id": case_id or None,
                    "kind": kind or None,
                    "passed": not issues,
                    "issues": issues,
                    "expected_artifact": case.get("expected_artifact"),
                    "contract_paths": valid_paths,
                    "execution": "deterministic-manifest-contract",
                }
            )

        missing_kinds = sorted(DECLARATIVE_KINDS - kinds)
        if missing_kinds:
            skill_issues.append(f"tipos ausentes: {missing_kinds}")
        if len(case_results) < len(DECLARATIVE_KINDS):
            skill_issues.append("menos de quatro casos declarativos")
        manifest_count += 1 if payload is not None else 0
        results.append(
            {
                "skill": skill_name,
                "manifest": str(manifest_path.relative_to(repository)) if manifest_path.is_relative_to(repository) else str(manifest_path),
                "passed": not skill_issues and all(item["passed"] for item in case_results),
                "issues": skill_issues,
                "case_count": len(case_results),
                "kinds": sorted(kinds),
                "contract_paths": valid_paths,
                "cases": case_results,
            }
        )

    failed_cases = [
        {"skill": skill["skill"], "case_id": case["case_id"], "issues": case["issues"]}
        for skill in results
        for case in skill["cases"]
        if not case["passed"]
    ]
    failed_skills = [
        {"skill": item["skill"], "issues": item["issues"]}
        for item in results
        if item["issues"]
    ]
    total_cases = sum(item["case_count"] for item in results)
    expected_minimum = len(REQUIRED_SKILLS) * len(DECLARATIVE_KINDS)
    return {
        "passed": not failed_cases and not failed_skills and total_cases >= expected_minimum,
        "mode": "deterministic-manifest-contract",
        "llm_execution": False,
        "limitations": (
            "Não executa geração nem avalia qualidade semântica de LLM; valida contratos declarativos, "
            "critérios objetivos e produtores/schemas locais versionados."
        ),
        "manifest_count": manifest_count,
        "total_cases": total_cases,
        "minimum_required_cases": expected_minimum,
        "passed_cases": total_cases - len(failed_cases),
        "failed_cases": failed_cases,
        "failed_skills": failed_skills,
        "skills": results,
    }


def main() -> int:
    """Run repository-wide deterministic skill and capability regressions."""

    structure = validate_skill_tree(REPO_ROOT / ".codex" / "skills")
    declarative = evaluate_declarative_manifests(REPO_ROOT / ".codex" / "skills")
    regression = evaluate_cases(REPO_ROOT / "evals" / "cases")
    plan = select_capabilities({"stage": "full"})
    routed = [item["skill"] for item in plan["selected_capabilities"]]
    routing_passed = set(routed) == set(REQUIRED_SKILLS) and routed[0] == "reviews-writer"
    report = {
        "passed": structure["valid"] and declarative["passed"] and regression["passed"] and routing_passed,
        "skill_structure": structure,
        "declarative_manifest_contracts": declarative,
        "deterministic_regressions": {
            "total": regression["total"],
            "passed": regression["passed_count"],
            "failed": regression["failed_count"],
            "failed_cases": regression["failed_cases"],
        },
        "orchestrator_route": {
            "passed": routing_passed,
            "selected_skills": routed,
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
