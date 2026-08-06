from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from reviews_editorial.guideline_intro import audit_guideline_introduction


def main() -> int:
    parser = argparse.ArgumentParser(description="Auditar introdução de edição baseada em diretriz.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--artifact-id", default="draft")
    args = parser.parse_args()

    text = args.input.read_text(encoding="utf-8-sig")
    report = audit_guideline_introduction(text, artifact_id=args.artifact_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
