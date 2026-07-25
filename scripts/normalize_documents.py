from __future__ import annotations

import argparse
import json

from _bootstrap import REPO_ROOT
from reviews_editorial.documents import normalize_job_documents
from reviews_editorial.jobs import load_job


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalizar fontes registradas em um job.")
    parser.add_argument("job_dir")
    args = parser.parse_args()
    job = load_job(args.job_dir)
    sources = [source.get("job_copy") or source["location"] for source in job["source_documents"]]
    report = normalize_job_documents(args.job_dir, sources)
    print(json.dumps(report["validation"], ensure_ascii=False, indent=2))
    return 0 if report["validation"]["status"] != "blocked" else 1


if __name__ == "__main__":
    raise SystemExit(main())
