---
name: reviews-editorial-brief
description: Use para converter evidência e avaliação já validadas em um brief editorial rastreável do Reviews: tipo de edição, pergunta, ângulo proporcional, seleção de claims, contexto, título, lead, nut graf, estrutura e limites de redação antes da candidata.
---

# Brief editorial operacional do Reviews

## Propósito, gatilhos e fronteira

O brief toma decisões editoriais antes da prosa. Ele traduz uma pergunta e uma
avaliação científica em seleção, ordem, tensão e função de leitura, sem
aumentar a evidência nem imitar a estrutura de um exemplar sem necessidade.

Use quando os gatilhos forem:

- “qual é o ângulo?”, “o que entra na edição?”, “fazer o brief”, “escolher
  título/lead” ou “organizar o texto antes de escrever”;
- há um claim ledger liberado, um bottom line e a pauta precisa de tipo de
  edição, hierarquia de resultados ou condições de título;
- reviews-journalistic-framing identificou contexto, conflito, contraste ou
  não-notícia que deve orientar a leitura;
- uma candidata está redundante, promete mais que a evidência ou perde a
  pergunta central e precisa ser replanejada.

Não use para extrair dados, corrigir números, declarar risco de viés, escrever
parágrafos finais, substituir revisão humana ou fabricar relevância atual. Se a
pergunta, claim central ou limite de inferência ainda não está resolvido, volte
a reviews-source-provenance ou reviews-scientific-appraisal.

## Entradas obrigatórias, pré-condições e gates

Exija:

1. extraction/claim-ledger.json com claims liberados e source map;
2. analysis/methodological-review.json, inference-boundaries.md e
   bottom-line.yaml;
3. análise de tipo de edição ou escolha explícita do editor;
4. descrição do leitor e da decisão clínica ou intelectual;
5. planning/journalistic-framing.md quando houver contexto jornalístico,
   controvérsia, conflito, mudança temporal ou contraponto material.

Leia AGENTS.md, editorial/audience.md, editorial/source-rules.md,
editorial/style/titles-and-subtitles.md e o contrato do tipo de edição
selecionado. Leia também corpus/reviews-human-style-evidence.json: ele é
evidência graduada de finais e correções humanas, não especificação canônica.
Depois leia references/brief-contract.md e
references/brief-decision-matrix.md. Use
references/examples-and-evals.md ao testar alternativas ou bordas.

Referências diretas obrigatórias: [contrato do brief](references/brief-contract.md),
[matriz de decisão](references/brief-decision-matrix.md) e
[exemplos e evals](references/examples-and-evals.md).

Hierarquia: claim ledger e appraisal controlam o que pode ser dito; framing
controla por que e em que contexto isso é lido; contrato de edição controla
estrutura; autoridade editorial e correções humanas controlam regra de forma;
exemplares A/B orientam solução, jamais fatos ou promessas. Uma sugestão de
headline não supera um limite de inferência.

## Fontes, decisões e critérios de julgamento

Hierarquia: claim ledger e appraisal controlam o que pode ser dito; framing
controla por que e em que contexto isso é lido; contrato de edição controla
estrutura; autoridade editorial e correções humanas controlam regra de forma;
exemplares A/B orientam solução, jamais fatos ou promessas. Uma sugestão de
headline não supera um limite de inferência.

## Procedimento operacional

### 1. Fixar ou recomendar o tipo de edição

Respeite escolha explícita do editor salvo incompatibilidade crítica, que deve
ser registrada sem apagar o override. Sem escolha, crie
planning/edition-routing.json com contexto explícito e execute:

    python scripts/edition_router.py <context.json> --output <job_dir>/planning/edition-routing.json

Se o comando indicar requires_editor_review, não finja decisão final: registre
alternativas, incompatibilidade e decisão humana necessária. Leia o contrato do
tipo selecionado e inclua apenas módulos cuja função é necessária.

### 2. Escrever a pergunta, leitor e decisão

Defina uma pergunta central respondível pelas fontes, o leitor real e a decisão
clínica ou intelectual em jogo. Se a edição é conceitual, declare sua função
em vez de inventar uma conduta. Delimite população, comparação, desfecho e
tempo quando isso protege a interpretação.

O leitor deve sair sabendo o que foi perguntado, o que foi comparado, o que
importa, onde está a incerteza e o significado prático permitido. Explique
método apenas quando ele muda essa leitura.

### 3. Escolher o ângulo sem inflar a novidade

Preencha, com links a claims ou issues:

- por que o tema importa agora;
- o que mudou de fato, ou que não houve mudança;
- tensão central entre achado, incerteza, decisão, dano, aplicabilidade ou
  desacordo;
- takeaway mais forte permitido;
- incerteza mais importante;
- risco de contexto, incentivo, conflito ou narrativa secundária.

“Novo”, “revolucionário”, “muda tudo” e “resolve” não são ângulos. Se não há
novidade material, o ângulo pode ser esclarecer um limite, uma decisão
condicional ou uma pergunta mal compreendida.

### 4. Selecionar claims e omissões de modo justificável

Crie planning/selection-rationale.md. Para cada item escolhido ou omitido,
registre função, claim_id, fonte, prioridade e motivo. Priorize desfecho
primário, resultado crítico para a decisão, segurança, sensibilidade que muda
a leitura, contraponto material e contexto necessário para não distorcer.

Inclua em must_not_claim toda inferência bloqueada, salto de causalidade,
generalização indevida, número sem contexto, mecanismo não demonstrado,
recomendação sem condição e controvérsia não verificada. Não use completude
aparente como critério para listar todos os resultados.

### 5. Planejar contexto, conflito e contraponto

Para cada item de contexto_needed, diga qual pergunta ele responde, fonte,
autoridade, data, limite e onde entra. Para fonte de incentivo/conflito,
registre relevância editorial sem insinuar motivo ou invalidar resultado
automaticamente. Para desacordo, identifique escopo, data, método, população,
evidência e valores antes de chamar de conflito.

Não crie controvérsia artificial, falsa equivalência ou “os dois lados” quando
as fontes não têm a mesma qualidade e relevância.

### 6. Delinear título, lead, nut graf e fecho

Crie planning/title-options.md com até três opções e teste cada uma contra
pergunta, população, desfecho, certeza e body. O título identifica a pergunta
ou tensão; o subtítulo delimita o que for necessário. Não use título
grandioso, clickbait, pergunta retórica que o texto não responde ou precisão
que o corpo não sustenta.

Defina:

- lead_strategy: primeira informação de maior valor para o leitor;
- nut_graf: pergunta, escopo, tensão e por que a leitura continua;
- ending_function: implicação, incerteza, monitoramento, decisão condicional
  ou pergunta realmente aberta.

O fecho não deve apenas repetir a abertura com outras palavras.

Quando compatível com a pauta, aplique as observações derivadas do corpus:
REV-STYLE-001 para abrir por decisão/problema/limite em vez de importância
abstrata; REV-STYLE-002 para título clínico proporcional e subtítulo sem
autoqualificação vazia; REV-STYLE-004 para fecho que acrescente aplicabilidade
ou incerteza. Registre a observação e a fronteira usada em
planning/selection-rationale.md; não trate frequência editorial como regra
automática.

Quando compatível com a pauta, aplique as observações derivadas do corpus:
REV-STYLE-001 para abrir por decisão/problema/limite em vez de importância
abstrata; REV-STYLE-002 para título clínico proporcional e subtítulo sem
autoqualificação vazia; REV-STYLE-004 para fecho que acrescente aplicabilidade
ou incerteza. Registre a observação e a fronteira usada em
planning/selection-rationale.md; não trate frequência editorial como regra
automática.

### 7. Compor a arquitetura por função

Crie planning/outline.md. Cada seção precisa ter função, claims permitidos,
pergunta a que responde, material de transição e condição de saída. A ordem
deve sustentar: pergunta para desenho; desenho para resultado; resultado para
significado; benefício para dano/limite; evidência para implicação.

Não crie subtítulos apenas para segmentar texto. Em tipos de edição com títulos
ou sequência pendentes, registre a decisão como pendente para o editor em vez
de canonizar uma preferência local.

### 8. Preencher, validar e transferir o brief

Preencha planning/editorial-brief.json com todos os campos do schema e execute:

    python scripts/validate_schema.py <job_dir>/planning/editorial-brief.json --schema editorial-brief

Crie planning/handoff-to-writing.md com edição selecionada, outline, claims
liberados, claims proibidos, números que pedem contexto, modalidade e gates de
auditoria. Transfira somente esse pacote a reviews-edition-writing.

## Contrato de saída, artefatos e ferramentas

| Artefato | Função | Gate objetivo |
| --- | --- | --- |
| planning/edition-routing.json | escolha, recomendação ou override | incompatibilidade não é escondida |
| planning/editorial-brief.json | contrato editorial estruturado | valida contra editorial-brief.schema.json |
| planning/selection-rationale.md | inclusão e omissão por claim | cada resultado prioritário é decidido |
| planning/title-options.md | títulos proporcionais, não finais automáticos | cada opção passa matriz de título |
| planning/outline.md | ordem por função e transição | nenhuma seção sem propósito |
| planning/handoff-to-writing.md | limites transferidos para a redação | só contém claims liberados |

O detalhamento de cada campo, inclusive como registrar ausência e contexto, está
em references/brief-contract.md.

## Stop conditions e caminho degradado

Pare o planejamento se o claim central estiver bloqueado, se headline/ângulo
exigir afirmação não autorizada, se tipo de edição estiver incompatível sem
decisão do editor, se uma controvérsia relevante não estiver rastreada ou se
faltarem contexto e fonte necessários para evitar leitura enganosa.

Em modo degradado, reduza o escopo a uma pergunta que as fontes realmente
respondem, declare a cobertura ausente e mantenha o texto em formato de
contexto/explicação. Não preencha campos com linguagem genérica para fazer o
schema passar, não transforme ausência de evidência em decisão prática e não
crie uma estrutura fixa para uma edição que exige decisão humana.

## Proibições

É proibido:

- usar exemplar como evidência, título como conclusão ou novidade como prova;
- incluir número sem população, comparação, unidade, tempo ou localizador
  necessário;
- omitir segurança, incerteza ou contraprova material para proteger o ângulo;
- transformar recomendação condicional em regra universal;
- apresentar crítica externa como fato ou tratar conflito de interesse como
  prova de viés no resultado;
- redigir a candidata durante o brief ou aprovar publicação.

## Interação com outras skills

reviews-scientific-appraisal e reviews-journalistic-framing alimentam esta
skill. Ela entrega pacote limitado a reviews-edition-writing. reviews-audit
verifica se a candidata respeitou must_not_claim, título, estrutura e seleção;
reviews-feedback-learning pode propor uma preferência futura, mas não altera o
brief sem decisão humana.

## Evals, exemplos e casos adversariais

references/examples-and-evals.md traz três exemplos concretos e três casos
adversariais. evals/cases.json contém positivo, negativo, limite e regressão.
Execute o roteador e a validação de schema com um job-fixture, compare os
artefatos aos critérios objetivos e registre a evidência. Aprovação exige que
os quatro casos gerem brief válido, seleção rastreável e nenhum headline ou
claim que exceda a evidência.

## Checklist operacional executável

- Confirme que a pergunta, os claims e o bottom line chegaram liberados.
- Roteie o tipo de edição ou registre o override humano e sua incompatibilidade.
- Selecione claims e omissões com razão, função e modalidade explícitas.
- Crie title options, outline e handoff limitados pelos claims permitidos.
- Valide o brief estruturado contra o schema editorial-brief.
- Bloqueie a redação se o título, ângulo ou contexto pedir afirmação não autorizada.
