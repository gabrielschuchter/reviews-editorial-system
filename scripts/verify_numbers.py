from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.claims import verify_number_records
from reviews_editorial.io import dump_data, load_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validar registros de conferência numérica.")
    parser.add_argument("job_dir")
    parser.add_argument("--input")
    args = parser.parse_args()
    root = Path(args.job_dir)
    input_path = Path(args.input) if args.input else root / "extraction" / "number-records.json"
    payload = load_data(input_path)
    records = payload.get("records", payload) if isinstance(payload, dict) else payload
    report = verify_number_records(records)
    dump_data(root / "extraction" / "number-verification.json", report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
