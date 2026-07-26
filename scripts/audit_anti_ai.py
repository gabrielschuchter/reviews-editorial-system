from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.anti_ai import audit_text
from reviews_editorial.io import dump_data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Auditar padrões artificiais em PT-BR sem alegar autoria ou reescrever o texto."
    )
    parser.add_argument("--input", required=True, help="Rascunho UTF-8 a auditar.")
    parser.add_argument("--output", required=True, help="Caminho do anti-ai-report JSON.")
    parser.add_argument("--artifact-id", default="draft", help="Identificador rastreável do rascunho.")
    args = parser.parse_args()

    draft_path = Path(args.input)
    report = audit_text(draft_path.read_text(encoding="utf-8-sig"), artifact_id=args.artifact_id)
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (REPO_ROOT / output_path).resolve()
    dump_data(output_path, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
