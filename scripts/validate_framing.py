from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.framing import validate_framing_memo
from reviews_editorial.io import dump_data, load_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validar enquadramento jornalístico proporcional ao claim ledger.")
    parser.add_argument("memo", type=Path)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    claims: set[str] | None = None
    if args.ledger:
        ledger = load_data(args.ledger)
        claims = {str(item.get("claim_id")) for item in ledger.get("claims", []) if isinstance(item, dict)}
    report = validate_framing_memo(load_data(args.memo), claim_ids=claims)
    if args.output:
        dump_data(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
