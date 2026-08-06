"""Gate estrutural para introduções de edições baseadas em diretrizes.

A política editorial exige contexto clínico antes da apresentação do documento.
O auditor é determinístico e conservador: ele verifica cobertura, ordem e
proporção. A suficiência factual de cada contexto continua dependente das fontes
e da auditoria humana.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


AUDIT_VERSION = "1.0.0"

_INTRO_HEADING = re.compile(r"^\s*(?:#{1,6}\s*)?introdu[cç][aã]o\s*$", re.IGNORECASE)
_NEXT_HEADING = re.compile(
    r"^\s*(?:#{1,6}\s+|"
    r"resumo(?:\s+das?\s+recomenda[cç][oõ]es)?|"
    r"tabela\s+\d+|quadro\s+\d+|figura\s+\d+|"
    r"se[cç][aã]o\s+[IVXLCDM0-9]+|"
    r"pergunta(?:\s+cl[ií]nica)?|s[ií]ntese(?:\s+da\s+evid[eê]ncia)?|"
    r"refer[eê]ncias)\b",
    re.IGNORECASE,
)

_METHOD_CUES = (
    "diretriz",
    "guideline",
    "aspen",
    "cosa",
    "publicada",
    "método",
    "metodologia",
    "busca",
    "pubmed",
    "embase",
    "cinahl",
    "cochrane",
    "painel",
    "delphi",
    "grade",
    "risco de viés",
    "estudos incluídos",
    "estudos elegíveis",
    "ensaios randomizados",
    "quase experimentais",
    "inferência causal",
)

_DIMENSION_CUES: dict[str, tuple[str, ...]] = {
    "disease_and_population": (
        "câncer",
        "cancro",
        "tumor",
        "doença",
        "condição",
        "paciente",
        "pessoa",
        "adulto",
        "população",
    ),
    "epidemiology_or_burden": (
        "epidemiologia",
        "epidemiológica",
        "incidência",
        "prevalência",
        "frequente",
        "comum",
        "casos",
        "diagnósticos",
        "mortes",
        "mortalidade",
        "carga",
        "internação",
        "hospitalização",
        "posição",
        "mundo",
        "global",
    ),
    "central_clinical_topic": (
        "nutrição",
        "nutricional",
        "alimentação",
        "ingestão",
        "energia",
        "proteína",
        "desnutrição",
        "malnutrição",
        "peso",
        "massa muscular",
    ),
    "care_challenges": (
        "mastigação",
        "deglutição",
        "disfagia",
        "odinofagia",
        "mucosite",
        "xerostomia",
        "salivação",
        "paladar",
        "apetite",
        "dor",
        "cirurgia",
        "radioterapia",
        "quimioterapia",
        "terapia sistêmica",
        "toxicidade",
        "sintomas",
    ),
    "clinical_consequences": (
        "prognóstico",
        "sobrevida",
        "qualidade de vida",
        "complicações",
        "cicatrização",
        "internações",
        "interrupções",
        "concluir o tratamento",
        "conclusão do tratamento",
        "função",
        "recuperação",
    ),
    "guideline_relevance": (
        "diretriz",
        "orientação",
        "recomendações",
        "decisões",
        "cuidado interdisciplinar",
        "equipe interdisciplinar",
        "prática clínica",
        "necessidade",
        "orientar profissionais",
    ),
}


def _normalize(text: str) -> str:
    return " ".join(text.casefold().split())


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\wÀ-ÿ]+\b", text, flags=re.UNICODE))


def _paragraphs(text: str) -> list[str]:
    blocks = [" ".join(block.split()) for block in re.split(r"\n\s*\n", text) if block.strip()]
    if len(blocks) > 1:
        return blocks
    lines = [" ".join(line.split()) for line in text.splitlines() if line.strip()]
    return lines if len(lines) > 1 else blocks


def extract_introduction(text: str) -> dict[str, Any]:
    """Extrair a introdução e seus limites a partir de texto simples ou Markdown."""

    lines = text.splitlines()
    start_line: int | None = None
    end_line = len(lines)
    for index, line in enumerate(lines):
        if _INTRO_HEADING.fullmatch(line):
            start_line = index + 1
            break
    if start_line is None:
        return {
            "found": False,
            "text": "",
            "paragraphs": [],
            "start_line": None,
            "end_line": None,
        }
    for index in range(start_line, len(lines)):
        if lines[index].strip() and _NEXT_HEADING.match(lines[index]):
            end_line = index
            break
    intro_text = "\n".join(lines[start_line:end_line]).strip()
    return {
        "found": bool(intro_text),
        "text": intro_text,
        "paragraphs": _paragraphs(intro_text),
        "start_line": start_line + 1,
        "end_line": end_line,
    }


def _method_score(paragraph: str) -> int:
    normalized = _normalize(paragraph)
    return sum(1 for cue in _METHOD_CUES if cue in normalized)


def _is_guideline_or_method_paragraph(paragraph: str) -> bool:
    normalized = _normalize(paragraph)
    if re.match(r"^(?:publicada|publicado|a diretriz|esta diretriz|o documento|a aspen|o guideline)\b", normalized):
        return True
    return _method_score(paragraph) >= 2


def _coverage(intro_text: str) -> dict[str, bool]:
    normalized = _normalize(intro_text)
    return {
        dimension: any(cue in normalized for cue in cues)
        for dimension, cues in _DIMENSION_CUES.items()
    }


def audit_guideline_introduction(text: str, *, artifact_id: str = "draft") -> dict[str, Any]:
    """Auditar a introdução de uma edição baseada em diretriz."""

    if not isinstance(text, str):
        raise TypeError("text deve ser uma string")

    extracted = extract_introduction(text)
    findings: list[dict[str, Any]] = []

    def add(rule: str, issue: str, required_action: str, *, evidence: Any = None) -> None:
        findings.append(
            {
                "finding_id": f"RGI-{len(findings) + 1:03d}",
                "rule_id": rule,
                "severity": "critical",
                "status": "confirmed",
                "issue": issue,
                "evidence": evidence,
                "required_action": required_action,
                "disposition_allowed": False,
            }
        )

    paragraphs = list(extracted["paragraphs"])
    method_indexes = [
        index for index, paragraph in enumerate(paragraphs)
        if _is_guideline_or_method_paragraph(paragraph)
    ]
    first_method_index = method_indexes[0] if method_indexes else None
    context_before_method = first_method_index if first_method_index is not None else len(paragraphs)
    total_words = _word_count(extracted["text"])
    method_words = sum(_word_count(paragraphs[index]) for index in method_indexes)
    method_share = method_words / total_words if total_words else 0.0
    coverage = _coverage(extracted["text"])

    if not extracted["found"]:
        add(
            "REV-STRUCT-HARD-003",
            "A candidata não contém uma introdução identificável.",
            "Criar uma introdução de diretriz com contexto clínico rastreável.",
        )
    else:
        if paragraphs and first_method_index == 0:
            add(
                "REV-STRUCT-HARD-003",
                "A introdução começa pela diretriz ou por sua elaboração.",
                "Abrir pela doença, população, carga e desafios do cuidado.",
                evidence=paragraphs[0],
            )
        if context_before_method < 2:
            add(
                "REV-STRUCT-HARD-003",
                "Há menos de dois parágrafos clínicos antes da apresentação da diretriz.",
                "Inserir pelo menos dois parágrafos de contexto clínico antes do documento.",
                evidence={"context_paragraphs_before_guideline": context_before_method},
            )
        if len(method_indexes) > 1:
            add(
                "REV-STRUCT-HARD-003",
                "A introdução dedica mais de um parágrafo à diretriz ou aos métodos.",
                "Concentrar o conteúdo metodológico indispensável em um único parágrafo.",
                evidence={"guideline_or_method_paragraphs": [index + 1 for index in method_indexes]},
            )
        if method_share > 0.25:
            add(
                "REV-STRUCT-HARD-003",
                "O conteúdo sobre diretriz e métodos ultrapassa vinte e cinco por cento da introdução.",
                "Reduzir método e ampliar contexto clínico sustentado pelas fontes.",
                evidence={"method_word_share": round(method_share, 4)},
            )
        for dimension, present in coverage.items():
            if not present:
                add(
                    "REV-STRUCT-HARD-003",
                    f"A introdução não cobre a dimensão obrigatória: {dimension}.",
                    "Adicionar contexto rastreável para essa dimensão ou registrar a indisponibilidade na fonte.",
                    evidence={"dimension": dimension},
                )

    source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "report_id": f"RGI-{source_hash[:12].upper()}",
        "audit_version": AUDIT_VERSION,
        "artifact_id": artifact_id,
        "artifact_sha256": source_hash,
        "policy": "introduções clínicas de edições baseadas em diretrizes",
        "passed": not findings,
        "blocking": bool(findings),
        "introduction": {
            "found": extracted["found"],
            "start_line": extracted["start_line"],
            "end_line": extracted["end_line"],
            "paragraph_count": len(paragraphs),
            "context_paragraphs_before_guideline": context_before_method,
            "guideline_or_method_paragraphs": [index + 1 for index in method_indexes],
            "total_words": total_words,
            "guideline_or_method_words": method_words,
            "guideline_or_method_share": round(method_share, 4),
            "coverage": coverage,
        },
        "findings": findings,
    }
