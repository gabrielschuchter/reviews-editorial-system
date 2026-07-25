from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.feedback import compare_versions
from reviews_editorial.io import dump_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Comparar candidata e versão revisada.")
    parser.add_argument("candidate")
    parser.add_argument("reviewed")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = compare_versions(
        Path(args.candidate).read_text(encoding="utf-8-sig"),
        Path(args.reviewed).read_text(encoding="utf-8-sig"),
    )
    dump_data(args.output, result)
    print(json.dumps({"changes": len(result["changes"]), "similarity_ratio": result["similarity_ratio"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
