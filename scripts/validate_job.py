from __future__ import annotations

import argparse
import json

from _bootstrap import REPO_ROOT
from reviews_editorial.jobs import confirm_document_validation
from reviews_editorial.pipeline import advance_job, validate_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(description="Validar gates e opcionalmente avançar um job.")
    parser.add_argument("job_dir")
    parser.add_argument("--target-state")
    parser.add_argument("--confirm-documents", metavar="REVIEWER")
    parser.add_argument("--advance", action="store_true")
    parser.add_argument("--actor", default="codex")
    parser.add_argument("--human-approval", action="store_true")
    args = parser.parse_args()
    if args.confirm_documents:
        confirm_document_validation(args.job_dir, args.confirm_documents)
    if args.advance:
        if not args.target_state:
            parser.error("--advance exige --target-state")
        report = advance_job(
            args.job_dir,
            args.target_state,
            actor=args.actor,
            human_approval=args.human_approval,
        )
    else:
        report = validate_pipeline(args.job_dir, target_state=args.target_state)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
