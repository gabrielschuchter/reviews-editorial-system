from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.anti_ai import lint_text
from reviews_editorial.claims import audit_draft_text
from reviews_editorial.io import dump_data, load_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditar suporte factual e sinais heurísticos de escrita artificial.")
    parser.add_argument("--draft", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--factual-output", required=True)
    parser.add_argument("--anti-ai-output", required=True)
    args = parser.parse_args()
    text = Path(args.draft).read_text(encoding="utf-8-sig")
    factual = audit_draft_text(text, load_data(args.ledger))
    anti_ai = lint_text(text)
    dump_data(args.factual_output, factual)
    dump_data(args.anti_ai_output, anti_ai)
    summary = {"passed": factual["passed"] and anti_ai["passed"], "factual": factual, "anti_ai": anti_ai}
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
