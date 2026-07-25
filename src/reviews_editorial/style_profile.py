"""Métricas descritivas para um perfil de estilo candidato."""

from __future__ import annotations

import re
import statistics
from pathlib import Path
from typing import Any

from .io import dump_data

SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")
CONNECTORS = (
    "além disso",
    "no entanto",
    "por outro lado",
    "ainda assim",
    "portanto",
    "em contraste",
    "nesse contexto",
)


def _summary(values: list[int]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "mean": None, "median": None, "min": None, "max": None}
    return {
        "count": len(values),
        "mean": round(statistics.fmean(values), 2),
        "median": statistics.median(values),
        "min": min(values),
        "max": max(values),
    }


def analyze_texts(paths: list[str | Path]) -> dict[str, Any]:
    paragraph_lengths: list[int] = []
    sentence_lengths: list[int] = []
    title_lengths: list[int] = []
    numeric_tokens = 0
    total_words = 0
    connector_counts = {connector: 0 for connector in CONNECTORS}
    documents = []
    for raw_path in paths:
        path = Path(raw_path)
        text = path.read_text(encoding="utf-8-sig")
        words = re.findall(r"\b[\wÀ-ÿ-]+\b", text)
        total_words += len(words)
        numeric_tokens += len(re.findall(r"(?<!\w)\d+(?:[.,]\d+)?%?(?!\w)", text))
        paragraphs = [item.strip() for item in re.split(r"\n\s*\n", text) if item.strip()]
        paragraph_lengths.extend(len(re.findall(r"\b[\wÀ-ÿ-]+\b", item)) for item in paragraphs)
        sentences = [item.strip() for item in SENTENCE_RE.split(text) if item.strip()]
        sentence_lengths.extend(len(re.findall(r"\b[\wÀ-ÿ-]+\b", item)) for item in sentences)
        for line in text.splitlines():
            if line.startswith("#"):
                title_lengths.append(len(re.findall(r"\b[\wÀ-ÿ-]+\b", line.lstrip("# "))))
        lowered = text.casefold()
        for connector in CONNECTORS:
            connector_counts[connector] += lowered.count(connector)
        documents.append({"path": str(path.resolve()), "word_count": len(words)})
    return {
        "profile_status": "candidate-awaiting-editorial-approval",
        "documents": documents,
        "metrics": {
            "paragraph_words": _summary(paragraph_lengths),
            "sentence_words": _summary(sentence_lengths),
            "title_words": _summary(title_lengths),
            "numeric_tokens_per_1000_words": round(numeric_tokens / total_words * 1000, 2) if total_words else None,
            "connector_counts": connector_counts,
        },
        "interpretation_limits": [
            "Métricas linguísticas não são regras editoriais.",
            "O corpus de entrada deve conter apenas exemplares A/B aprovados.",
            "Conclusões sobre voz, naturalidade e qualidade exigem curadoria humana.",
        ],
    }


def write_profile(paths: list[str | Path], output_path: str | Path) -> dict[str, Any]:
    profile = analyze_texts(paths)
    dump_data(output_path, profile)
    return profile
