---
name: reviews-edition-writing
description: Redigir uma edição Reviews com fidelidade às fontes, precisão científica e voz editorial humana. Use somente depois de provenance, appraisal e brief aprovados.
---

# Escrita de edição Reviews

## Contrato

Esta skill transforma um `editorial-brief` aprovado em uma peça publicável. Ela não pesquisa para preencher lacunas, não reabre a avaliação metodológica e não muda a recomendação da fonte. Se a evidência disponível não sustenta uma frase, registre a pendência e devolva o trabalho ao estágio correto.

Entradas obrigatórias:

- pacote de fontes e `source-roles` validados;
- `claim-ledger` com localizadores e números conferidos;
- `scientific-appraisal` concluído;
- `editorial-brief` com ângulo, limites, público e formato da edição.

Saídas: rascunho da edição, bloco de tabelas quando aplicável, lista de afirmações sensíveis para auditoria e registro das lacunas que impediram uma redação segura.

## Escolher o formato antes de redigir

Use o formato definido no brief. Não force todos os conteúdos para uma resenha de artigo.

| Formato | Pergunta que governa | Estrutura mínima |
| --- | --- | --- |
| Artigo/estudo | O que este estudo observou e até onde isso vai? | contexto, pergunta, método, achado, interpretação, limites |
| Diretriz | O que é recomendado, para quem e com qual força? | problema, recomendações, certeza, implementação, ressalvas |
| Revisão/síntese | O que o conjunto de evidências permite concluir? | escopo, elegibilidade, resultados, heterogeneidade, aplicabilidade |
| Debate | Onde está o desacordo real e o que o resolve? | consenso, dissenso delimitado, evidências de cada lado, decisão prática |
| Prática | Como aplicar sem transformar associação em prescrição? | cenário, ação condicional, monitoramento, quando não aplicar |

## Procedimento de escrita

1. Releia o brief e liste: tese editorial, conclusão verificável, limites obrigatórios, público, palavras proibidas e números que não podem variar.
2. Escreva uma pauta de parágrafos. Cada parágrafo deve ter função explícita: orientar, explicar método, apresentar resultado, interpretar ou limitar. Corte parágrafos que só repetem o anterior.
3. Abra com o problema ou a decisão clínica/editorial, não com uma sinopse burocrática do artigo. O primeiro bloco precisa responder por que o leitor deve continuar.
4. No nut graf, declare o que o material permite dizer e o que não permite. Separe relevância de certeza: um tema pode ser importante e ainda incerto.
5. Apresente método apenas no nível necessário para entender a força da conclusão. Preserve população, comparador, desfecho, janela temporal e desenho quando eles mudam o significado.
6. Escreva resultados com denominadores, unidade, direção, horizonte e incerteza quando disponíveis. Não troque risco absoluto por relativo sem declarar a troca; não arredonde de modo que altere a decisão.
7. Faça a interpretação usando o appraisal. Marque explicitamente se a conclusão é resultado do estudo, inferência editorial moderada ou hipótese. Um adjetivo não substitui essa distinção.
8. Inclua limites perto da afirmação que eles limitam. Evite uma seção final que tenta compensar excesso de certeza já espalhado no texto.
9. Feche retornando à decisão do leitor: o que muda agora, o que continua incerto e qual informação seria necessária para mudar a leitura.

## Linguagem e tom

Escreva em português brasileiro natural, direto e específico. Prefira verbos observáveis: “associou-se”, “estimou”, “recomendou”, “não demonstrou”, “sugere”. Evite fórmulas como “é importante ressaltar”, “vale destacar”, “revolucionário”, “definitivamente” e uma lista de ressalvas sem hierarquia.

Não reescreva semanticamente termos que carregam precisão: população, dose, escala, intervalo, certeza da evidência, força da recomendação, efeito relativo/absoluto e qualificadores temporais. Preserve as condições comerciais, clínicas e científicas do material fonte.

## Tabelas e recomendações

Para cada recomendação, construa uma linha completa com população/cenário, intervenção ou conduta, comparador quando houver, direção/força, certeza, condições, exceções e fonte-localizador. Uma célula vazia não autoriza inferência. Se a recomendação depende de um fluxograma, remeta ao fluxograma e declare a dependência.

Antes de inserir uma tabela, valide-a com `python scripts/validate_tables.py <arquivo>`. Corrija a fonte, não a tabela, quando a informação original for ambígua.

## Auto-revisão antes de enviar à auditoria

- Cada número sensível consta do claim ledger e conserva unidade e denominador?
- O título e o lead resistem à pergunta “qual é a fonte exata desta promessa?”
- Resultados, inferências e hipóteses estão linguisticamente distintos?
- Os limites mais relevantes estão no corpo, e não escondidos no rodapé?
- O leitor consegue identificar para quem a conclusão vale e para quem não vale?
- A edição responde à decisão proposta pelo brief sem fabricar uma controvérsia?

Entregue o rascunho com a lista de afirmações que exigem auditoria independente. Não faça a auditoria nesta skill.
