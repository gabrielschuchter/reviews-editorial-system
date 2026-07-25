---
name: reviews-audit
description: Auditar independentemente uma candidata do Reviews quanto a fonte, números, método, calibração de claims, framing, estrutura, português, tabelas, provenance e readiness. Use para produzir findings, não para reescrever o texto.
---

# Reviews audit

Ler `references/finding-contract.md` e executar o modo mais estreito que responda ao risco.

1. Selecionar modo: `source-fidelity`, `numbers`, `statistics`, `methodology`, `claim-calibration`, `journalistic-framing`, `tables`, `provenance`, `publication-readiness` ou `incremental`.
2. Produzir findings com evidência, status, severidade, confiança, claims afetados, consequência, correção recomendada e teste de regressão.
3. Distinguir confirmado, suspeito, não avaliado e resolvido. Não atribuir certeza à ausência de cobertura.
4. Rodar `scripts/audit_inference.py`, `scripts/validate_tables.py` e `scripts/validate_artifact.py audit-report` quando aplicável.
5. Entregar o relatório ao fluxo de correção separado; finding crítico bloqueia avanço.

Auditoria anti-IA é revisão de qualidade textual, nunca detector de autoria ou pontuação de humanidade.
