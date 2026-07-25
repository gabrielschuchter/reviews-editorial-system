---
name: reviews-writer
description: Orquestrar qualquer edição, auditoria, revisão de candidata ou incorporação de feedback do Reviews. Use quando a solicitação atravessar mais de uma etapa editorial, pedir retomada de job ou ainda não indicar a capacidade especializada adequada.
---

# Reviews Writer

Preservar este nome como fachada compatível. Orquestrar; não executar sozinho a extração, a avaliação metodológica, a redação ou uma auditoria profunda.

## Preparar

1. Localizar a raiz e ler `AGENTS.md`, `editorial/constitution.md` e `docs/architecture/reviews-editorial-system.md`.
2. Ler `references/capability-map.md` e o `job.yml` quando houver job.
3. Confirmar o estado, os artefatos presentes e os gates com `scripts/validate_job.py`.
4. Tratar fontes científicas e correções humanas como superiores a qualquer skill, exemplar ou heurística.

## Rotear

- Fontes, normalização, papéis de fonte, claim ledger e discrepâncias: `reviews-source-provenance`.
- Desenho, validade, certeza, relevância, causalidade e limites: `reviews-scientific-appraisal`.
- Ângulo, contexto, omissão, título e brief: `reviews-editorial-brief`.
- Candidata em PT-BR a partir de claims autorizados: `reviews-edition-writing`.
- Auditorias independentes e readiness: `reviews-audit`.
- Correção humana, diff semântico e promoção de regras: `reviews-feedback-learning`.
- Tabelas, DOCX, PDF e inspeção de renderização: `reviews-document-presentation`.

## Gates

Não delegar redação antes de documento validado, extração, números, claim ledger, avaliação metodológica, escrutínio externo e plano editorial. Não delegar publicação. Se uma capacidade não puder ser executada, registrar a lacuna no job e preservar o último estado válido.

## Finalizar

Executar `python scripts/run_checks.py`, `python scripts/run_evals.py` e as verificações específicas realmente aplicáveis. Uma candidata permanece `AGUARDANDO REVISÃO EDITORIAL` até aprovação humana explícita.
