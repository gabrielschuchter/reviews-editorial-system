# Contrato operacional de redação

## Matriz frase-claim

Todo parágrafo que declara população, método, número, resultado, dano,
recomendação, certeza, conflito ou aplicabilidade precisa apontar para claim_id
ou registrar por que é transição puramente editorial. A função do parágrafo não
substitui a fonte. Quando duas frases usam o mesmo claim, registre ambas para que
uma revisão posterior não altere a outra silenciosamente.

## Regras por elemento

| Elemento | Exigir | Recusar |
| --- | --- | --- |
| título | assunto e limite proporcionais | promessa de benefício ou mudança de paradigma |
| lead | decisão, problema ou achado com fonte | importância abstrata sem conteúdo |
| método | dado que muda interpretação | inventário enciclopédico do artigo |
| resultado | escala, direção, grupo, tempo e incerteza | comparação intragrupo apresentada como entre grupos |
| interpretação | consequência permitida pelo appraisal | causalidade em estudo observacional |
| limite | perto do claim afetado | ressalva genérica no último parágrafo |
| tabela | população, condição, ação e exceção | célula que depende de contexto oculto |

## Edições baseadas em diretrizes

Quando a candidata for uma edição de diretriz, aplique `REV-STRUCT-HARD-003` à introdução e `REV-STRUCT-HARD-004` à formulação das recomendações.

A recomendação pública deve ser declarada diretamente. Recuse construções como “A ASPEN recomenda”, “Segundo a ACG, recomenda-se”, “A diretriz orienta”, “O documento recomenda”, “Os autores sugerem” ou equivalentes. A fonte continua identificável no título, subtítulo, legenda, introdução, escopo, proveniência e metodologia quando essa informação é útil.

A retirada da atribuição não pode alterar a modalidade. Preserve integralmente força, certeza, população, condição, exceção e grau de obrigação. Uma recomendação condicional não pode virar imperativo forte por simplificação de estilo.

Antes do handoff, execute `scripts/audit_guideline_attribution.py` sobre a versão exata da candidata e exija `passed: true`.

## Revisão de números

Compare valor literal, sinal, unidade, população analítica, denominador,
comparador e horizonte. Se um cálculo for derivado, declare entradas, fórmula e
autoria do sistema. Não arredonde quando o arredondamento muda categoria, direção
ou decisão.

## Handoff

Antes de enviar para auditoria, entregue cobertura de claims, números sensíveis,
lacunas, versão do brief/framing e uma lista explícita de mudanças que exigem
reauditoria se forem aceitas.
