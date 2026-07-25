from __future__ import annotations

import argparse
import json

from _bootstrap import REPO_ROOT
from reviews_editorial.feedback import validate_feedback
from reviews_editorial.io import dump_data, load_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Validar feedback sem modificar regras automaticamente.")
    parser.add_argument("feedback")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    payload = load_data(args.feedback)
    records = payload.get("changes", payload) if isinstance(payload, dict) else payload
    result = validate_feedback(records, repository_root=REPO_ROOT)
    dump_data(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
