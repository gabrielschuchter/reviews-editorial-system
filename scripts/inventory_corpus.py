from __future__ import annotations

import argparse
import json

from _bootstrap import REPO_ROOT
from reviews_editorial.inventory import (
    rows_from_drive_snapshot,
    scan_local_file,
    scan_zip,
    write_inventory,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventariar fontes sem alterar os originais.")
    parser.add_argument("--zip", dest="zips", action="append", default=[], help="Arquivo ZIP a inspecionar")
    parser.add_argument("--file", dest="files", action="append", default=[], help="Arquivo local adicional")
    parser.add_argument("--drive-snapshot", action="append", default=[], help="Snapshot JSON do Drive")
    parser.add_argument("--output-csv", default=str(REPO_ROOT / "SOURCE_INVENTORY.csv"))
    parser.add_argument("--manifest", default=str(REPO_ROOT / "corpus" / "manifest.yml"))
    args = parser.parse_args()
    rows = []
    for path in args.zips:
        rows.extend(scan_zip(path))
    for path in args.files:
        rows.append(scan_local_file(path))
    for path in args.drive_snapshot:
        rows.extend(rows_from_drive_snapshot(path))
    if not rows:
        parser.error("Informe ao menos uma fonte com --zip, --file ou --drive-snapshot")
    manifest = write_inventory(rows, args.output_csv, args.manifest)
    print(json.dumps({"records": manifest["record_count"], "counts": manifest["counts_by_level"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
