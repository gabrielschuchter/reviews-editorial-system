#!/usr/bin/env python3
"""Fachada JSON versionada para o aplicativo local Reviews Desktop."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import _bootstrap  # noqa: F401

from reviews_editorial.ui_bridge import (  # noqa: E402
    DEFAULT_DB,
    ReviewsUiBridge,
    UiBridgeError,
    envelope,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ponte local JSON do Reviews Editorial System para clientes desktop."
    )
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--storage", default=os.environ.get("REVIEWS_PRIVATE_ARCHIVE_ROOT"))
    parser.add_argument("command")
    parser.add_argument(
        "--arguments",
        help="Objeto JSON com os argumentos estruturados do comando.",
        default="{}",
    )
    parser.add_argument(
        "--arguments-file",
        help="Arquivo JSON local alternativo a --arguments.",
    )
    return parser


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = _parser().parse_args()
    try:
        if args.arguments_file:
            arguments = json.loads(Path(args.arguments_file).read_text(encoding="utf-8"))
        else:
            arguments = json.loads(args.arguments)
        if not isinstance(arguments, dict):
            raise ValueError("arguments deve ser um objeto JSON")
        bridge = ReviewsUiBridge(database_path=args.db, storage_root=args.storage)
        payload = bridge.dispatch(args.command, arguments)
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return 0
    except UiBridgeError as exc:
        print(
            json.dumps(
                envelope(args.command, errors=[exc.as_dict()]),
                ensure_ascii=False,
                indent=2,
                default=str,
            )
        )
        return 2 if exc.category in {"usage_error", "editorial_block"} else 1
    except (json.JSONDecodeError, ValueError) as exc:
        error = UiBridgeError(
            "INVALID_ARGUMENTS",
            str(exc),
            action="Envie um objeto JSON válido em --arguments.",
            category="usage_error",
        )
        print(
            json.dumps(
                envelope(args.command, errors=[error.as_dict()]),
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
