from __future__ import annotations

import argparse
import json

from _bootstrap import REPO_ROOT
from reviews_editorial.corpus import apply_classification_overrides
from reviews_editorial.io import dump_data, load_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Aplicar decisões explícitas de curadoria ao corpus.")
    parser.add_argument("--manifest", default=str(REPO_ROOT / "corpus" / "manifest.yml"))
    parser.add_argument(
        "--catalog",
        help=(
            "Catálogo curado a alterar diretamente. Use para IDs que não pertencem ao "
            "snapshot-base; não expande nem duplica o manifesto."
        ),
    )
    parser.add_argument("--overrides", required=True, help="JSON com lista de overrides")
    parser.add_argument("--output", help="Destino; por padrão atualiza o manifesto informado")
    args = parser.parse_args()
    source = args.catalog or args.manifest
    manifest = load_data(source)
    payload = load_data(args.overrides)
    overrides = payload.get("overrides", payload) if isinstance(payload, dict) else payload
    if not isinstance(overrides, list):
        parser.error("overrides deve ser uma lista")
    result = apply_classification_overrides(manifest, overrides)
    destination = args.output or source
    dump_data(destination, result)
    print(json.dumps({"changes": len(result.get("classification_changes", [])), "output": destination}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
