from __future__ import annotations

import argparse
import json
from pathlib import Path

from _bootstrap import REPO_ROOT
from reviews_editorial.drive_policy import prepare_drive_transfer
from reviews_editorial.io import dump_data


def main() -> int:
    parser = argparse.ArgumentParser(description="Preparar uma transferência segura para o conector do Drive.")
    parser.add_argument("candidate")
    parser.add_argument("--job-dir", required=True)
    parser.add_argument("--destination-folder-id", required=True)
    parser.add_argument(
        "--authorized-production-folder-id",
        action="append",
        required=True,
        help="ID de pasta de produção permitida; repita para autorizar mais de uma.",
    )
    parser.add_argument("--source-archive-folder-id", action="append", default=[])
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    manifest = prepare_drive_transfer(
        args.candidate,
        job_dir=args.job_dir,
        destination_folder_id=args.destination_folder_id,
        authorized_production_folder_ids=args.authorized_production_folder_id,
        source_archive_folder_ids=args.source_archive_folder_id,
        job_id=args.job_id,
        version=args.version,
    )
    output = Path(args.output) if args.output else Path(args.candidate).resolve().parent / "drive-transfer.json"
    dump_data(output, manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    print("Nenhum upload foi executado: o Codex deve usar o conector e registrar o URL retornado.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
