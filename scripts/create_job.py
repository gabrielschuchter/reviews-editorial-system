from __future__ import annotations

import argparse

from _bootstrap import REPO_ROOT
from reviews_editorial.jobs import create_job


def main() -> int:
    parser = argparse.ArgumentParser(description="Criar job editorial isolado.")
    parser.add_argument("--source", action="append", required=True, help="Documento-fonte; repita para vários")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--edition-type")
    parser.add_argument("--source-folder")
    parser.add_argument("--editor")
    parser.add_argument("--notes")
    parser.add_argument("--copy-inputs", action="store_true")
    parser.add_argument("--jobs-root", default=str(REPO_ROOT / "jobs"))
    args = parser.parse_args()
    job_dir = create_job(
        args.jobs_root,
        args.source,
        topic=args.topic,
        requested_edition_type=args.edition_type,
        source_folder=args.source_folder,
        editor=args.editor,
        notes=args.notes,
        copy_inputs=args.copy_inputs,
    )
    print(job_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
