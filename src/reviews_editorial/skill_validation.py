"""Deterministic validation for the Reviews skill bundles.

This module deliberately validates operational evidence, not prose volume alone.
It checks the parts a new Codex instance needs in order to use a skill safely:
triggering metadata, a local output contract, stop conditions, executable or
declared evaluations, and resolvable one-hop references.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


REQUIRED_SKILLS = (
    "reviews-writer",
    "reviews-source-provenance",
    "reviews-scientific-appraisal",
    "reviews-editorial-brief",
    "reviews-journalistic-framing",
    "reviews-edition-writing",
    "reviews-anti-ai-writing",
    "reviews-humanizer-ptbr",
    "reviews-audit",
    "reviews-document-presentation",
    "reviews-feedback-learning",
)

# These are content requirements, not a template: aliases make the validator
# tolerant of natural Portuguese headings while keeping the required operating
# information explicit and discoverable.
REQUIRED_SECTIONS: dict[str, tuple[str, ...]] = {
    "purpose": ("propósito", "proposito"),
    "triggers": ("gatilhos", "quando usar", "acionamento"),
    "non_use": ("quando não usar", "quando nao usar", "não use", "nao use"),
    "inputs": ("entradas", "input obrigatório", "insumos"),
    "gates": ("gates", "pré-condições", "pre-condicoes"),
    "sources": ("hierarquia de fontes", "fontes e autoridade", "fontes"),
    "procedure": ("procedimento", "execução", "execucao", "passo a passo"),
    "judgment": ("decisões", "decisoes", "critérios de julgamento", "criterios de julgamento"),
    "output": ("contrato de saída", "contrato de saida", "saídas", "saidas", "output"),
    "artifacts": ("artefatos", "caminhos", "paths"),
    "tools": ("ferramentas", "scripts"),
    "stop": ("stop conditions", "condições de parada", "condicoes de parada"),
    "failure": ("falhas", "degraded", "degrada", "caminho degradado"),
    "prohibitions": ("proibições", "proibicoes", "não faça", "nao faca"),
    "interaction": ("interação", "interacao", "outras skills", "integração", "integracao"),
    "examples": ("exemplos"),
    "adversarial": ("casos adversariais", "adversarial"),
    "evals": ("evals", "avaliações", "avaliacoes"),
}

PLACEHOLDER_RE = re.compile(
    r"\b(?:todo|tbd|fixme|placeholder|lorem ipsum|a preencher|implementar aqui|exemplo ilustrativo)\b",
    flags=re.IGNORECASE,
)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
REPOSITORY_PATH_RE = re.compile(
    r"(?<![\w./-])((?:scripts|schemas|editorial|corpus|src)/[A-Za-z0-9_./-]+(?:\.[A-Za-z0-9_-]+)?)(?![\w./-])"
)


def _nonempty_lines(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def _read_utf8(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig", errors="replace")


def _frontmatter(text: str) -> tuple[dict[str, str], str, list[str]]:
    issues: list[str] = []
    if not text.startswith("---\n"):
        return {}, text, ["frontmatter YAML ausente"]
    end = text.find("\n---", 4)
    if end < 0:
        return {}, text, ["frontmatter YAML não foi encerrado"]
    raw = text[4:end]
    values: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if ":" not in line:
            issues.append(f"linha de frontmatter inválida: {line}")
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values, text[end + 4 :], issues


def _local_reference_paths(skill_root: Path, text: str) -> tuple[list[Path], list[str]]:
    references: list[Path] = []
    issues: list[str] = []
    for match in LINK_RE.finditer(text):
        target = match.group(1).strip()
        if not target or target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        candidate = (skill_root / target).resolve()
        try:
            candidate.relative_to(skill_root.resolve())
        except ValueError:
            issues.append(f"referência sai da skill: {target}")
            continue
        if not candidate.is_file():
            issues.append(f"referência local inexistente: {target}")
            continue
        references.append(candidate)
    return references, issues


def _load_eval_manifest(skill_root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    path = skill_root / "evals" / "cases.json"
    if not path.is_file():
        return None, ["evals/cases.json ausente"]
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"evals/cases.json inválido: {exc}"]
    if not isinstance(payload, dict):
        return None, ["evals/cases.json deve ser objeto"]
    return payload, []


def validate_skill_bundle(skill_root: str | Path, *, expected_name: str | None = None) -> dict[str, Any]:
    """Validate a single skill, including its direct operational resources."""

    # Resolve once so local references and report paths share the same absolute
    # base even when callers pass a relative skills root from the CLI.
    root = Path(skill_root).resolve()
    issues: list[str] = []
    skill_path = root / "SKILL.md"
    if not skill_path.is_file():
        return {"valid": False, "skill": root.name, "issues": ["SKILL.md ausente"]}
    text = _read_utf8(skill_path)
    metadata, body, frontmatter_issues = _frontmatter(text)
    issues.extend(frontmatter_issues)
    name = metadata.get("name")
    if not name:
        issues.append("frontmatter sem name")
    if expected_name and name != expected_name:
        issues.append(f"name esperado={expected_name}, obtido={name!r}")
    description = metadata.get("description", "")
    if len(description.split()) < 12:
        issues.append("description sem trigger específico suficiente")
    if PLACEHOLDER_RE.search(text):
        issues.append("SKILL.md contém marcador de placeholder/TODO")
    body_lines = _nonempty_lines(body)
    if body_lines < 70:
        issues.append(f"SKILL.md superficial: {body_lines} linhas úteis (<70)")
    local_refs, reference_issues = _local_reference_paths(root, body)
    issues.extend(reference_issues)
    referenced_text = "\n".join(_read_utf8(path) for path in local_refs)
    operational_text = (body + "\n" + referenced_text).casefold()
    combined_lines = body_lines + _nonempty_lines(referenced_text)
    if combined_lines < 130:
        issues.append(f"procedimento e referências insuficientes: {combined_lines} linhas úteis (<130)")
    for label, aliases in REQUIRED_SECTIONS.items():
        if not any(alias in operational_text for alias in aliases):
            issues.append(f"seção operacional ausente: {label}")
    example_count = len(re.findall(r"(?im)^#{2,6}\s*(?:exemplo|example)\b", body + "\n" + referenced_text))
    if example_count < 3:
        issues.append(f"menos de três exemplos concretos: {example_count}")
    adversarial_count = len(
        re.findall(r"(?im)^#{2,6}\s*(?:caso adversarial|adversarial|armadilha)\b", body + "\n" + referenced_text)
    )
    if adversarial_count < 3:
        issues.append(f"menos de três casos adversariais: {adversarial_count}")
    # A shallow “leia outro arquivo” wrapper cannot pass: it needs local steps,
    # paths/contracts and at least six imperative operational list items.
    imperative_lines = [
        line for line in body.splitlines()
        if re.match(r"\s*(?:\d+[.)]|[-*])\s+(?:confirme|registre|execute|valide|crie|gere|leia|compare|bloqueie|pare|selecione|audite|extraia|roteie|rejeite|verifique)\b", line, flags=re.IGNORECASE)
    ]
    if len(imperative_lines) < 6:
        issues.append("SKILL.md não contém procedimento operacional suficiente")
    repository_root = root.parents[2] if len(root.parents) >= 3 else None
    checked_repository_paths: list[str] = []
    if repository_root is not None:
        for token in sorted(set(REPOSITORY_PATH_RE.findall(body + "\n" + referenced_text))):
            candidate = repository_root / token
            checked_repository_paths.append(token)
            if not candidate.exists():
                issues.append(f"caminho de ferramenta ou contrato inexistente: {token}")
    manifest, eval_issues = _load_eval_manifest(root)
    issues.extend(eval_issues)
    eval_summary: dict[str, Any] = {"case_count": 0, "kinds": []}
    if manifest is not None:
        cases = manifest.get("cases")
        if not isinstance(cases, list):
            issues.append("evals/cases.json.cases deve ser lista")
        else:
            kinds: set[str] = set()
            identifiers: set[str] = set()
            for index, case in enumerate(cases, start=1):
                if not isinstance(case, dict):
                    issues.append(f"eval[{index}] não é objeto")
                    continue
                for field in ("case_id", "kind", "prompt", "input", "expected_artifact", "acceptance_criteria"):
                    if case.get(field) in (None, "", []):
                        issues.append(f"eval[{index}].{field} ausente")
                case_id = str(case.get("case_id") or "")
                if case_id in identifiers:
                    issues.append(f"eval case_id duplicado: {case_id}")
                identifiers.add(case_id)
                kinds.add(str(case.get("kind") or ""))
                if PLACEHOLDER_RE.search(json.dumps(case, ensure_ascii=False)):
                    issues.append(f"eval[{index}] contém placeholder")
            required_kinds = {"positive", "negative", "boundary", "regression"}
            missing_kinds = sorted(required_kinds - kinds)
            if missing_kinds:
                issues.append(f"tipos de eval ausentes: {missing_kinds}")
            eval_summary = {"case_count": len(cases), "kinds": sorted(kinds)}
    openai = root / "agents" / "openai.yaml"
    if not openai.is_file() or not _read_utf8(openai).strip():
        issues.append("agents/openai.yaml ausente ou vazio")
    return {
        "valid": not issues,
        "skill": root.name,
        "name": name,
        "issues": issues,
        "body_nonempty_lines": body_lines,
        "combined_nonempty_lines": combined_lines,
        "references_checked": [str(path.relative_to(root)) for path in local_refs],
        "repository_paths_checked": checked_repository_paths,
        "evals": eval_summary,
    }


def validate_skill_tree(skills_root: str | Path) -> dict[str, Any]:
    """Validate all mandatory Reviews skills and reject accidental extras/missing ones."""

    root = Path(skills_root)
    results = [
        validate_skill_bundle(root / name, expected_name=name)
        for name in REQUIRED_SKILLS
    ]
    discovered = sorted(path.name for path in root.iterdir() if path.is_dir()) if root.is_dir() else []
    missing = [name for name in REQUIRED_SKILLS if name not in discovered]
    return {
        "valid": not missing and all(result["valid"] for result in results),
        "required_skills": list(REQUIRED_SKILLS),
        "discovered_skills": discovered,
        "missing_skills": missing,
        "results": results,
    }
