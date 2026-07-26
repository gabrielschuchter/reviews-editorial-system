from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.io import dump_data, load_data
from reviews_editorial.scientific_appraisal import validate_scientific_appraisal


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validar evidência localizada e julgamentos humanos de appraisal científico."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    payload = load_data(args.input)
    if not isinstance(payload, dict):
        parser.error("input deve ser objeto JSON/YAML-JSON")
    report = validate_scientific_appraisal(payload)
    if args.output:
        dump_data(args.output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
