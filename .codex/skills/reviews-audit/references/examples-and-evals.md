# Exemplos e evals de auditoria

## Exemplos

### Exemplo 1 — Número com unidade trocada

O draft diz redução de 12 pontos, mas o ledger registra 12 por cento. Registre
numeric_accuracy blocker, cite trecho, claim_id e localizador, explique que a
unidade muda interpretação e devolva à redação/provenance.

### Exemplo 2 — Recomendação perde exceção

Uma tabela recomenda procedimento para todos, mas a fonte limita a pacientes
estáveis. Registre recommendation major ou blocker, preserve força/certidão da
fonte e encaminhe para redação, não corrija a célula no report.

### Exemplo 3 — Fecho repete sem acrescentar

O fecho reitera os achados sem aplicabilidade ou limite. Compare claims e
REV-STYLE-004; se nenhum conteúdo protegido for removido, registre style minor
com recomendação localizada de corte ou reformulação.

## Casos adversariais

### Caso adversarial 1 — Artigo mudou após candidata

Suplemento novo altera denominador. Pare o report final, registre versão
incompatível e retorne a provenance; não aceite correção manual sem novo ledger.

### Caso adversarial 2 — Falso positivo de linter

Uma expressão repetida é necessária para distinguir dois subgrupos. Registre
contexto, mantenha o trecho e classifique note; não force alteração cosmética.

### Caso adversarial 3 — Auditor tenta corrigir a prosa

O auditor sabe uma formulação melhor. Registre problema e correção solicitada,
mas não escreva sobre a candidata nem marque o finding como resolvido.

## Evals

Os casos locais exigem evidência por finding, bloqueio de promessa sem fonte,
cobertura declarada quando material falta e regressão contra encerramento vazio
que remove condição relevante.
