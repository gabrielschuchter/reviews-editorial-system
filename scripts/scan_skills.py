from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.assurance import scan_skill_tree


def main() -> int:
    parser = argparse.ArgumentParser(description="Examinar skills locais por padrões de alto risco.")
    parser.add_argument("skills_root", nargs="?", type=Path, default=REPO_ROOT / ".codex" / "skills")
    args = parser.parse_args()
    result = scan_skill_tree(args.skills_root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
