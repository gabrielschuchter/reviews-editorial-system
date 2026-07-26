from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

# Importing the bootstrap establishes ``src/`` before loading the integration
# module when this file is executed directly from the repository root.
from _bootstrap import REPO_ROOT
from reviews_editorial.integration_smoke import run_full_job


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Executar fixture de job completo até candidate_for_review, sem autoaprovação humana."
    )
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Diretório temporário a preservar para inspeção; sem ele, a fixture é removida ao fim.",
    )
    args = parser.parse_args()
    if args.workspace:
        report = run_full_job(args.workspace)
    else:
        with tempfile.TemporaryDirectory(prefix="reviews-integration-") as temporary:
            report = run_full_job(Path(temporary))
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
