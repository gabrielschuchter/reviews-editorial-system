from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.io import dump_data, load_data
from reviews_editorial.provenance import validate_claim_provenance


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validar proveniência por claim contra papéis de fonte registrados."
    )
    parser.add_argument("ledger", type=Path)
    parser.add_argument("source_roles", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate_claim_provenance(load_data(args.ledger), load_data(args.source_roles))
    if args.output:
        dump_data(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
