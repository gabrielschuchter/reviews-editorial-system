from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.assurance import validate_audit_report, validate_editorial_brief, validate_source_roles
from reviews_editorial.io import load_data


VALIDATORS = {
    "editorial-brief": validate_editorial_brief,
    "source-roles": validate_source_roles,
    "audit-report": validate_audit_report,
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validar artefatos modulares do Reviews.")
    parser.add_argument("kind", choices=sorted(VALIDATORS))
    parser.add_argument("artifact", type=Path)
    args = parser.parse_args()
    result = VALIDATORS[args.kind](load_data(args.artifact))
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("valid") else 1


if __name__ == "__main__":
    raise SystemExit(main())
