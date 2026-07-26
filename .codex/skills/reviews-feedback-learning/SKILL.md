---
name: reviews-feedback-learning
description: Converter feedback editorial em aprendizagem rastreável e testável sem corromper o corpus humano. Use após uma auditoria, revisão humana ou pós-publicação.
---

# Aprendizado editorial Reviews

## Contrato

O sistema aprende com decisões editoriais, mas não transforma toda alteração em regra e nunca reescreve a fonte humana para aparentar consistência. Esta skill compara versões, entende o motivo da mudança, liga-o a evidência e promove apenas regras testáveis.

Entradas: versão antes/depois, comentários humanos ou audit report, fontes/brief envolvidos e contexto da edição. Saídas: `learning-pattern` com confiança e escopo, regra candidata quando apropriada e caso de regressão.

## Processar feedback

1. Faça diff semântico, não apenas textual. Classifique a mudança: fato/número, interpretação, método, recomendação, enquadramento, estrutura, tom, apresentação ou preferência pessoal.
2. Pergunte qual decisão a mudança evita ou melhora. “Soa melhor” não basta para virar regra; registre como preferência de edição se não houver critério repetível.
3. Conecte a mudança à frase antiga, à nova frase, à fonte/localizador e ao gate que deveria tê-la detectado. Se não há suporte, trate-a como hipótese de processo, não como verdade.
4. Delimite o escopo: vale para artigos observacionais, diretrizes, tabelas, títulos, todos os formatos ou apenas para esta edição? Regras amplas exigem evidência proporcionalmente ampla.
5. Atribua confiança: alta para padrão repetido com fonte e auditoria; média para decisão editorial bem justificada; baixa para impressão isolada. Baixa confiança não automatiza comportamento.

## Promover uma regra

Uma regra candidata precisa ter gatilho, ação, exceção e teste observável. Exemplo: “quando um resultado for substituto, o lead não pode chamá-lo de benefício clínico sem declarar a limitação”. A regra é aprovada apenas após revisão humana e teste de regressão que falhe antes da regra e passe depois dela.

Não promova regras que alterem a voz humana, removam nuance ou conflitem com uma fonte primária. O corpus de referência é imutável: novos exemplos entram como versões datadas, com proveniência e decisão editorial anexada.

## Regressão e ciclo fechado

Adicione o caso ao diretório de evals quando a regra puder ser avaliada automaticamente ou por rubrica. Rode a suíte relevante antes de liberar a regra. Se uma regra produzir falsos positivos repetidos, reduza escopo ou desative-a; não force conformidade por meio de texto genérico.

Em uma revisão periódica, agrupe padrões por categoria e severidade, conte recorrência e priorize os que geram blocker/major. Atualize skill, schema, checklist ou eval conforme o local correto da falha. Registre a decisão e mantenha a versão anterior recuperável.
