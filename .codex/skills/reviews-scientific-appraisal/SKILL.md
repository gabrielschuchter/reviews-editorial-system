---
name: reviews-scientific-appraisal
description: Use depois de reviews-source-provenance para avaliar, por resultado, desenho, estimativa, risco de viés, certeza, relevância clínica, aplicabilidade e limites de inferência de ensaio, estudo observacional, revisão, metanálise ou diretriz do Reviews.
---

# Avaliação científica orientada por resultado

## Propósito e gatilhos

Esta skill converte extração rastreável em julgamento explícito. Ela avalia o
resultado e a pergunta respondida, não atribui uma nota global ao artigo. Cada
crítica precisa indicar o resultado/claim afetado, a fonte, o mecanismo,
consequência plausível, direção quando inferível e impacto na conclusão.

Use quando ocorrer qualquer um destes gatilhos:

- “avaliar risco de viés”, “o estudo permite causalidade?”, “quão certa é a
  evidência?” ou “isso muda conduta?”;
- há um ensaio, estudo observacional, revisão sistemática, metanálise ou
  diretriz com claims já extraídos;
- o brief precisa de bottom line, limites de inferência, efeitos absolutos,
  contraponto metodológico ou condições de uma recomendação;
- revisão factual encontrou subgrupo, multiplicidade, dados ausentes, desfecho
  substituto, conflito de fontes ou possível extrapolação.

Não use para localizar fontes, ajustar estilo, escolher título, reescrever
texto ou declarar aprovação editorial. Sem claim ledger e localizadores
validados, volte a reviews-source-provenance em vez de emitir julgamento.

## Entradas obrigatórias, pré-condições e gates

Exija:

1. job com documentos normalizados e revisão humana concluída ou limitação
   explicitamente bloqueante;
2. extraction/claim-ledger.json, extraction/number-verification.json e
   extraction/source-map.md;
3. pergunta editorial, tipo de fonte/desenho e resultados prioritários;
4. acesso ao texto completo e aos materiais necessários para a pergunta;
5. identificador de estudo e IDs dos claims que a análise poderá afetar.

Leia editorial/constitution.md, editorial/clinical-interpretation.md,
editorial/methodology/general-principles.md e o módulo do desenho pertinente.
Depois leia references/judgment-contract.md e
references/design-routing.md. Para risco de viés e certeza, carregue
references/rob-grade-boundaries.md; para treino de decisão e bordas, carregue
references/examples-and-evals.md.

Use schemas/scientific-appraisal.schema.json e
scripts/validate_scientific_appraisal.py para o julgamento consolidado por
desfecho; o validador exige fontes localizáveis e human_judgment_required=true.

Referências diretas obrigatórias: [contrato de julgamento](references/judgment-contract.md),
[roteamento por desenho](references/design-routing.md),
[limites de RoB 2 e GRADE](references/rob-grade-boundaries.md) e
[exemplos e evals](references/examples-and-evals.md).

Não atribua baixo risco, alta certeza, ausência de problema ou recomendação
forte se o material necessário não está disponível. Falta de relato é falta de
relato; não prova falha de condução.

## Hierarquia de fontes, decisões e critérios de julgamento

Para o que aconteceu no estudo, use a fonte primária e seus materiais
associados. Para como julgar um domínio, use autoridade metodológica; ela não
substitui resultados. Para uma recomendação, preserve a formulação, a força,
a certeza, as condições e o contexto declarados pela diretriz. Para crítica
externa, mantenha atribuição e classificação verificável.

corpus/reviews-human-style-evidence.json pode orientar a clareza da transferência
para o leitor, mas não muda risco de viés, certeza, efeito, causalidade ou
recomendação. Se uma correção humana sugerir linguagem mais direta, preserve a
mesma modalidade e mantenha o julgamento científico ancorado nas fontes.

corpus/reviews-human-style-evidence.json pode orientar a clareza da transferência
para o leitor, mas não muda risco de viés, certeza, efeito, causalidade ou
recomendação. Se uma correção humana sugerir linguagem mais direta, preserve a
mesma modalidade e mantenha o julgamento científico ancorado nas fontes.

A unidade é:

    pergunta + população + intervenção/exposição + comparador + desfecho + tempo + estimando

Não transporte um julgamento de risco de viés ou certeza para outro desfecho
sem justificar a equivalência.

## Procedimento operacional

### 1. Delimitar a pergunta e classificar o desenho

Registre em analysis/study-classification.json o desenho, variante relevante,
fonte do dado, população analisada, pergunta respondível e perguntas que o
material não responde. Em seguida escolha a rota em
references/design-routing.md.

Confirme se a comparação é entre grupos, se o tempo está correto, se o
estimando é causal/descritivo/prognóstico/diagnóstico e se o desfecho é
clínico, substituto ou composto. Associação, predição e mecanismo são
conclusões diferentes.

### 2. Criar a ficha por resultado prioritário

Para cada desfecho primário, desfecho crítico para decisão, evento adverso
relevante e sensibilidade decisiva, registre:

- claim_id e localizadores;
- comparação, população, tempo e população de análise;
- medida, unidade, estimativa, intervalo e direção;
- risco basal e efeito absoluto quando fornecidos ou quando um cálculo
  reproduzível foi documentado;
- estatuto: confirmatório, secundário, exploratório ou não determinável;
- relevância para o leitor e o que permanece fora da pergunta.

Revise números com o artefato de proveniência; execute novamente, se houve
alteração:

    python scripts/verify_numbers.py <job_dir>

Não escolha o menor valor de p, o tempo mais favorável ou a escala que produz
o melhor resultado.

### 3. Examinar validade interna e seletividade

Use o roteiro do desenho, não uma lista genérica de limitações. Em ensaios,
examine randomização, ocultação, desvios, mensuração, perdas, seleção de
resultado e análise. Em observacionais, examine tempo zero, seleção,
mensuração, confundimento, ajuste, temporalidade e causalidade reversa. Em
revisões e metanálises, examine pergunta, busca, seleção, risco de viés,
compatibilidade, síntese, heterogeneidade e evidência ausente.

Para cada problema material, crie um objeto em
analysis/methodological-issues/<issue_id>.json conforme
methodological-issue.schema.json e valide:

    python scripts/validate_schema.py <issue_file> --schema methodological-issue

O resumo legível vai em analysis/methodological-review.json e
analysis/critical-issues.md. Não alegue que o arquivo-resumo valida contra o
schema individual.

### 4. Avaliar precisão, multiplicidade e dados ausentes

Interprete estimativa e intervalo; p maior que 0,05 não demonstra ausência de
efeito e teste de superioridade não significativo não demonstra equivalência.
Faça um mapa de desfechos, tempos, grupos, subgrupos, modelos e contrastes
antes de chamar um achado de confirmatório.

Para dados ausentes, registre proporção, motivos, distribuição entre grupos,
população efetivamente analisada, pressupostos de imputação e sensibilidades.
Para subgrupos, exija contraste de interação ou equivalente; significância em
um estrato e não no outro não demonstra diferença entre estratos.

### 5. Julgar relevância clínica e aplicabilidade

Separe significância estatística de importância clínica. Examine desfecho,
magnitude, intervalo, efeitos absolutos quando disponíveis, duração,
segurança, carga, comparador e limiar de importância apenas quando sua origem
for documentada.

Para transportabilidade, identifique população-alvo, diferença concreta,
modificador de efeito plausível, motivo e população que fica fora da
inferência. “Amostra não representativa” sozinho não é crítica suficiente nem
falha automática de validade interna.

Desfecho substituto permanece marcador até haver suporte específico para o
benefício clínico. Nomeie o marcador, sua escala e o salto inferencial que não
é permitido.

### 6. Tratar certeza e recomendações

Avalie certeza por desfecho e comparação, não pelo prestígio do periódico ou
pelo desenho isolado. Quando uma fonte usa GRADE ou método formal, registre
método, autoria, desfecho, categoria e justificativa, e confira se se aplicam
ao resultado discutido.

Quando não houver método formal completo, descreva os domínios concretos sem
inventar rótulos alta, moderada, baixa ou muito baixa. Para diretrizes, separe:
resultado dos estudos, certeza, balanço de benefícios e danos, recomendação,
força/condicionalidade, valores, recursos, viabilidade e aplicabilidade local.

### 7. Delimitar inferências e bottom line

Crie analysis/inference-boundaries.md com uma linha por claim relevante:

    claim_id | categoria | sustentação | limite | modalidade permitida | bloqueio

Produza analysis/bottom-line.yaml:

    bottom_line:
    certainty:
    main_reason:
    main_limitation:
    practical_meaning:

Cada campo precisa apontar para claims e issues; nenhum pode transformar
resultado exploratório, marcador, associação ou recomendação condicional em
certeza, benefício clínico, causalidade ou regra universal.

Consolide as fichas em analysis/scientific-appraisal.json e valide:

    python scripts/validate_scientific_appraisal.py <job_dir>/analysis/scientific-appraisal.json --output <job_dir>/analysis/scientific-appraisal-validation.json

O arquivo consolidado requer appraisal_id, job_id, study_id, design,
outcome_appraisals, cross_cutting, human_judgment_required=true e provenance.
Não use a ferramenta para substituir a leitura por desfecho: ela rejeita
estrutura incompleta, mas a justificativa continua humana e rastreável.

### 8. Aplicar gate e transferir

Libere reviews-journalistic-framing e reviews-editorial-brief somente quando
cada claim prioritário tiver categoria, estimativa conferida, limite de
inferência, implicação de relevância e destino no bottom line. Marque
explicitamente quais frases são permitidas, condicionais ou bloqueadas.

## Contrato de saída, artefatos e ferramentas

| Artefato | Conteúdo mínimo | Verificação |
| --- | --- | --- |
| analysis/study-classification.json | desenho, pergunta, estimando e rota | revisão contra fonte e rota |
| analysis/methodological-issues/*.json | cada questão específica e vinculada | schema methodological-issue |
| analysis/methodological-review.json | síntese por resultado e links aos issues | campos do contrato de referência |
| analysis/scientific-appraisal.json | julgamento consolidado por desfecho | validador científico aprovado |
| analysis/scientific-appraisal-validation.json | evidência de validação estruturada | valid=true, sem omitir julgamento humano |
| analysis/inference-boundaries.md | claim, limite e modalidade permitida | nenhum claim prioritário sem linha |
| analysis/bottom-line.yaml | certeza, razão, limite e significado | todos os campos rastreáveis |
| analysis/critical-issues.md | bloqueios, discrepâncias e material necessário | críticos impedem avanço |

Um issue crítico exige blocks_progress=true. Crítica externa requer classificação
explícita. O contrato detalhado está em references/judgment-contract.md.

## Stop conditions e caminho degradado

Bloqueie a edição se estiver indefinido o desfecho primário relevante, a
comparação, a direção, a população de análise, o material necessário para
avaliar uma questão crítica, ou se houver discrepância não resolvida que altere
o claim. Também bloqueie conclusão causal quando o desenho e as informações
não sustentam temporalidade, comparabilidade ou pressupostos necessários.

Em modo degradado, descreva estritamente a cobertura disponível: por exemplo,
“o relato não permite avaliar seleção do resultado” ou “o efeito clínico não
foi medido”. Produza limite de inferência, não um veredito de baixo risco,
ausência de viés ou ausência de efeito. Não use a falta de protocolo,
suplemento ou registro para presumir tanto qualidade quanto falha.

## Proibições

É proibido:

- converter associação em causalidade sem justificação;
- converter mudança intragrupo em efeito comparativo;
- chamar resultado não significativo de equivalência;
- chamar marcador de benefício clínico;
- inferir força de recomendação a partir de certeza, ou certeza a partir de
  força;
- fazer crítica vaga sem resultado, mecanismo e consequência;
- aplicar GRADE ou RoB 2 como rótulo decorativo ou nota do artigo inteiro;
- recalcular metanálise mentalmente ou ocultar cálculo derivado.

## Interação com outras skills

Esta skill recebe facts e IDs de reviews-source-provenance. Ela entrega
fronteiras para reviews-journalistic-framing e um bottom line para
reviews-editorial-brief. reviews-edition-writing só recebe claims liberados e
sua modalidade; reviews-audit pode reabrir issues, mas não os corrige sem uma
nova avaliação.

## Evals, exemplos e casos adversariais

references/examples-and-evals.md contém três exemplos concretos e três casos
adversariais. evals/cases.json contém quatro casos versionados: positivo,
negativo, limite e regressão. Execute os comandos de verificação do
procedimento sobre um job-fixure, compare os artefatos aos critérios objetivos
e registre o resultado. Aprovação exige que os quatro casos preservem a
categoria do claim, a modalidade e o bloqueio exigido; JSON válido isolado não
é evidência de julgamento correto.

## Checklist operacional executável

- Confirme a pergunta, o desenho, o estimando e os claims afetados.
- Registre uma ficha por resultado prioritário antes de emitir conclusão.
- Verifique estimativa, intervalo, unidade, grupo, tempo e população analisada.
- Crie e valide um issue para cada problema metodológico material.
- Compare a modalidade do bottom line com as fronteiras de inferência.
- Bloqueie a transferência quando um issue crítico ou informação essencial ficar aberto.
