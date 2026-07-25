from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviews_editorial.assurance import validate_table_rows
from reviews_editorial.io import load_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validar linhas de recomendações editoriais.")
    parser.add_argument("table", type=Path, help="JSON/YAML-JSON com {rows: [...]}")
    args = parser.parse_args()
    payload = load_data(args.table)
    result = validate_table_rows(payload.get("rows", []) if isinstance(payload, dict) else [])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
