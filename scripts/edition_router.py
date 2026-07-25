from __future__ import annotations

import argparse
import json

from _bootstrap import REPO_ROOT
from reviews_editorial.edition_router import recommend_edition_type
from reviews_editorial.io import dump_data, load_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Recomendar tipo de edição com justificativa e override.")
    parser.add_argument("context", help="JSON com contexto do estudo e do briefing")
    parser.add_argument("--output")
    args = parser.parse_args()
    context = load_data(args.context)
    result = recommend_edition_type(context)
    if args.output:
        dump_data(args.output, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not result.get("requires_editor_review") else 2


if __name__ == "__main__":
    raise SystemExit(main())
