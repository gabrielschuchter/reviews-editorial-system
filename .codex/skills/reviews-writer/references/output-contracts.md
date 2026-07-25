# Contratos de saída

## Pacote normalizado

Gerar `document-inventory.json`, `page-map.json`, `table-map.json`, `figure-map.json`, `document-validation.json` e `missing-materials.md`.

## Extração e análise

Gerar overview, população, intervenções, desfechos, resultados, segurança, informação ausente, verificação numérica, claim ledger, classificação do estudo, revisão metodológica, limites de inferência e questões críticas.

## Pesquisa e planejamento

Gerar log de busca, escrutínio externo, correções/retratações, seleção de tipo, outline, exemplares e justificativa de inclusão/exclusão de resultados.

## Drafts e auditorias

Manter versões `v1-content.md`, `v2-structure.md`, `v3-style.md` e `v4-candidate.md`. Preservar auditorias factual, estatística, metodológica, estrutural, estilo, anti-IA, coerência e final; não sobrescrever a evidência de uma etapa anterior. Auditorias estatística, metodológica e de coerência devem ter narrativa `.md` e gate estruturado `.json` com `passed`; um texto Markdown isolado não autoriza avanço.

## Candidata

Gerar:

- `final/candidate.md`;
- `final/candidate.docx`;
- `final/editorial-report.md`;
- `final/source-map.json`;
- `final/quality-report.json`;
- `final/visual-plan.md`;
- `final/review-status.json` com `AGUARDANDO REVISÃO EDITORIAL`.

Registrar versões do sistema, Skill, constituição, contratos, metodologia, estilo, anti-IA, corpus, design, modelo, data e hashes das fontes. Nenhuma regra nova altera retroativamente edições antigas.
