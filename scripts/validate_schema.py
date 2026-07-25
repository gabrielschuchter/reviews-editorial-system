from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.io import load_data
from reviews_editorial.schema_validation import validate


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validar um artefato contra um dos 13 contratos JSON Schema locais."
    )
    parser.add_argument("artifact")
    parser.add_argument(
        "--schema",
        required=True,
        help="Nome (ex.: population) ou caminho para um *.schema.json.",
    )
    args = parser.parse_args()
    schema_arg = Path(args.schema)
    schema_path = (
        schema_arg
        if schema_arg.suffix
        else REPO_ROOT / "schemas" / f"{args.schema}.schema.json"
    )
    if not schema_path.is_absolute():
        schema_path = (REPO_ROOT / schema_path).resolve()
    artifact_path = Path(args.artifact).resolve()
    schema = load_data(schema_path)
    payload = load_data(artifact_path)
    issues = validate(payload, schema)
    report = {
        "valid": not issues,
        "artifact": str(artifact_path),
        "schema": str(schema_path),
        "issues": [
            {"path": issue.path, "message": issue.message}
            for issue in issues
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
