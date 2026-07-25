from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.claims import build_ledger_file
from reviews_editorial.jobs import load_job


def main() -> int:
    parser = argparse.ArgumentParser(description="Construir e validar o claim ledger.")
    parser.add_argument("job_dir")
    parser.add_argument("--input")
    args = parser.parse_args()
    root = Path(args.job_dir)
    source = Path(args.input) if args.input else root / "extraction" / "proposed-claims.json"
    job = load_job(root)
    ledger = build_ledger_file(
        source,
        root / "extraction" / "claim-ledger.json",
        job_id=job["job_id"],
    )
    print(json.dumps(ledger["validation"], ensure_ascii=False, indent=2))
    return 0 if ledger["validation"]["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
