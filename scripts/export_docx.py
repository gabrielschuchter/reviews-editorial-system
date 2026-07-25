from __future__ import annotations

import argparse
import json

from _bootstrap import REPO_ROOT
from reviews_editorial.export_docx import export_markdown_to_docx


def main() -> int:
    parser = argparse.ArgumentParser(description="Exportar Markdown para DOCX Google Docs-friendly.")
    parser.add_argument("markdown")
    parser.add_argument("output")
    args = parser.parse_args()
    audit = export_markdown_to_docx(args.markdown, args.output)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
