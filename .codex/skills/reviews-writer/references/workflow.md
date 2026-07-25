# Workflow editorial

## Índice

1. Estados e gates
2. Regra de avanço
3. Lote e checkpoints
4. Revisão humana

## Estados e gates

Executar os 20 estados definidos em `src/reviews_editorial/constants.py`. Cada estado representa uma etapa concluída e exige seus outputs antes do avanço. Usar `scripts/validate_job.py <job> --target-state <estado>` para inspecionar o gate e `--advance --actor <nome>` apenas após a validação.

O estado `documents_validated` exige confirmação humana item a item em `normalized/manual-document-review.json`, vinculada pelo hash ao inventário, além do status final em `document-validation.json`. O estado `claim_ledger_complete` precede qualquer redação. Erros críticos permanecem em `job.yml:gates.critical_errors` e nos relatórios de auditoria.

## Regra de avanço

- Avançar somente um estado por vez.
- Nunca criar um output vazio apenas para satisfazer o gate.
- Registrar a origem de todo artefato derivado.
- Salvar o último estado válido quando uma etapa falhar.
- Reexecutar auditorias afetadas por qualquer mudança factual ou metodológica.

## Lote e checkpoints

Criar um job por artigo. A coordenação de lote ainda é manual: não há runner nem schema de lote implementado. Se um manifesto externo for usado, registrar `batch_id`, pasta-fonte, tipo padrão, instruções e status. Compartilhar regras e templates, nunca extrações, claims, resultados ou auditorias entre jobs.

## Revisão humana

A candidata termina em `AGUARDANDO REVISÃO EDITORIAL`. A aprovação humana deve registrar responsável, data, versão e escopo. Pontuação alta ou ausência de erro automático não equivale a aprovação.
