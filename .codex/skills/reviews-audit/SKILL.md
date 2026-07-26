---
name: reviews-audit
description: Auditar uma edição Reviews de forma independente contra fontes, appraisal e brief. Use antes de publicar e depois de revisões materiais.
---

# Auditoria independente Reviews

## Princípio

Auditoria não é revisão de estilo nem reescrita do autor. É uma leitura adversarial rastreável: para cada risco identificado, encontre a afirmação, a fonte, o localizador, o julgamento e a consequência editorial. Não dê “nota geral”, não invente defeitos e não aceite um texto persuasivo como evidência.

Entradas: edição candidata, pacote de fontes, claim ledger, appraisal, brief e tabelas. Saída: `audit-report` validável, com bloqueios e correções separadas por gravidade.

## Modos e independência

Use `preflight` para encontrar bloqueios antes da publicação, `revision` depois de alterações e `regression` quando uma regra aprendida deveria impedir um erro conhecido. Quem audita não deve substituir silenciosamente a redação: descreva a correção necessária e devolva ao responsável pela etapa.

## Roteiro de auditoria

1. Confirme a versão do rascunho, fontes e brief. Se uma fonte mudou, pare: trate como novo pacote de evidência.
2. Comece pelo título, subtítulo, lead, pull quotes, resumo e tabelas. Eles concentram a maior parte das promessas e são lidos fora de contexto.
3. Percorra cada afirmação factual, numérica, causal, normativa ou de aplicabilidade. Localize-a no claim ledger e na fonte. Registre ausência de suporte, mudança de sentido, unidade, população ou horizonte.
4. Compare a leitura editorial com o scientific appraisal: causalidade, precisão, multiplicidade, perdas, surrogate endpoint, subgrupos e generalização não podem ser “corrigidos” pela prosa.
5. Audite recomendações linha a linha. Toda recomendação deve conservar força, certeza, população, condições e exceções. A ausência de um dado deve aparecer como limitação, não como preenchimento implícito.
6. Examine enquadramento: conflito de interesse, controvérsia real, incentivos e perspectiva de pacientes devem aparecer quando materialmente relevantes. Não exija falsa simetria para parecer equilibrado.
7. Faça uma passagem de legibilidade e apresentação: hierarquia, tabelas completas, referências localizáveis, links, notas e quebra de página não podem esconder condições críticas.

## Classificar achados

Use uma categoria: `source_fidelity`, `numeric_accuracy`, `methodology`, `inference`, `recommendation`, `framing`, `style`, `table`, `provenance` ou `presentation`. Para cada achado, registre:

- severidade: `blocker`, `major`, `minor` ou `note`;
- texto/localização exata no rascunho;
- evidência e localizador da fonte;
- julgamento curto e confiança;
- consequência para a decisão do leitor;
- correção solicitada e responsável/etapa para onde deve retornar.

`blocker` inclui promessa sem suporte, número errado, causalidade indevida, recomendação alterada, fonte não rastreável ou omissão que inverte a interpretação. `major` altera materialmente nuance, população, aplicabilidade ou certeza. `minor` melhora clareza sem mudar o significado. `note` documenta risco sem exigir alteração.

## Verificações mecânicas

Execute quando houver os artefatos correspondentes:

```powershell
python scripts/audit_inference.py <rascunho>
python scripts/validate_tables.py <tabelas>
python scripts/validate_artifact.py audit-report <relatorio>
```

Esses comandos encontram padrões; nunca substituem a comparação com a fonte. Registre falsos positivos como nota de auditoria, sem apagar o alerta apenas para obter saída limpa.

## Encerramento

O relatório só pode aprovar quando não houver blocker e todos os achados major estiverem resolvidos ou aceitos explicitamente pelo responsável editorial com justificativa registrada. Após mudanças materiais, rode nova auditoria focada nas afirmações alteradas e nas dependências delas. Arquive o report junto da edição; não reduza o aprendizado a uma memória informal.
