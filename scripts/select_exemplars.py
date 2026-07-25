from __future__ import annotations

import argparse
import json

from _bootstrap import REPO_ROOT
from reviews_editorial.corpus import load_manifest_with_catalogs
from reviews_editorial.exemplars import select_exemplars
from reviews_editorial.io import dump_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Selecionar somente exemplares A/B pertinentes.")
    parser.add_argument("--edition-type", required=True)
    parser.add_argument("--study-design")
    parser.add_argument("--section")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--manifest", default=str(REPO_ROOT / "corpus" / "manifest.yml"))
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = select_exemplars(
        load_manifest_with_catalogs(args.manifest),
        edition_type=args.edition_type,
        study_design=args.study_design,
        section=args.section,
        limit=args.limit,
    )
    dump_data(args.output, result)
    print(json.dumps({"selected": len(result["selected"]), "warning": result["warning"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
