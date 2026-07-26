from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.assurance import scan_skill_tree
from reviews_editorial.skill_validation import validate_skill_tree


def main() -> int:
    parser = argparse.ArgumentParser(description="Examinar skills locais por padrões de alto risco.")
    parser.add_argument("skills_root", nargs="?", type=Path, default=REPO_ROOT / ".codex" / "skills")
    args = parser.parse_args()
    security = scan_skill_tree(args.skills_root)
    implementation = validate_skill_tree(args.skills_root)
    result = {
        "passed": security["passed"] and implementation["valid"],
        "scanner": "local-equivalent-to-cisco-skill-scanner",
        "security": security,
        "implementation": implementation,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
