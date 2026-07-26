"""Edição mínima de padrões confirmados pela auditoria anti-IA.

O humanizer não aceita candidatos não confirmados, não faz troca cosmética de
sinônimos e bloqueia qualquer operação que altere conteúdo factual protegido.
"""

from __future__ import annotations

import difflib
import hashlib
import re
from collections import Counter
from typing import Any, Iterable

from .claims import audit_draft_text


HUMANIZER_VERSION = "1.0.0"
_NUMBER = re.compile(r"(?<![\w])\d+(?:[.,]\d+)?(?![\w])")
_QUANTITY = re.compile(
    r"(?<![\w])\d+(?:[.,]\d+)?\s*(?:%|mg(?:/dL|/dia)?|g/dL|mmHg|mL|kg|"
    r"µg|UI|dias?|semanas?|meses?|anos?|horas?)(?![\w])",
    re.IGNORECASE,
)
_REFERENCE = re.compile(
    r"(?:\[[^\]]{1,80}\]|\([^()]{0,100}\b(?:19|20)\d{2}[a-z]?[^()]{0,100}\)|"
    r"\b(?:doi:\s*)?10\.\d{4,9}/\S+|https?://\S+)",
    re.IGNORECASE,
)
_MODALITY = re.compile(
    r"\b(?:não|nunca|deve|devem|deveria|deveriam|pode|podem|poderia|"
    r"recomenda-se|sugere-se|contraindicado|indicada|indicado|forte|condicional)\b",
    re.IGNORECASE,
)
_CONDITION = re.compile(
    r"\b(?:quando|se|salvo|exceto|desde que|apenas|em pessoas|em pacientes|"
    r"na ausência de|após)\b",
    re.IGNORECASE,
)
_DIRECTION = re.compile(
    r"\b(?:aumenta|aumentou|reduz|reduziu|diminui|diminuiu|melhora|melhorou|"
    r"piora|piorou|maior|menor|benefício|dano|risco)\b",
    re.IGNORECASE,
)
_TRANSITION_PREFIX = re.compile(
    r"^(?P<space>\s*)(?:além disso|nesse contexto|vale destacar(?: que)?|"
    r"vale ressaltar(?: que)?|é importante destacar(?: que)?|em suma|em conclusão|por fim)"
    r"\s*[,;:]?\s*",
    re.IGNORECASE,
)
_GENERIC_PREFIX = re.compile(
    r"^(?P<space>\s*)(?:no mundo atual|nos dias de hoje|em um cenário "
    r"(?:cada vez mais )?(?:dinâmico|complexo|em constante evolução))\s*,\s*",
    re.IGNORECASE,
)
_SELF_QUALIFIED_SUBTITLE = re.compile(
    r"^(?P<space>\s*)uma\s+síntese\s+(?:crítica|abrangente)\s+das\s+",
    re.IGNORECASE,
)


def _counter(pattern: re.Pattern[str], value: str) -> Counter[str]:
    return Counter(match.group(0).casefold().strip() for match in pattern.finditer(value))


def _protected_content(value: str) -> dict[str, list[str] | dict[str, int]]:
    return {
        "numbers": sorted(_counter(_NUMBER, value).elements()),
        "quantities": sorted(_counter(_QUANTITY, value).elements()),
        "references": sorted(_counter(_REFERENCE, value).elements()),
        "modalities": dict(_counter(_MODALITY, value)),
        "conditions": dict(_counter(_CONDITION, value)),
        "directions": dict(_counter(_DIRECTION, value)),
    }


def _preservation_issues(before: str, after: str) -> list[str]:
    original = _protected_content(before)
    revised = _protected_content(after)
    return [key for key in original if original[key] != revised[key]]


def _requires_claim_ledger(before: str) -> bool:
    protected = _protected_content(before)
    return any(
        protected[key]
        for key in ("numbers", "quantities", "references", "modalities", "conditions", "directions")
    )


def _line_or_sentence_range(text: str, start: int, end: int) -> tuple[int, int]:
    """Expandir um achado para a menor unidade editável sem tocar o documento inteiro."""

    line_start = text.rfind("\n", 0, start) + 1
    next_newline = text.find("\n", end)
    line_end = len(text) if next_newline == -1 else next_newline
    line = text[line_start:line_end]
    stripped = line.lstrip()
    if stripped.startswith("#") or stripped.startswith("Seção ") or ":" in line and len(line) <= 140:
        return line_start, line_end

    sentence_start = line_start
    for marker in re.finditer(r"[.!?]\s+", text[line_start:start]):
        sentence_start = line_start + marker.end()
    # A maioria dos achados vem do auditor como uma frase completa. Procurar
    # somente *depois* de ``end`` faria cada operação engolir a frase seguinte.
    # Quando o fim já é terminal, mantenha-o; caso contrário, complete apenas
    # a frase em que a ocorrência está localizada.
    if end > line_start and text[end - 1] in ".!?":
        sentence_end = end
    else:
        punctuation = re.search(r"[.!?](?=\s|$)", text[end:line_end])
        sentence_end = end + punctuation.end() if punctuation else line_end
    return sentence_start, sentence_end


def _finding_location(finding: dict[str, Any]) -> dict[str, int | None]:
    """Normalizar a localização para o contrato do diff, sem metadados extras."""

    raw = finding.get("location")
    if not isinstance(raw, dict):
        return {"start": None, "end": None}
    start = raw.get("start")
    end = raw.get("end")
    return {
        "start": start if isinstance(start, int) and start >= 0 else None,
        "end": end if isinstance(end, int) and end >= 0 else None,
    }


def _suggest_edit(category: str, segment: str) -> tuple[str, str] | None:
    """Sugerir somente transformações locais cuja semântica seja inalterada."""

    if category == "self-importance-announcement":
        revised = _SELF_QUALIFIED_SUBTITLE.sub(r"\g<space>As ", segment, count=1)
        if revised != segment:
            return revised, "Retirou autoqualificação do subtítulo sem alterar tema ou fonte."
    if category in {"formulaic-transition", "metadiscourse", "recap-conclusion"}:
        revised = _TRANSITION_PREFIX.sub(r"\g<space>", segment, count=1)
        if revised != segment and revised.strip():
            return revised, "Retirou apenas a moldura discursiva; preservou a frase informativa."
    if category == "generic-opening":
        revised = _GENERIC_PREFIX.sub(r"\g<space>", segment, count=1)
        if revised != segment and revised.strip():
            return revised, "Removeu uma abertura genérica antes do conteúdo específico."
    if category == "predictable-structure" and ":" in segment:
        heading, _, _ = segment.partition(":")
        if heading.strip():
            return heading.rstrip(), "Manteve o domínio no cabeçalho e retirou a tese antecipada."
    return None


def _decision_map(decisions: Iterable[dict[str, Any]] | dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    raw = decisions.get("decisions", []) if isinstance(decisions, dict) else decisions
    if raw is None:
        return {}
    if not isinstance(raw, Iterable) or isinstance(raw, (str, bytes)):
        raise TypeError("decisions deve ser uma lista ou objeto com decisions")
    mapped: dict[str, dict[str, Any]] = {}
    for decision in raw:
        if not isinstance(decision, dict):
            continue
        finding_id = str(decision.get("finding_id") or "")
        if finding_id:
            mapped[finding_id] = decision
    return mapped


def _affected_claim_ids(segment: str, claim_ledger: dict[str, Any] | None) -> list[str]:
    if not claim_ledger:
        return []
    normalized = " ".join(segment.casefold().split())
    ids: list[str] = []
    for claim in claim_ledger.get("claims", []):
        claim_text = " ".join(str(claim.get("claim_text") or "").casefold().split())
        if claim_text and (claim_text in normalized or normalized in claim_text):
            ids.append(str(claim.get("claim_id")))
    return ids


def _base_result(text: str, report: dict[str, Any]) -> dict[str, Any]:
    source_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    report_id = str(report.get("report_id") or "unknown-report")
    digest = hashlib.sha256(f"{source_hash}:{report_id}".encode("utf-8")).hexdigest()
    return {
        "humanization_id": f"HUM-{digest[:12].upper()}",
        "humanizer_version": HUMANIZER_VERSION,
        "source_report_id": report_id,
        "original_sha256": source_hash,
        "revised_sha256": source_hash,
        "status": "no-confirmed-findings",
        "revised_text": text,
        "unified_diff": "",
        "changes": [],
        "summary": {"applied": 0, "rejected": 0, "skipped": 0, "blocked": 0},
        "overall_reaudit": {
            "status": "not-applicable",
            "affected_claim_ids": [],
            "checks": ["Nenhuma alteração aplicada."],
        },
        "prohibitions": [
            "Não alterar fatos, números, unidades, referências, direção, modalidade ou condições.",
            "Não trocar palavras apenas por sinônimos.",
            "Não aplicar finding candidato sem confirmação humana registrada.",
            "Não reescrever o documento inteiro para resolver ocorrência localizada.",
        ],
    }


def humanize_text(
    text: str,
    anti_ai_report: dict[str, Any],
    decisions: Iterable[dict[str, Any]] | dict[str, Any] | None,
    *,
    claim_ledger: dict[str, Any] | None = None,
    max_operations: int = 6,
    max_changed_characters: int | None = None,
) -> dict[str, Any]:
    """Aplicar somente mudanças confirmadas e retorná-las como diff auditável."""

    if not isinstance(text, str):
        raise TypeError("text deve ser uma string")
    if not isinstance(anti_ai_report, dict):
        raise TypeError("anti_ai_report deve ser um objeto")
    result = _base_result(text, anti_ai_report)
    findings = anti_ai_report.get("findings")
    if not isinstance(findings, list):
        result["status"] = "blocked"
        result["summary"]["blocked"] = 1
        result["overall_reaudit"] = {
            "status": "blocked",
            "affected_claim_ids": [],
            "checks": ["Relatório anti-IA sem lista de ocorrências."],
        }
        return result

    decision_by_id = _decision_map(decisions)
    pending: list[dict[str, Any]] = []
    for finding in findings:
        if not isinstance(finding, dict):
            continue
        finding_id = str(finding.get("finding_id") or "")
        decision = decision_by_id.get(finding_id)
        category = str(finding.get("category") or finding.get("rule") or "unknown")
        if not decision or decision.get("status") != "confirmed" or not str(decision.get("reviewed_by") or "").strip():
            result["changes"].append(
                {
                    "change_id": f"HUM-{len(result['changes']) + 1:03d}",
                    "finding_id": finding_id,
                    "category": category,
                    "status": "skipped-unconfirmed",
                    "before": None,
                    "after": None,
                    "reason": "A ocorrência não possui confirmação humana identificada.",
                    "location": _finding_location(finding),
                    "protected_content": {"preserved": None, "issues": []},
                    "claim_reaudit": {"status": "not-applicable", "affected_claim_ids": [], "checks": []},
                    "reviewed_by": decision.get("reviewed_by") if decision else None,
                    "user_rejectable": True,
                }
            )
            result["summary"]["skipped"] += 1
            continue
        if decision.get("disposition") == "rejected":
            result["changes"].append(
                {
                    "change_id": f"HUM-{len(result['changes']) + 1:03d}",
                    "finding_id": finding_id,
                    "category": category,
                    "status": "rejected",
                    "before": None,
                    "after": None,
                    "reason": str(decision.get("reason") or "Mudança rejeitada por revisão humana."),
                    "location": _finding_location(finding),
                    "protected_content": {"preserved": None, "issues": []},
                    "claim_reaudit": {"status": "not-applicable", "affected_claim_ids": [], "checks": []},
                    "reviewed_by": decision.get("reviewed_by"),
                    "user_rejectable": True,
                }
            )
            result["summary"]["rejected"] += 1
            continue

        location = finding.get("location") if isinstance(finding.get("location"), dict) else {}
        start = location.get("start")
        end = location.get("end")
        if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start or end > len(text):
            result["changes"].append(
                {
                    "change_id": f"HUM-{len(result['changes']) + 1:03d}",
                    "finding_id": finding_id,
                    "category": category,
                    "status": "blocked",
                    "before": None,
                    "after": None,
                    "reason": "A localização da ocorrência não é segura para edição localizada.",
                    "location": {"start": start, "end": end},
                    "protected_content": {"preserved": None, "issues": ["invalid-location"]},
                    "claim_reaudit": {"status": "blocked", "affected_claim_ids": [], "checks": ["Localização inválida."]},
                    "reviewed_by": decision.get("reviewed_by"),
                    "user_rejectable": True,
                }
            )
            result["summary"]["blocked"] += 1
            continue
        segment_start, segment_end = _line_or_sentence_range(text, start, end)
        before = text[segment_start:segment_end]
        suggestion = _suggest_edit(category, before)
        if suggestion is None:
            result["changes"].append(
                {
                    "change_id": f"HUM-{len(result['changes']) + 1:03d}",
                    "finding_id": finding_id,
                    "category": category,
                    "status": "manual-only",
                    "before": before,
                    "after": None,
                    "reason": "A categoria confirmada exige julgamento editorial; não há transformação automática segura.",
                    "location": {"start": segment_start, "end": segment_end},
                    "protected_content": {"preserved": None, "issues": []},
                    "claim_reaudit": {"status": "not-applicable", "affected_claim_ids": [], "checks": []},
                    "reviewed_by": decision.get("reviewed_by"),
                    "user_rejectable": True,
                }
            )
            result["summary"]["skipped"] += 1
            continue
        after, reason = suggestion
        preservation = _preservation_issues(before, after)
        if preservation:
            result["changes"].append(
                {
                    "change_id": f"HUM-{len(result['changes']) + 1:03d}",
                    "finding_id": finding_id,
                    "category": category,
                    "status": "blocked",
                    "before": before,
                    "after": after,
                    "reason": "A edição proposta alteraria conteúdo protegido.",
                    "location": {"start": segment_start, "end": segment_end},
                    "protected_content": {"preserved": False, "issues": preservation},
                    "claim_reaudit": {"status": "blocked", "affected_claim_ids": [], "checks": ["Conteúdo protegido divergiu."]},
                    "reviewed_by": decision.get("reviewed_by"),
                    "user_rejectable": True,
                }
            )
            result["summary"]["blocked"] += 1
            continue
        if _requires_claim_ledger(before) and claim_ledger is None:
            result["changes"].append(
                {
                    "change_id": f"HUM-{len(result['changes']) + 1:03d}",
                    "finding_id": finding_id,
                    "category": category,
                    "status": "blocked",
                    "before": before,
                    "after": after,
                    "reason": "A mudança toca enunciado com claim protegido; claim ledger é obrigatório para reauditoria.",
                    "location": {"start": segment_start, "end": segment_end},
                    "protected_content": {"preserved": True, "issues": []},
                    "claim_reaudit": {"status": "blocked", "affected_claim_ids": [], "checks": ["Claim ledger ausente."]},
                    "reviewed_by": decision.get("reviewed_by"),
                    "user_rejectable": True,
                }
            )
            result["summary"]["blocked"] += 1
            continue
        pending.append(
            {
                "finding_id": finding_id,
                "category": category,
                "start": segment_start,
                "end": segment_end,
                "before": before,
                "after": after,
                "reason": reason,
                "reviewed_by": str(decision.get("reviewed_by")),
                "affected_claim_ids": _affected_claim_ids(before, claim_ledger),
            }
        )

    pending.sort(key=lambda item: (item["start"], item["end"]))
    overlaps = any(current["start"] < previous["end"] for previous, current in zip(pending, pending[1:]))
    change_budget = max_changed_characters if max_changed_characters is not None else max(120, int(len(text) * 0.15))
    changed_characters = sum(max(len(item["before"]), len(item["after"])) for item in pending)
    if pending and (overlaps or len(pending) > max_operations or changed_characters > change_budget):
        result["status"] = "blocked"
        reason = "Operações sobrepostas" if overlaps else "Edição ampla excede o limite configurado"
        for item in pending:
            result["changes"].append(
                {
                    "change_id": f"HUM-{len(result['changes']) + 1:03d}",
                    "finding_id": item["finding_id"],
                    "category": item["category"],
                    "status": "blocked",
                    "before": item["before"],
                    "after": item["after"],
                    "reason": reason,
                    "location": {"start": item["start"], "end": item["end"]},
                    "protected_content": {"preserved": True, "issues": []},
                    "claim_reaudit": {"status": "blocked", "affected_claim_ids": item["affected_claim_ids"], "checks": [reason]},
                    "reviewed_by": item["reviewed_by"],
                    "user_rejectable": True,
                }
            )
            result["summary"]["blocked"] += 1
        result["overall_reaudit"] = {"status": "blocked", "affected_claim_ids": [], "checks": [reason]}
        return result

    revised = text
    for item in reversed(pending):
        revised = revised[:item["start"]] + item["after"] + revised[item["end"]:]
    ledger_audit: dict[str, Any] | None = None
    if pending and claim_ledger is not None:
        ledger_audit = audit_draft_text(revised, claim_ledger)
        if not ledger_audit["passed"]:
            result["status"] = "blocked"
            for item in pending:
                result["changes"].append(
                    {
                        "change_id": f"HUM-{len(result['changes']) + 1:03d}",
                        "finding_id": item["finding_id"],
                        "category": item["category"],
                        "status": "blocked",
                        "before": item["before"],
                        "after": item["after"],
                        "reason": "A reauditoria do claim ledger não passou; nenhuma mudança foi aplicada.",
                        "location": {"start": item["start"], "end": item["end"]},
                        "protected_content": {"preserved": True, "issues": []},
                        "claim_reaudit": {
                            "status": "failed",
                            "affected_claim_ids": item["affected_claim_ids"],
                            "checks": [issue.get("issue_id", "issue") for issue in ledger_audit.get("issues", [])],
                        },
                        "reviewed_by": item["reviewed_by"],
                        "user_rejectable": True,
                    }
                )
                result["summary"]["blocked"] += 1
            result["overall_reaudit"] = {
                "status": "failed",
                "affected_claim_ids": sorted({claim for item in pending for claim in item["affected_claim_ids"]}),
                "checks": [issue.get("issue_id", "issue") for issue in ledger_audit.get("issues", [])],
            }
            return result

    for item in pending:
        checks = ["Números, unidades, referências, direção, modalidade e condições preservados."]
        if ledger_audit is not None:
            checks.append("Claim ledger reaudited after the local edit.")
        result["changes"].append(
            {
                "change_id": f"HUM-{len(result['changes']) + 1:03d}",
                "finding_id": item["finding_id"],
                "category": item["category"],
                "status": "applied",
                "before": item["before"],
                "after": item["after"],
                "reason": item["reason"],
                "location": {"start": item["start"], "end": item["end"]},
                "protected_content": {"preserved": True, "issues": []},
                "claim_reaudit": {
                    "status": "passed" if ledger_audit is not None else "not-applicable",
                    "affected_claim_ids": item["affected_claim_ids"],
                    "checks": checks,
                },
                "reviewed_by": item["reviewed_by"],
                "user_rejectable": True,
            }
        )
        result["summary"]["applied"] += 1

    if pending:
        result["status"] = "completed"
        result["revised_text"] = revised
        result["revised_sha256"] = hashlib.sha256(revised.encode("utf-8")).hexdigest()
        result["unified_diff"] = "\n".join(
            difflib.unified_diff(
                text.splitlines(), revised.splitlines(), fromfile="before", tofile="after", lineterm=""
            )
        )
        result["overall_reaudit"] = {
            "status": "passed" if ledger_audit is not None else "not-applicable",
            "affected_claim_ids": sorted({claim for item in pending for claim in item["affected_claim_ids"]}),
            "checks": [
                "Mudanças limitadas a ocorrências confirmadas.",
                "Conteúdo protegido preservado em cada diff.",
                "Claim ledger reaudited." if ledger_audit is not None else "Nenhum claim protegido foi editado sem ledger.",
            ],
        }
    return result
