"""Classificação conservadora baseada em sinais, nunca em nome como verdade final."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import PurePosixPath
from typing import Any


def _key(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return "".join(char for char in normalized if not unicodedata.combining(char)).casefold()


def _clean_title(name: str) -> str:
    value = re.sub(
        r"(?i)^\s*(?:c[oó]pia de\s+)+|^\s*\[(?:revisando|publicad[oa]|old)\]\s*",
        "",
        name,
    )
    value = re.sub(
        r"(?i)^\s*(?:final(?: revisada| humana)?|publica[cç][aã]o final|auditoria(?: final)?|vers[aã]o antiga)\s*[—-]\s*",
        "",
        value,
    )
    return re.sub(r"\s+", " ", value).strip()


@dataclass(frozen=True)
class Classification:
    document_type_id: str
    editorial_function_id: str
    stage_id: str
    status_id: str
    suggested_edition_title: str | None
    editorial_meaning: str
    confidence: float
    rationale: str
    evidence: tuple[str, ...]
    alternatives: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _edition_from_path(path: PurePosixPath, name: str) -> str | None:
    parts = path.parts
    if len(parts) >= 3 and parts[0:2] == ("Reviews", "Testes"):
        group = parts[2]
        if group != "REVISÃO FINAL — 7 EDIÇÕES":
            return group.replace("_", " ")
        cleaned = _clean_title(name)
        if cleaned and "relatório mestre" not in _key(cleaned):
            return cleaned.replace("_", " ")
    if len(parts) >= 3 and parts[0:2] == ("Reviews", "Entregas Gabriel"):
        if parts[2] == "Sugestões de Temas":
            return None
        if parts[2] == "Publicados":
            candidate = parts[3] if len(parts) >= 5 else parts[-1]
            return _clean_title(candidate).replace("_", " ")
        if parts[2] in {"Entendendo o Risco", "Versões antigas"}:
            candidate = parts[3] if len(parts) >= 5 else parts[-1]
            return _clean_title(candidate).replace("_", " ")
        candidate = parts[2] if len(parts) >= 4 else parts[-1]
        return _clean_title(candidate).replace("_", " ")
    return None


def classify_drive_item(item: dict[str, Any]) -> Classification:
    name = str(item.get("name") or "")
    path = PurePosixPath(str(item.get("path") or name))
    mime = str(item.get("mime_type") or "")
    signal = _key(f"{path.as_posix()} {name}")
    evidence: list[str] = [f"caminho={path.as_posix()}", f"mime_type={mime or 'desconhecido'}"]
    alternatives: list[str] = []
    suggested_edition = _edition_from_path(path, name)

    document_type = "type.unknown"
    editorial_function = "function.unclassified"
    stage = "stage.awaiting_classification"
    status = "status.classification_pending"
    confidence = 0.42
    meaning = (
        "Documento importado e preservado, mas ainda sem classificação editorial "
        "confirmada. Não deve ser usado como padrão aprovado."
    )
    rationale = "Metadados insuficientes para uma classificação segura."

    if mime == "application/pdf":
        document_type = "type.clinical_guideline" if any(
            token in signal for token in ("guideline", "diretriz", " acg ", " esc ", " aspen ", " apa ")
        ) else "type.scientific_article"
        editorial_function = "function.main_source"
        stage = "stage.material_received"
        status = "status.unverified"
        confidence = 0.76 if document_type == "type.clinical_guideline" else 0.66
        meaning = (
            "Fonte científica preservada como material de origem. A identidade, a "
            "integridade e o papel como fonte principal ainda exigem confirmação humana."
        )
        rationale = "Formato PDF e contexto da pasta indicam material científico de origem."
        alternatives.append("type.scientific_article")
    elif "auditoria" in signal:
        document_type = "type.audit"
        editorial_function = "function.audit"
        stage = "stage.audit"
        status = "status.unverified"
        confidence = 0.9
        meaning = (
            "Relatório de auditoria vinculado ao processo editorial. Seus achados devem "
            "ser lidos no contexto da versão auditada e não funcionam, isoladamente, "
            "como aprovação da edição."
        )
        rationale = "O título declara explicitamente que o documento é uma auditoria."
    elif any(token in signal for token in ("aprendizado editorial", "registro integral para ia")):
        document_type = "type.editorial_learning_record"
        editorial_function = "function.learning"
        stage = "stage.archived"
        status = "status.unverified"
        confidence = 0.91
        meaning = (
            "Registro histórico de alterações, decisões ou aprendizado. Pode apoiar "
            "auditoria e proposta de lições, mas não integra a memória validada sem aprovação."
        )
        rationale = "O título identifica explicitamente um registro de aprendizado ou comparação."
    elif "versao antiga" in signal or "/versoes antigas/" in signal or "[old]" in signal:
        document_type = "type.editorial_draft"
        editorial_function = "function.draft"
        stage = "stage.superseded"
        status = "status.superseded"
        confidence = 0.88
        meaning = (
            "Versão histórica indicada como antiga ou substituída. Deve permanecer "
            "auditável e não deve ser usada como texto corrente."
        )
        rationale = "O caminho ou o título contém marcador explícito de versão antiga."
    elif "publicacao final" in signal or "[publicado]" in signal or "[publicada]" in signal:
        document_type = "type.published_material"
        editorial_function = "function.published"
        stage = "stage.published"
        status = "status.published"
        confidence = 0.91
        meaning = (
            "Material com forte evidência de publicação pelo título. A correspondência "
            "com a publicação efetiva e a versão de origem ainda deve ser confirmada."
        )
        rationale = "Título contém marcador explícito de publicação."
    elif "/publicados/" in signal:
        document_type = "type.publication_version"
        editorial_function = "function.published"
        stage = "stage.ready_to_publish"
        status = "status.ready_to_publish"
        confidence = 0.82
        meaning = (
            "Arquivo localizado na área de publicados, forte evidência de material final. "
            "A publicação efetiva não é presumida apenas pelo diretório."
        )
        rationale = "A pasta Publicados é evidência forte, mas não confirmação definitiva."
        alternatives.append("type.published_material")
    elif "final revisada" in signal or "final humana" in signal:
        document_type = "type.editorial_review"
        editorial_function = "function.review"
        stage = "stage.awaiting_audit"
        status = "status.awaiting_review"
        confidence = 0.86
        meaning = (
            "Versão revisada com evidência de intervenção humana ou revisão final. "
            "Não deve ser tratada como aprovada ou publicada sem registro de aprovação."
        )
        rationale = "O título identifica uma versão final revisada ou humana."
        alternatives.extend(("type.publication_version", "type.editorial_draft"))
    elif re.search(r"(^|[\s/])final\s*[—-]", signal):
        document_type = "type.editorial_draft"
        editorial_function = "function.final"
        stage = "stage.awaiting_review"
        status = "status.preliminary"
        confidence = 0.79
        meaning = (
            "Versão indicada como final no nome, ainda sem aprovação humana registrada. "
            "Deve ser tratada como candidata até a confirmação editorial."
        )
        rationale = "O título contém marcador de final, usado apenas como evidência."
        alternatives.append("type.publication_version")
    elif "[revisando]" in signal:
        document_type = "type.editorial_review"
        editorial_function = "function.review"
        stage = "stage.editorial_review"
        status = "status.awaiting_review"
        confidence = 0.84
        meaning = (
            "Documento marcado como em revisão. O marcador pode estar desatualizado e "
            "precisa ser confirmado antes de orientar o fluxo atual."
        )
        rationale = "O título contém o marcador [Revisando]."
    elif "/modelos de reviews/" in signal or "modelo " in signal or "estrutura de " in signal:
        document_type = "type.template"
        editorial_function = "function.template"
        stage = "stage.material_received"
        status = "status.unverified"
        confidence = 0.88
        meaning = (
            "Modelo editorial reutilizável em caráter histórico. Sua validade atual e "
            "seu escopo precisam ser confirmados antes do uso normativo."
        )
        rationale = "O caminho e o título identificam um modelo editorial."
    elif "/prompts/" in signal or "prompt" in signal:
        document_type = "type.prompt"
        editorial_function = "function.prompt"
        stage = "stage.archived"
        status = "status.unverified"
        confidence = 0.9
        meaning = (
            "Prompt ou instrução histórica. Pode explicar como um resultado foi produzido, "
            "mas não constitui regra editorial aprovada por si só."
        )
        rationale = "O caminho ou título identifica explicitamente um prompt."
    elif "/transcricoes/" in signal:
        document_type = "type.transcript"
        editorial_function = "function.source"
        stage = "stage.material_received"
        status = "status.unverified"
        confidence = 0.9
        meaning = "Transcrição preservada como fonte histórica, sem aprovação normativa automática."
        rationale = "O arquivo está na árvore de transcrições."
    elif mime.startswith("image/"):
        document_type = "type.visual_asset"
        editorial_function = "function.derived"
        stage = "stage.material_received"
        status = "status.unverified"
        confidence = 0.88
        meaning = "Ativo visual preservado com sua proveniência e sem interpretação editorial automática."
        rationale = "O MIME type identifica uma imagem."
    elif "mapa de edicoes" in signal:
        document_type = "type.editorial_map"
        editorial_function = "function.organization"
        stage = "stage.material_received"
        status = "status.unverified"
        confidence = 0.91
        meaning = (
            "Mapa de organização editorial. Pode apoiar associação e classificação, "
            "mas não substitui a confirmação humana de cada edição."
        )
        rationale = "O título identifica explicitamente um mapa de edições."
    elif "sugestoes de temas" in signal or "/temas reviews" in signal:
        document_type = "type.topic_suggestion"
        editorial_function = "function.organization"
        stage = "stage.not_started"
        status = "status.unverified"
        confidence = 0.86
        meaning = "Sugestão de pauta ainda não equivalente a uma edição produzida."
        rationale = "O caminho identifica uma área de sugestões de temas."
    elif suggested_edition:
        document_type = "type.editorial_draft"
        editorial_function = "function.draft"
        stage = "stage.awaiting_classification"
        status = "status.classification_pending"
        confidence = 0.58
        meaning = (
            "Documento editorial associado por contexto de pasta a uma possível edição. "
            "A etapa, a versão e o vínculo precisam de confirmação humana."
        )
        rationale = "A pasta fornece evidência de edição, mas o nome não confirma o estado."

    if name.casefold().startswith("cópia de"):
        evidence.append("marcador_de_copia_no_titulo")
        alternatives.append("possible_version_or_duplicate")
        rationale += " O marcador “Cópia de” foi tratado somente como pista."
        confidence = min(confidence, 0.84)

    return Classification(
        document_type_id=document_type,
        editorial_function_id=editorial_function,
        stage_id=stage,
        status_id=status,
        suggested_edition_title=suggested_edition,
        editorial_meaning=meaning,
        confidence=confidence,
        rationale=rationale,
        evidence=tuple(evidence),
        alternatives=tuple(dict.fromkeys(alternatives)),
    )
