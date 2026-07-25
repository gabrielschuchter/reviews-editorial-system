from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from _bootstrap import REPO_ROOT
from reviews_editorial.anti_ai import lint_text
from reviews_editorial.claims import (
    audit_draft_text,
    build_claim_ledger,
    verify_number_records,
)
from reviews_editorial.exemplars import select_exemplars
from reviews_editorial.io import load_data


def _critical_rules(category: str, result: dict[str, Any]) -> set[str]:
    if category == "anti-ai":
        return {
            str(item.get("rule"))
            for item in result.get("findings", [])
            if item.get("severity") == "critical"
        }
    rules: set[str] = set()
    for item in result.get("issues", []):
        if item.get("severity") != "critical":
            continue
        issue_id = str(item.get("issue_id") or "")
        message = str(item.get("message") or "")
        if issue_id.startswith("unmapped-number:"):
            rules.add("unmapped-number")
            rules.add(issue_id)
        if "divergência numérica" in message:
            rules.add("divergent-number")
        if issue_id == "ledger" or "ledger vazio" in message:
            rules.add("invalid-ledger")
    return rules


def evaluate_case(case: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case.get("case_id") or "case-without-id")
    category = case.get("category")
    payload = case.get("input")
    expected = case.get("expected", {})
    actual: dict[str, Any]

    if category == "anti-ai":
        actual = lint_text(str(payload or ""))
    elif category == "factual":
        claims = payload.get("claims", []) if isinstance(payload, dict) else []
        draft = str(payload.get("draft") or "") if isinstance(payload, dict) else ""
        ledger = build_claim_ledger(claims)
        actual = audit_draft_text(draft, ledger)
    elif category == "number-verification":
        records = payload.get("records", []) if isinstance(payload, dict) else payload
        actual = verify_number_records(records)
        actual["passed"] = actual["valid"]
    elif category == "corpus-selection":
        manifest = {"records": payload.get("records", [])}
        actual = select_exemplars(
            manifest,
            edition_type=str(payload.get("edition_type") or ""),
            study_design=payload.get("study_design"),
            section=payload.get("section"),
            limit=int(payload.get("limit", 5)),
        )
        actual["selected_ids"] = [
            record.get("record_id") for record in actual.get("selected", [])
        ]
        actual["passed"] = True
    else:
        return {
            "case_id": case_id,
            "passed": False,
            "message": f"categoria de eval desconhecida: {category}",
            "actual": {},
        }

    failures: list[str] = []
    expected_passed = expected.get("passed")
    if isinstance(expected_passed, bool) and actual.get("passed") is not expected_passed:
        failures.append(
            f"passed esperado={expected_passed}, obtido={actual.get('passed')}"
        )
    expected_rule = expected.get("critical_rule")
    if expected_rule and expected_rule not in _critical_rules(str(category), actual):
        failures.append(f"regra crítica esperada não encontrada: {expected_rule}")
    excluded = expected.get("excluded_record_id")
    if excluded and excluded in actual.get("selected_ids", []):
        failures.append(f"holdout foi selecionado: {excluded}")
    included = expected.get("included_record_id")
    if included and included not in actual.get("selected_ids", []):
        failures.append(f"exemplar esperado não foi selecionado: {included}")
    return {
        "case_id": case_id,
        "passed": not failures,
        "message": "; ".join(failures) if failures else "ok",
        "actual": actual,
    }


def evaluate_cases(cases_dir: str | Path) -> dict[str, Any]:
    root = Path(cases_dir)
    results = []
    for path in sorted(root.glob("*.json")):
        try:
            result = evaluate_case(load_data(path))
        except (OSError, ValueError, TypeError, KeyError) as exc:
            result = {
                "case_id": path.stem,
                "passed": False,
                "message": f"erro ao executar caso: {exc}",
                "actual": {},
            }
        result["file"] = path.name
        results.append(result)
    failed = [result for result in results if not result["passed"]]
    return {
        "passed": bool(results) and not failed,
        "total": len(results),
        "passed_count": len(results) - len(failed),
        "failed_count": len(failed),
        "failed_cases": failed,
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Executar os casos determinísticos de avaliação.")
    parser.add_argument(
        "cases_dir",
        nargs="?",
        default=str(REPO_ROOT / "evals" / "cases"),
    )
    args = parser.parse_args()
    report = evaluate_cases(args.cases_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
