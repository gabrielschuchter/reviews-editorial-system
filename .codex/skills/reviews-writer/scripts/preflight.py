from __future__ import annotations

import json
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = SKILL_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from reviews_editorial.pipeline import validate_pipeline


def main() -> int:
    if len(sys.argv) != 2:
        print("uso: preflight.py <job-dir>", file=sys.stderr)
        return 2
    report = validate_pipeline(sys.argv[1])
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
