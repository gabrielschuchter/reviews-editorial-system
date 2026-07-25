"""I/O determinístico, atômico e sem dependências externas."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


class DataFormatError(ValueError):
    """Indica que um manifesto não usa o subconjunto JSON de YAML 1.2."""


def load_data(path: str | Path) -> Any:
    """Ler JSON ou um arquivo .yml escrito no subconjunto JSON de YAML 1.2."""

    target = Path(path)
    try:
        return json.loads(target.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise DataFormatError(
            f"{target} deve conter JSON válido (subconjunto determinístico de YAML 1.2): "
            f"linha {exc.lineno}, coluna {exc.colno}: {exc.msg}"
        ) from exc


def dump_data(path: str | Path, value: Any) -> Path:
    """Gravar dados em UTF-8 de forma atômica e estável."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=target.parent, delete=False
    ) as handle:
        handle.write(payload)
        temporary = Path(handle.name)
    os.replace(temporary, target)
    return target


def write_text(path: str | Path, text: str) -> Path:
    """Gravar texto em UTF-8 de forma atômica."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", dir=target.parent, delete=False
    ) as handle:
        handle.write(normalized)
        temporary = Path(handle.name)
    os.replace(temporary, target)
    return target


def sha256_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def relative_to_or_self(path: Path, root: Path | None) -> str:
    if root is None:
        return str(path)
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())
