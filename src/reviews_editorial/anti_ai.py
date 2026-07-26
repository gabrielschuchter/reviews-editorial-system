"""Auditoria contextual de padrões artificiais em português brasileiro.

O módulo não tenta identificar autoria humana ou de IA. Ele registra sinais
localizados que exigem leitura editorial, com risco explícito de falso positivo.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from dataclasses import dataclass
from statistics import mean, pstdev
from typing import Any, Iterable


AUDIT_VERSION = "1.0.0"
REFERENCE_URL = "https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing"

_TRANSITIONS = (
    "além disso",
    "nesse contexto",
    "vale destacar",
    "vale ressaltar",
    "em suma",
    "em conclusão",
    "por fim",
    "diante desse cenário",
)
_PROMOTIONAL = re.compile(
    r"\b(?:revolucion[áa]ri[oa]|transformador[oa]|imperdível|"
    r"sem precedentes|solução definitiva|melhor escolha)\b",
    re.IGNORECASE,
)
_FALSE_PRECISION = re.compile(
    r"\b(?:exatamente|precisamente|inequivocamente|sem (?:qualquer )?dúvida|"
    r"com total certeza)\b",
    re.IGNORECASE,
)
_RELEVANCE_INFLATION = re.compile(
    r"\b(?:é|são|será|serão)\s+(?:fundamental|essencial|crucial|indispensável)\b|"
    r"\b(?:marco|mudança de paradigma|impacto transformador)\b",
    re.IGNORECASE,
)
_EMPTY_CONCLUSION = re.compile(
    r"\b(?:é|são|será|serão)\s+(?:fundamental|essencial|importante|necessário)\s+"
    r"(?:continu\w*|avanç\w*|segu\w*|olh\w*|invest\w*)\b|"
    r"\b(?:o futuro|o caminho)\s+(?:depende|exige)\s+(?:de|uma)\s+(?:atenção|reflexão|ação)\b",
    re.IGNORECASE,
)
_SYMMETRIC_TRIAD = re.compile(
    r"\b(?:seja|quer)\s+[^,;.!?\n]{2,55},\s*(?:seja|quer)\s+[^,;.!?\n]{2,55},\s*"
    r"(?:seja|quer)\s+[^,;.!?\n]{2,55}",
    re.IGNORECASE,
)
_VAGUE_ATTRIBUTION = re.compile(
    r"\b(?:estudos|pesquisas|a literatura|especialistas|dados)\s+"
    r"(?:mostram|indicam|sugerem|apontam|demonstram)\b",
    re.IGNORECASE,
)
_CHATBOT = re.compile(
    r"\b(?:como modelo de linguagem|até minha última atualização|"
    r"espero que isso ajude|posso ajudar com|aqui está uma versão)\b",
    re.IGNORECASE,
)
_TOOL_TOKEN = re.compile(
    r"\b(?:turn\d+(?:search|view|fetch)\d+|oaicite|contentReference|"
    r"citation_metadata)\b",
    re.IGNORECASE,
)
_GENERIC_OPENING = re.compile(
    r"^(?:no mundo atual|nos dias de hoje|em um cenário (?:cada vez mais )?"
    r"(?:dinâmico|complexo|em constante evolução)|vivemos em uma era em que|"
    r"atualmente,? é (?:cada vez mais )?(?:importante|fundamental))\b[^\n]*",
    re.IGNORECASE,
)
_SELF_QUALIFICATION = re.compile(
    r"\b(?:uma|esta|esse|este)\s+(?:síntese|análise|edição|texto|artigo)\s+"
    r"(?:crítica|abrangente|definitiva|inovadora|essencial)\b",
    re.IGNORECASE,
)
_META_DISCOURSE = re.compile(
    r"\b(?:vale destacar que|vale ressaltar que|é importante destacar que|"
    r"cabe destacar que|este texto demonstra que|esta análise demonstra que)\b",
    re.IGNORECASE,
)
_GENERIC_HEDGING = re.compile(
    r"\b(?:é importante considerar que|vale lembrar que|convém ressaltar que|"
    r"não se pode ignorar que)\b",
    re.IGNORECASE,
)
_NOT_ONLY = re.compile(r"\bnão apenas\b[^.!?]{0,180}\bmas(?: também)?\b", re.IGNORECASE)
_REEXPLANATION = re.compile(r"^(?:em outras palavras|ou seja|isto é|isso significa que)\b", re.IGNORECASE)
_SOURCE_NOUNS = re.compile(r"\b(?:estudo|trabalho|pesquisa|investigação)\b", re.IGNORECASE)
_CITATION = re.compile(
    r"(?:\[[^\]]{1,80}\]|\([^()]{0,100}\b(?:19|20)\d{2}[a-z]?[^()]{0,100}\)|"
    r"\bdoi:\s*10\.\d{4,9}/\S+|https?://\S+)",
    re.IGNORECASE,
)
_WORD = re.compile(r"[\wÀ-ÿ]+", re.UNICODE)
_STOP_WORDS = {
    "a", "ao", "aos", "as", "com", "da", "das", "de", "do", "dos", "e", "é",
    "em", "na", "nas", "no", "nos", "o", "os", "ou", "para", "por", "que", "se",
    "um", "uma", "uns", "umas",
}


@dataclass(frozen=True)
class _Paragraph:
    text: str
    start: int
    end: int
    number: int


def _paragraphs(text: str) -> list[_Paragraph]:
    paragraphs: list[_Paragraph] = []
    for match in re.finditer(r"(?s)\S.*?(?=\n\s*\n|\Z)", text):
        value = match.group(0).strip()
        if value:
            start = match.start() + len(match.group(0)) - len(match.group(0).lstrip())
            paragraphs.append(_Paragraph(value, start, start + len(value), len(paragraphs) + 1))
    return paragraphs


def _sentences(paragraph: _Paragraph) -> list[tuple[str, int, int]]:
    result: list[tuple[str, int, int]] = []
    for match in re.finditer(r"[^.!?\n]+(?:[.!?]+(?=\s|$)|$)", paragraph.text):
        value = match.group(0).strip()
        if value:
            offset = len(match.group(0)) - len(match.group(0).lstrip())
            start = paragraph.start + match.start() + offset
            result.append((value, start, start + len(value)))
    return result


def _excerpt(text: str, start: int, end: int, *, limit: int = 280) -> str:
    value = " ".join(text[start:end].split())
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip() + "…"


def _sentence_at(paragraphs: Iterable[_Paragraph], start: int) -> tuple[str, int, int] | None:
    for paragraph in paragraphs:
        if paragraph.start <= start <= paragraph.end:
            for sentence in _sentences(paragraph):
                if sentence[1] <= start <= sentence[2]:
                    return sentence
            return (paragraph.text, paragraph.start, paragraph.end)
    return None


def _paragraph_number(paragraphs: Iterable[_Paragraph], start: int) -> int | None:
    for paragraph in paragraphs:
        if paragraph.start <= start <= paragraph.end:
            return paragraph.number
    return None


def _word_set(sentence: str) -> set[str]:
    return {
        token.casefold()
        for token in _WORD.findall(sentence)
        if token.casefold() not in _STOP_WORDS and len(token) > 2
    }


def _contains_citation(sentence: str) -> bool:
    return bool(_CITATION.search(sentence))


def _finding(
    findings: list[dict[str, Any]],
    text: str,
    paragraphs: list[_Paragraph],
    *,
    category: str,
    start: int,
    end: int,
    evidence: str,
    severity: str,
    confidence: str,
    reason: str,
    false_positive_risk: str,
    recommendation: str,
) -> None:
    if start < 0 or end < start:
        return
    key = (category, start, end)
    if any((item["category"], item["location"]["start"], item["location"]["end"]) == key for item in findings):
        return
    findings.append(
        {
            "finding_id": f"AAI-{len(findings) + 1:03d}",
            "rule": category,
            "category": category,
            "excerpt": _excerpt(text, start, end),
            "location": {
                "paragraph": _paragraph_number(paragraphs, start),
                "start": start,
                "end": end,
            },
            "evidence": evidence,
            "severity": severity,
            "confidence": confidence,
            "reason": reason,
            "false_positive_risk": false_positive_risk,
            "localized_recommendation": recommendation,
            "review_status": "candidate",
            "requires_manual_confirmation": True,
        }
    )


def audit_text(text: str, *, artifact_id: str = "draft") -> dict[str, Any]:
    """Classificar sinais localizados sem emitir score ou alegação de autoria."""

    if not isinstance(text, str):
        raise TypeError("text deve ser uma string")
    paragraphs = _paragraphs(text)
    findings: list[dict[str, Any]] = []

    for match in _TOOL_TOKEN.finditer(text):
        _finding(
            findings, text, paragraphs, category="tool-token-leak", start=match.start(), end=match.end(),
            evidence="Token de ferramenta ou citação interna no texto público.", severity="critical",
            confidence="high", reason="O token expõe o processo de geração, não uma fonte legível.",
            false_positive_risk="low", recommendation="Remova o token e reinsira uma referência pública localizável.",
        )
    for match in _CHATBOT.finditer(text):
        _finding(
            findings, text, paragraphs, category="chatbot-tone", start=match.start(), end=match.end(),
            evidence="Fórmula de conversa de assistente encontrada no manuscrito.", severity="critical",
            confidence="high", reason="A frase fala como interface, não como edição Reviews.",
            false_positive_risk="low", recommendation="Remova a fórmula e reescreva apenas a informação editorial necessária.",
        )

    content_paragraphs = [
        item for item in paragraphs
        if not item.text.lstrip().startswith(("#", "-", "*")) and len(_WORD.findall(item.text)) >= 8
    ]
    if content_paragraphs:
        opening = content_paragraphs[0]
        match = _GENERIC_OPENING.search(opening.text)
        if match:
            _finding(
                findings, text, paragraphs, category="generic-opening",
                start=opening.start + match.start(), end=opening.start + match.end(),
                evidence="A abertura usa uma moldura genérica antes de apresentar o problema, população ou decisão.",
                severity="moderate", confidence="medium",
                reason="A formulação pode servir a quase qualquer tema e adia o conteúdo específico.",
                false_positive_risk="medium",
                recommendation="Comece pelo problema clínico, escopo ou decisão que esta edição realmente cobre.",
            )

    for match in _SELF_QUALIFICATION.finditer(text):
        sentence = _sentence_at(paragraphs, match.start())
        start, end = (sentence[1], sentence[2]) if sentence else (match.start(), match.end())
        _finding(
            findings, text, paragraphs, category="self-importance-announcement", start=start, end=end,
            evidence="O próprio texto qualifica sua relevância ou qualidade antes de demonstrá-la.", severity="moderate",
            confidence="high", reason="O corpus Reviews substitui autoqualificação por descrição objetiva do tema e da fonte.",
            false_positive_risk="low", recommendation="Descreva o conteúdo e a fonte; retire o adjetivo autoavaliativo.",
        )
    for match in _META_DISCOURSE.finditer(text):
        sentence = _sentence_at(paragraphs, match.start())
        start, end = (sentence[1], sentence[2]) if sentence else (match.start(), match.end())
        _finding(
            findings, text, paragraphs, category="metadiscourse", start=start, end=end,
            evidence="A frase anuncia que algo merece atenção em vez de entregar diretamente a informação.",
            severity="minor", confidence="medium", reason="O leitor pode avaliar a relevância a partir de evidência e contexto.",
            false_positive_risk="high", recommendation="Teste remover apenas a fórmula introdutória; mantenha o conteúdo que a sucede.",
        )

    for phrase in _TRANSITIONS:
        matches = list(re.finditer(rf"\b{re.escape(phrase)}\b", text, flags=re.IGNORECASE))
        if len(matches) < 2:
            continue
        for match in matches:
            sentence = _sentence_at(paragraphs, match.start())
            start, end = (sentence[1], sentence[2]) if sentence else (match.start(), match.end())
            _finding(
                findings, text, paragraphs, category="formulaic-transition", start=start, end=end,
                evidence=f"A transição “{phrase}” aparece {len(matches)} vezes no mesmo artefato.",
                severity="minor" if len(matches) == 2 else "moderate", confidence="medium",
                reason="Repetição cria uma cadência previsível sem garantir conexão lógica melhor.",
                false_positive_risk="high", recommendation="Verifique se a relação lógica já está explícita; remova a transição só se a coesão permanecer.",
            )
    hedges = list(_GENERIC_HEDGING.finditer(text))
    if len(hedges) >= 2:
        for match in hedges:
            sentence = _sentence_at(paragraphs, match.start())
            start, end = (sentence[1], sentence[2]) if sentence else (match.start(), match.end())
            _finding(
                findings, text, paragraphs, category="generic-hedging", start=start, end=end,
                evidence=f"A ressalva genérica aparece {len(hedges)} vezes.", severity="minor", confidence="medium",
                reason="A ressalva não identifica condição, risco ou incerteza específica.", false_positive_risk="high",
                recommendation="Substitua por uma condição concreta da fonte ou elimine a moldura redundante.",
            )

    heading_matches = list(re.finditer(r"(?m)^(?:#{1,6}\s+|Seção\s+[IVXLCDM]+\.\s+)[^\n]+$", text))
    if heading_matches and len(heading_matches) >= max(5, len(content_paragraphs) // 2):
        for match in heading_matches:
            _finding(
                findings, text, paragraphs, category="excessive-headings", start=match.start(), end=match.end(),
                evidence=f"Há {len(heading_matches)} cabeçalhos para {max(len(content_paragraphs), 1)} blocos de prosa.",
                severity="moderate", confidence="medium", reason="A segmentação pode interromper a leitura contínua.",
                false_positive_risk="medium", recommendation="Mantenha apenas cabeçalhos que mudam de domínio clínico, decisão ou tipo de evidência.",
            )
    for match in re.finditer(r"(?m)^(?:#{1,6}\s+|Seção\s+[IVXLCDM]+\.\s+)[^\n:]{4,80}:\s+[^\n.]{8,120}$", text):
        _finding(
            findings, text, paragraphs, category="predictable-structure", start=match.start(), end=match.end(),
            evidence="O cabeçalho já enuncia uma conclusão que o corpo deveria sustentar.", severity="minor",
            confidence="high", reason="O padrão antecipa a interpretação e torna a estrutura repetitiva.",
            false_positive_risk="medium", recommendation="Conserve o domínio clínico no título e mova a tese para o desenvolvimento.",
        )

    bullets = list(re.finditer(r"(?m)^\s*(?:[-*+]\s+|\d+[.)]\s+)([^\n]+)$", text))
    if len(bullets) >= 5:
        starters = [" ".join(_WORD.findall(match.group(1).casefold())[:3]) for match in bullets]
        repeated = [item for item, count in Counter(starters).items() if item and count >= 3]
        if repeated:
            for match, starter in zip(bullets, starters):
                if starter in repeated:
                    _finding(
                        findings, text, paragraphs, category="mechanical-enumeration", start=match.start(), end=match.end(),
                        evidence=f"Lista longa repete a mesma abertura sintática (“{starter}”).", severity="minor",
                        confidence="medium", reason="A enumeração pode substituir uma hierarquia argumentativa real.",
                        false_positive_risk="medium", recommendation="Agrupe itens pela decisão que muda ou converta itens repetitivos em prosa curta.",
                    )

    document_sentences = [sentence for paragraph in paragraphs for sentence in _sentences(paragraph)]
    starts = Counter(
        " ".join(_WORD.findall(sentence.casefold())[:3])
        for sentence, _, _ in document_sentences
        if len(_WORD.findall(sentence)) >= 7
    )
    repeated_starts = {value for value, count in starts.items() if value and count >= 3}
    for sentence, start, end in document_sentences:
        prefix = " ".join(_WORD.findall(sentence.casefold())[:3])
        if prefix in repeated_starts:
            _finding(
                findings, text, paragraphs, category="artificial-parallelism", start=start, end=end,
                evidence=f"A mesma abertura (“{prefix}”) inicia ao menos três frases relevantes.", severity="minor",
                confidence="medium", reason="Paralelismo repetido pode produzir cadência mecânica.", false_positive_risk="high",
                recommendation="Mantenha apenas o paralelismo que organiza uma comparação real; varie a sintaxe do restante.",
            )
    not_only = list(_NOT_ONLY.finditer(text))
    if len(not_only) >= 2:
        for match in not_only:
            _finding(
                findings, text, paragraphs, category="mechanical-not-only-but", start=match.start(), end=match.end(),
                evidence=f"A oposição “não apenas … mas …” aparece {len(not_only)} vezes.", severity="minor",
                confidence="medium", reason="A construção perde força quando funciona como tique de ritmo.", false_positive_risk="high",
                recommendation="Reescreva somente as ocorrências que não preservam contraste clínico ou lógico indispensável.",
            )

    for index, (sentence, start, end) in enumerate(document_sentences):
        if _VAGUE_ATTRIBUTION.search(sentence) and not _contains_citation(sentence):
            _finding(
                findings, text, paragraphs, category="vague-attribution", start=start, end=end,
                evidence="Atribuição genérica sem fonte ou localizador no mesmo enunciado.", severity="moderate",
                confidence="medium", reason="O leitor não consegue distinguir dado, inferência e opinião editorial.",
                false_positive_risk="medium", recommendation="Nomeie a fonte, vincule ao claim ledger ou rebaixe a frase para hipótese editorial.",
            )
        for match in _PROMOTIONAL.finditer(sentence):
            _finding(
                findings, text, paragraphs, category="promotional-language", start=start + match.start(), end=start + match.end(),
                evidence="Adjetivo promocional ou absoluto detectado.", severity="moderate", confidence="high",
                reason="A linguagem aumenta a promessa sem acrescentar medida, condição ou evidência.",
                false_positive_risk="low", recommendation="Troque por efeito, população e limite verificáveis — ou remova o adjetivo.",
            )
        for match in _FALSE_PRECISION.finditer(sentence):
            _finding(
                findings, text, paragraphs, category="false-precision", start=start + match.start(), end=start + match.end(),
                evidence="Marcador de certeza absoluta sem estimativa, fonte ou condição visível.", severity="moderate",
                confidence="medium", reason="A formulação pode exceder a precisão permitida pela evidência.",
                false_positive_risk="medium", recommendation="Expresse o tamanho, a incerteza e a condição; não reduza a precisão sem conferir a fonte.",
            )
        for match in _RELEVANCE_INFLATION.finditer(sentence):
            _finding(
                findings, text, paragraphs, category="relevance-inflation", start=start + match.start(), end=start + match.end(),
                evidence="Expressão que anuncia importância, excepcionalidade ou impacto sem medida verificável.",
                severity="moderate", confidence="medium",
                reason="A relevância precisa aparecer pelo efeito, população, decisão e limite — não por autoafirmação.",
                false_positive_risk="high",
                recommendation="Substitua a declaração por consequência observável ou mantenha-a apenas com fonte e escopo explícitos.",
            )
        for match in _SYMMETRIC_TRIAD.finditer(sentence):
            _finding(
                findings, text, paragraphs, category="overly-symmetric-sentence", start=start + match.start(), end=start + match.end(),
                evidence="Três membros paralelos iniciados pela mesma construção retórica.", severity="minor",
                confidence="medium", reason="A simetria pode criar ritmo mecânico quando não organiza uma comparação indispensável.",
                false_positive_risk="high",
                recommendation="Mantenha a tríade somente se cada membro mudar uma condição, população ou consequência clínica.",
            )
        if index:
            previous = document_sentences[index - 1][0]
            previous_words = _word_set(previous)
            current_words = _word_set(sentence)
            overlap = len(previous_words & current_words) / max(len(previous_words | current_words), 1)
            if overlap >= 0.78 and len(current_words) >= 6:
                _finding(
                    findings, text, paragraphs, category="semantic-repetition", start=start, end=end,
                    evidence=f"A frase repete {overlap:.0%} do vocabulário informativo da frase anterior.",
                    severity="minor", confidence="medium", reason="A repetição pode reexplicar uma conclusão já entregue.",
                    false_positive_risk="medium", recommendation="Mantenha a segunda frase apenas se acrescentar condição, efeito, fonte ou consequência nova.",
                )
            if _REEXPLANATION.search(sentence) and overlap >= 0.45:
                _finding(
                    findings, text, paragraphs, category="obvious-reexplanation", start=start, end=end,
                    evidence="Marcador de reexplicação seguido por conteúdo muito próximo da frase anterior.", severity="minor",
                    confidence="medium", reason="A paráfrase não acrescenta decisão ou evidência.", false_positive_risk="high",
                    recommendation="Corte a reexplicação ou torne explícito qual novo limite ela esclarece.",
                )

    for paragraph in paragraphs:
        source_nouns = {match.group(0).casefold() for match in _SOURCE_NOUNS.finditer(paragraph.text)}
        if len(source_nouns) >= 3 and len(_sentences(paragraph)) >= 3:
            _finding(
                findings, text, paragraphs, category="rotating-synonymy", start=paragraph.start, end=paragraph.end,
                evidence=f"O mesmo referente parece alternar entre {', '.join(sorted(source_nouns))} no mesmo bloco.",
                severity="minor", confidence="low", reason="A troca de sinônimos pode obscurecer que se trata da mesma fonte.",
                false_positive_risk="high", recommendation="Use o termo mais preciso; varie somente quando houver diferença real de objeto ou desenho.",
            )

    paragraph_sentence_lengths = [len(_WORD.findall(sentence)) for sentence, _, _ in document_sentences]
    if len(paragraph_sentence_lengths) >= 7:
        relevant = [length for length in paragraph_sentence_lengths if 8 <= length <= 28]
        if len(relevant) >= 7 and pstdev(relevant) <= 1.5 and 10 <= mean(relevant) <= 22:
            first_sentence = document_sentences[0]
            _finding(
                findings, text, paragraphs, category="uniform-cadence", start=first_sentence[1], end=document_sentences[-1][2],
                evidence="Sete ou mais frases relevantes possuem comprimento quase idêntico.", severity="minor",
                confidence="low", reason="Cadência uniformizada pode soar mecânica em leitura contínua.", false_positive_risk="high",
                recommendation="Varie apenas onde a mudança melhora clareza, ênfase ou relação entre evidência e consequência.",
            )

    last_blocks = [item for item in content_paragraphs[-2:] if item]
    for paragraph in last_blocks:
        if re.search(r"\b(?:em suma|em conclusão|em síntese|em resumo)\b", paragraph.text, re.IGNORECASE):
            has_specific_anchor = bool(
                _CITATION.search(paragraph.text)
                or re.search(r"(?<![\w])\d+(?:[.,]\d+)?(?![\w])", paragraph.text)
                or re.search(r"\b(?:quando|exceto|salvo|risco|dano|incerteza|população)\b", paragraph.text, re.IGNORECASE)
            )
            if _EMPTY_CONCLUSION.search(paragraph.text) and not has_specific_anchor:
                _finding(
                    findings, text, paragraphs, category="empty-conclusion", start=paragraph.start, end=paragraph.end,
                    evidence="O fechamento usa um marcador conclusivo e uma chamada genérica sem efeito, limite ou condição.",
                    severity="minor", confidence="medium", reason="A conclusão recapitula importância abstrata sem orientar leitura ou decisão.",
                    false_positive_risk="high",
                    recommendation="Acrescente limite, aplicabilidade ou consequência verificável — ou remova o fechamento redundante.",
                )
            _finding(
                findings, text, paragraphs, category="recap-conclusion", start=paragraph.start, end=paragraph.end,
                evidence="O fechamento é apresentado como recapitulação explícita.", severity="minor", confidence="medium",
                reason="O corpus Reviews preserva a conclusão quando ela acrescenta limite, aplicabilidade ou decisão nova.",
                false_positive_risk="high", recommendation="Retenha o fechamento apenas se ele introduzir uma consequência ou incerteza que não apareceu antes.",
            )
            break

    critical = any(item["severity"] == "critical" for item in findings)
    source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "report_id": f"AAI-{source_hash[:12].upper()}",
        "audit_version": AUDIT_VERSION,
        "artifact_id": artifact_id,
        "artifact_sha256": source_hash,
        "scope": "padrões editoriais artificiais em português brasileiro; não atribuição de autoria",
        "reference_role": "taxonomia descritiva e corpus editorial; não detector de IA",
        "reference_sources": [
            {
                "source_id": "reviews-drive-human-revision-hdb",
                "role": "correções humanas e pares antes/depois",
                "location": "Drive: 1r-TewK_9W0s9SSlQ-4pm757uud7LjY5NoRcJNcQJfvU",
            },
            {
                "source_id": "reviews-drive-raw-sii",
                "role": "regressão de manuscrito cru, notas internas e contaminação",
                "location": "Drive: 1z8YzC4WgYVPhKSHhs-o30hMdmeBiSpJaIaGJvSw8LDU",
            },
            {
                "source_id": "wikipedia-signs-of-ai-writing",
                "role": "taxonomia descritiva, sem inferência de autoria",
                "location": REFERENCE_URL,
            },
        ],
        "passed": not critical,
        "manual_review_required": bool(findings),
        "findings": findings,
        "prohibitions": [
            "Não inferir autoria humana ou de IA.",
            "Não calcular score global de humanidade.",
            "Não reescrever texto durante a auditoria.",
            "Não tratar uma palavra isolada como prova de artificialidade.",
        ],
    }


def lint_text(text: str) -> dict[str, Any]:
    """Compatibilidade retroativa para scripts que chamavam o linter antigo."""

    report = audit_text(text)
    report["linter_version"] = AUDIT_VERSION
    report["reference"] = REFERENCE_URL
    report["note"] = (
        "Os sinais são contextuais e exigem revisão humana; o relatório não mede autoria, "
        "humanidade nem qualidade científica."
    )
    return report
