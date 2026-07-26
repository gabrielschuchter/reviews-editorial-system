from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.skill_validation import validate_skill_tree


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validar profundidade operacional, referências e evals das skills Reviews."
    )
    parser.add_argument(
        "skills_root",
        nargs="?",
        type=Path,
        default=REPO_ROOT / ".codex" / "skills",
    )
    args = parser.parse_args()
    report = validate_skill_tree(args.skills_root)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
