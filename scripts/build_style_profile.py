from __future__ import annotations

import argparse
import json

from _bootstrap import REPO_ROOT
from reviews_editorial.style_profile import write_profile


def main() -> int:
    parser = argparse.ArgumentParser(description="Gerar perfil estilístico candidato a partir de textos A/B aprovados.")
    parser.add_argument("inputs", nargs="+", help="Arquivos de texto normalizado")
    parser.add_argument("--output", default=str(REPO_ROOT / "editorial" / "style" / "style-profile-candidate.json"))
    args = parser.parse_args()
    profile = write_profile(args.inputs, args.output)
    print(json.dumps({"documents": len(profile["documents"]), "status": profile["profile_status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
