from __future__ import annotations

import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.corpus import load_manifest_with_catalogs
from reviews_editorial.exemplars import select_exemplars
from reviews_editorial.io import load_data
from reviews_editorial.jobs import validate_job_shape
from reviews_editorial.skill_validation import validate_skill_tree
from run_evals import evaluate_cases

REQUIRED_ROOT_FILES = (
    "AGENTS.md",
    "README.md",
    "README-OPERACIONAL.md",
    "CHANGELOG.md",
    "DISCOVERY_REPORT.md",
    "SOURCE_INVENTORY.csv",
    "EDITORIAL_DECISIONS_PENDING.md",
    "IMPLEMENTATION_PLAN.md",
    "CONTINUATION_HANDOFF.md",
    ".codex/skills/reviews-writer/SKILL.md",
    ".codex/skills/reviews-writer/agents/openai.yaml",
    "corpus/testes-learning-catalog.yml",
    "editorial/style/style-profile-testes-candidate.json",
    "evals/cases/holdout-exclusion.json",
)


def main() -> int:
    issues = []
    for relative in REQUIRED_ROOT_FILES:
        path = REPO_ROOT / relative
        if not path.is_file() or path.stat().st_size == 0:
            issues.append(f"arquivo obrigatório ausente ou vazio: {relative}")
    schema_files = sorted((REPO_ROOT / "schemas").glob("*.schema.json"))
    required_schema_names = {
        "source-roles.schema.json",
        "editorial-brief.schema.json",
        "audit-report.schema.json",
        "learning-pattern.schema.json",
    }
    schema_names = {path.name for path in schema_files}
    if len(schema_files) < 17 or not required_schema_names.issubset(schema_names):
        issues.append(f"schemas modulares ausentes ou incompletos; encontrados {len(schema_files)}")
    ids = set()
    for path in schema_files:
        try:
            schema = json.loads(path.read_text(encoding="utf-8-sig"))
        except json.JSONDecodeError as exc:
            issues.append(f"schema JSON inválido {path.name}: {exc}")
            continue
        if schema.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
            issues.append(f"draft incorreto: {path.name}")
        if not schema.get("$id") or schema["$id"] in ids:
            issues.append(f"$id ausente ou duplicado: {path.name}")
        ids.add(schema.get("$id"))
    skill = REPO_ROOT / ".codex" / "skills" / "reviews-writer" / "SKILL.md"
    if skill.is_file() and "TODO" in skill.read_text(encoding="utf-8"):
        issues.append("SKILL.md ainda contém TODO")
    for path in list((REPO_ROOT / "src").rglob("*.py")) + list((REPO_ROOT / "scripts").glob("*.py")):
        try:
            compile(path.read_text(encoding="utf-8-sig"), str(path), "exec")
        except (SyntaxError, UnicodeError) as exc:
            issues.append(f"Python inválido {path.relative_to(REPO_ROOT)}: {exc}")

    try:
        template_job = load_data(REPO_ROOT / "jobs" / "JOB-YYYY-NNN" / "job.yml")
        for issue in validate_job_shape(template_job):
            issues.append(f"template de job inválido: {issue}")
    except (OSError, ValueError) as exc:
        issues.append(f"não foi possível validar o template de job: {exc}")

    corpus_summary = {"effective_records": 0, "approved_exemplars": 0, "holdouts": 0}
    try:
        manifest = load_manifest_with_catalogs(REPO_ROOT / "corpus" / "manifest.yml")
        approved = [
            record
            for record in manifest.get("records", [])
            if record.get("classification_level") == "B"
            and record.get("classification_status") == "approved"
        ]
        holdouts = [record for record in approved if record.get("holdout") is True]
        corpus_summary = {
            "effective_records": len(manifest.get("records", [])),
            "approved_exemplars": len(approved),
            "holdouts": len(holdouts),
        }
        if len(approved) != 7:
            issues.append(f"catálogo Testes deveria conter 7 exemplares B aprovados; contém {len(approved)}")
        if len(holdouts) != 1:
            issues.append(f"catálogo Testes deveria reservar 1 holdout; contém {len(holdouts)}")
        for record in approved:
            if record.get("quality_status") != "near-ideal-with-known-limitations":
                issues.append(f"exemplar sem limite de qualidade explícito: {record.get('record_id')}")
            if not record.get("known_limitations"):
                issues.append(f"exemplar sem limitações conhecidas: {record.get('record_id')}")
        selection = select_exemplars(
            manifest,
            edition_type="guideline-summary",
            study_design="clinical-guideline",
            limit=20,
        )
        selected_ids = {record.get("record_id") for record in selection["selected"]}
        leaked_holdouts = [
            record.get("record_id")
            for record in holdouts
            if record.get("record_id") in selected_ids
        ]
        if leaked_holdouts:
            issues.append(f"holdout recuperado como exemplar: {leaked_holdouts}")
    except (OSError, ValueError, KeyError) as exc:
        issues.append(f"catálogo curado inválido: {exc}")

    eval_report = evaluate_cases(REPO_ROOT / "evals" / "cases")
    if not eval_report["passed"]:
        issues.extend(
            f"eval {case['case_id']}: {case['message']}"
            for case in eval_report["failed_cases"]
        )

    skill_report = validate_skill_tree(REPO_ROOT / ".codex" / "skills")
    if not skill_report["valid"]:
        for skill in skill_report["results"]:
            for issue in skill.get("issues", []):
                issues.append(f"skill {skill.get('skill')}: {issue}")
        if skill_report["missing_skills"]:
            issues.append(f"skills obrigatórias ausentes: {skill_report['missing_skills']}")

    report = {
        "passed": not issues,
        "issues": issues,
        "schemas": len(schema_files),
        "corpus": corpus_summary,
        "evals": {
            "total": eval_report["total"],
            "passed": eval_report["passed_count"],
            "failed": eval_report["failed_count"],
        },
        "skills": {
            "required": len(skill_report["required_skills"]),
            "validated": sum(1 for item in skill_report["results"] if item["valid"]),
            "missing": skill_report["missing_skills"],
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
