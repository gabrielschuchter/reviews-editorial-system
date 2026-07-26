from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.io import dump_data, load_data
from reviews_editorial.orchestrator import run_preflight


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Selecionar as capabilities do Reviews e executar preflight determinístico."
    )
    parser.add_argument("context", type=Path, help="JSON/YAML-JSON com stage, job_dir e artefatos opcionais")
    parser.add_argument("--output", type=Path, help="Destino do capability-plan.json")
    args = parser.parse_args()
    payload = load_data(args.context)
    if not isinstance(payload, dict):
        parser.error("context deve ser objeto")
    report = run_preflight(payload)
    output = args.output
    if output is None and payload.get("job_dir"):
        output = Path(str(payload["job_dir"])) / "planning" / "capability-plan.json"
    if output is not None:
        dump_data(output, report)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["preflight_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
