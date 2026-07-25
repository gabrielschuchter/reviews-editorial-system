# Tipos de edição

## Status dos contratos

O registro atual contém sete tipos. Todos os contratos estão em estado provisório, podem ser usados no MVP e aguardam aprovação editorial. Eles derivam do prompt mestre, não de uma curadoria concluída do corpus.

O editor pode definir o tipo. Quando não define, o sistema recomenda um tipo, explica a decisão e preserva a possibilidade de override. Misturas silenciosas são proibidas.

## Registro

| ID | Uso principal | Gate específico |
|---|---|---|
| `clinical-answer-classic` | Pergunta clínica direta com resposta breve seguida de síntese | Evitar quando resposta e resultados gerarem redundância substancial |
| `clinical-answer-analytical` | Resposta clínica com métodos, achados e crítica em sequência | Títulos de algumas seções ainda são candidatos |
| `guideline-summary` | Recomendações centrais de guideline | Versão correta da diretriz precisa estar confirmada |
| `systematic-review-critical` | Revisão sistemática ou metanálise que exige análise extensa | Fonte central precisa ser revisão sistemática/metanálise |
| `clinical-protocol` | Informação organizada por decisões de conduta | Fontes precisam sustentar o nível operacional de orientação |
| `thematic-narrative` | Tema com múltiplas fontes, controvérsia ou questão conceitual | Estratégia e seleção documental explícitas |
| `primary-study-deep-dive` | Estudo primário que exige análise além de uma resposta comum | Estudo central e pacote metodológico validados |

Os contratos ficam em `editorial/edition-types/`. `registry.yml` governa seleção e combinação; cada arquivo específico governa conteúdo e restrições do tipo.

## Comportamento real do roteador

`src/reviews_editorial/edition_router.py` considera atualmente:

- tipo solicitado;
- desenho do estudo;
- número de artigos;
- objetivo;
- complexidade metodológica;
- suporte documental para conduta;
- prioridade dada à análise crítica.

Ele ainda não automatiza todos os fatores previstos pelo registro, como volume de resultados, existência de guideline como fonte secundária, natureza temática detalhada e extensão desejada. Esses fatores devem entrar no plano editorial do Codex até que o contrato do roteador seja ampliado e testado.

A ordem prática atual é:

1. aceitar o tipo explícito válido do editor;
2. sinalizar incompatibilidade crítica em guideline, revisão sistemática ou protocolo;
3. recomendar guideline para uma diretriz confirmada;
4. recomendar protocolo quando o objetivo é conduta e as fontes a sustentam;
5. recomendar análise crítica para revisão sistemática/metanálise complexa ou com foco crítico;
6. recomendar narrativa temática para múltiplas fontes sem estudo central definido;
7. recomendar deep dive para estudo primário complexo;
8. respeitar pedido de resposta clássica;
9. usar a resposta analítica como fallback conservador.

Uma incompatibilidade retorna `requires_editor_review: true`; não autoriza o agente a adaptar o tipo silenciosamente.

## Contratos resumidos

### Resposta clínica clássica

Sequência definida: título, subtítulo, introdução, pergunta e resposta clínica, síntese da evidência e implicações. A resposta prioriza desfechos primários e segurança, traz estimativa e intervalo quando disponíveis e não caracteriza magnitude sem valores e critério. A interpretação clínica deve explicar os números sem repeti-los mecanicamente.

### Resposta clínica analítica

Sequência-base: título, subtítulo, introdução, síntese inicial, métodos e inferência, principais achados, análise crítica e discussão ou implicações quando necessárias. A conclusão pode aparecer na síntese, no final da crítica ou na seção opcional, mas precisa ser clara.

O título de `study-methods-and-inference` está pendente. As alternativas são:

- `O que o estudo fez`;
- `Como o estudo investigou a questão`;
- `Como a questão foi investigada`.

`Principais achados` e `Análise crítica` são bons candidatos, não títulos canônicos aprovados.

### Síntese de diretriz

Organiza população, ação recomendada, contexto, força, certeza, exceções, contraindicações, monitoramento e mudanças relevantes. Não resume a diretriz inteira, não cria recomendações e não equipara recomendação forte a evidência de alta certeza.

### Revisão sistemática crítica

Avalia pergunta, elegibilidade, busca, seleção, extração, risco de viés, síntese, heterogeneidade, modelos, efeitos absolutos, certeza, publicação seletiva, multiplicidade, subgrupos e robustez. Cada crítica material precisa indicar sua consequência interpretativa.

### Protocolo clínico

Pode organizar identificação, avaliação, exames, diagnóstico, opções, contraindicações, acompanhamento, falha, encaminhamento e segurança. Inclui somente módulos sustentados e relevantes. Lacunas não podem ser preenchidas por plausibilidade clínica.

### Narrativa temática

Exige estratégia documental registrada, seleção explícita, hierarquia das fontes e limites de escopo. Uma seleção narrativa nunca deve ser apresentada como busca exaustiva.

### Deep dive de estudo primário

Pode incluir racional, método, resultados, análise estatística, crítica, relação com a literatura, implicações e perguntas não respondidas. A arquitetura é escolhida conforme o estudo; reproduzir todo o artigo ou promover desfechos exploratórios é proibido.

## Combinações controladas

O registro permite sobreposição, mas o roteador Python seleciona apenas um tipo-base. Uma combinação precisa ser planejada manualmente e registrar:

- tipo-base e overlays;
- motivo;
- origem de cada seção;
- conflitos encontrados e resolução;
- autoridade que aprovou.

Sem esse registro, o job deve permanecer bloqueado no planejamento.

## Inputs comuns e saída do planejamento

Antes da seleção final devem existir classificação documental, desenho, pacote de evidências, números verificados, análise metodológica e limites de inferência. O planejamento deve produzir:

- `planning/edition-selection.md`;
- `planning/editorial-outline.md`;
- `planning/selected-exemplars.yml`;
- `planning/content-selection.md`.

`content-selection.md` registra por que cada resultado entrou ou foi omitido. Significância estatística, destaque dos autores e facilidade de explicação não são critérios suficientes.

## Decisões pendentes

- canonização dos contratos e de seus nomes exibidos;
- título definitivo da Seção I do modelo analítico;
- títulos e ordem dos tipos flexíveis;
- critérios editoriais para combinações recorrentes;
- posição preferencial do modelo analítico depois dos pilotos;
- extensão e densidade esperadas em cada tipo com base em exemplares A/B.
