from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.humanizer import humanize_text
from reviews_editorial.io import dump_data, load_data, write_text


def _resolve_output(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else (REPO_ROOT / candidate).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Aplicar somente edições PT-BR confirmadas, mínimas e reauditéveis."
    )
    parser.add_argument("--input", required=True, help="Rascunho UTF-8 original.")
    parser.add_argument("--anti-ai-report", required=True, help="Relatório emitido por audit_anti_ai.py.")
    parser.add_argument("--decisions", required=True, help="JSON com decisões humanas por finding_id.")
    parser.add_argument("--output", required=True, help="Caminho do humanization-diff JSON.")
    parser.add_argument("--rewritten-output", required=True, help="Caminho do texto revisado; nunca sobrescreva a fonte.")
    parser.add_argument("--ledger", help="Claim ledger obrigatório quando a edição toca conteúdo protegido.")
    parser.add_argument("--max-operations", type=int, default=6)
    parser.add_argument("--max-changed-characters", type=int)
    args = parser.parse_args()

    source = Path(args.input)
    report = load_data(args.anti_ai_report)
    decisions = load_data(args.decisions)
    ledger = load_data(args.ledger) if args.ledger else None
    result = humanize_text(
        source.read_text(encoding="utf-8-sig"),
        report,
        decisions,
        claim_ledger=ledger,
        max_operations=args.max_operations,
        max_changed_characters=args.max_changed_characters,
    )
    dump_data(_resolve_output(args.output), result)
    write_text(_resolve_output(args.rewritten_output), result["revised_text"])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in {"completed", "no-confirmed-findings"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
