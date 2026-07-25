from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.assurance import audit_inference_text


def main() -> int:
    parser = argparse.ArgumentParser(description="Sinalizar saltos inferenciais que exigem revisão humana.")
    parser.add_argument("draft", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = audit_inference_text(args.draft.read_text(encoding="utf-8"))
    target = args.output or (REPO_ROOT / "audits" / "inference-audit.json")
    if args.output:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
