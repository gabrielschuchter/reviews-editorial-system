---
name: reviews-journalistic-framing
description: Use depois da proveniência e da avaliação científica para definir por que uma edição importa agora, qual tensão real ela esclarece, que contexto e contraponto são necessários e quais limites jornalísticos devem orientar brief, título, lead e estrutura sem inflar a evidência.
---

# Framing jornalístico proporcional do Reviews

## Propósito e gatilhos

Esta skill transforma evidência já avaliada em uma pergunta editorial legível:
qual decisão, mudança, incerteza ou desacordo real merece atenção e qual
contexto permite entendê-lo. Ela não cria notícia, não transforma incerteza em
polêmica e não altera a força da conclusão científica.

Use quando o pedido incluir:

- “por que isso importa agora?”, “qual é a história?”, “enquadrar a pauta”,
  “dar contexto”, “há conflito?” ou “qual deve ser o lead?”;
- uma fonte nova, diretriz atualizada, correção, crítica externa, decisão
  clínica, mudança de prática ou controvérsia exige leitura contextualizada;
- o brief precisa diferenciar mudança real, contexto histórico, contraponto
  relevante e ângulo proporcional;
- uma candidata parece promocional, sem tensão, artificialmente controversa ou
  desconectada da decisão do leitor.

Não use para extrair resultados, classificar risco de viés, substituir a
checagem de fontes, redigir a edição completa, otimizar para clique ou declarar
um fato sem claim liberado. Em pauta exclusivamente técnica sem questão de
leitura, faça o brief direto e registre que não há framing adicional necessário.

## Gates, entradas e fontes

Exija:

1. extraction/claim-ledger.json e extraction/source-map.md;
2. analysis/inference-boundaries.md e analysis/bottom-line.yaml;
3. lista de fontes contextuais, quando houver, com papel, data e localizador;
4. leitor e decisão que a edição pode ajudar a compreender;
5. edição/tipo pretendido ou insumos para o roteador;
6. corpus/reviews-human-style-evidence.json para usar aprendizagem humana de
   abertura, título e fecho, com as fronteiras de cada observação.

Leia editorial/source-rules.md, editorial/audience.md,
editorial/style/titles-and-subtitles.md e
editorial/style/transitions-and-cohesion.md, depois leia
references/framing-contract.md e references/framing-taxonomy.md. Carregue
references/examples-and-evals.md para casos de borda.

Referências diretas obrigatórias: [contrato de framing](references/framing-contract.md),
[taxonomia de enquadramento](references/framing-taxonomy.md) e
[exemplos e evals](references/examples-and-evals.md).

Use schemas/framing-memo.schema.json e scripts/validate_framing.py para
verificar que headline, contraponto e limite de evidência permanecem ligados ao
claim ledger.

Hierarquia: fonte primária e claim ledger determinam o que ocorreu; appraisal
determina o que se pode inferir; fontes oficiais e contextuais apenas
complementam a leitura; escrutínio externo permanece atribuído/classificado;
o corpus humano orienta função e clareza, não fatos ou força de evidência.

## Fontes, decisões e critérios de julgamento

Toda decisão de framing deve indicar se é dado, resultado, evidência,
inferência, hipótese ou crítica externa. Escolha o top line somente depois de
comparar força, atualidade, aplicabilidade, contraponto e incerteza; em empate
aparente, preserve a assimetria de autoridade em vez de inventar equilíbrio.

## Procedimento operacional

### 1. Fixar a pergunta jornalística

Escreva uma frase para cada item:

- decisão ou entendimento que o leitor precisa formar;
- pergunta científica e limites que a fonte realmente responde;
- população/contexto a que a edição se aplica;
- consequência de interpretar o resultado além do permitido.

Se não houver decisão prática, defina a função intelectual: explicar uma
incerteza, destrinchar uma diretriz, revisar uma controvérsia documentada ou
corrigir uma interpretação comum. Não force uma narrativa de urgência.

### 2. Classificar o motivo de atualidade

Classifique um único motivo principal e, se necessário, motivos secundários:

- evidência nova ou atualização verificável;
- recomendação, versão ou condição nova;
- correção, retratação ou discrepância reconhecida;
- contexto de decisão persistente, sem novidade;
- controvérsia documental com consequência material;
- não há mudança material.

Para cada um, registre fonte, data, claim_id, localizador e o que ele não
prova. “Publicado recentemente” não equivale a mudança de prática; “não há
mudança material” é resultado editorial válido.

### 3. Construir o mapa de contexto e contraponto

Crie planning/context-source-log.json com uma entrada por contexto:

    context_id, question_answered, source_id, source_role, date_accessed,
    authority, claim_ids, locator, limitation, inclusion_decision

Procure o mínimo de contexto que impede distorção: prática/decisão vigente,
população não coberta, dano, versão anterior, fonte concorrente, discrepância
ou crítica relevante. Compare desacordos por escopo, data, pergunta, método,
população, valores e condições; não apenas por conclusão.

Não afirme que nenhuma crítica ou atualização existe sem busca com data
registrada. Caso uma fonte externa altere um claim, devolva-a para
reviews-source-provenance antes de usá-la aqui.

### 4. Formular a tensão e o top line

Escolha uma tensão verificável, não um slogan. Formas comuns:

- benefício possível versus incerteza/segurança;
- recomendação prática versus condições de aplicabilidade;
- estimativa promissora versus limite de desenho;
- marcador alterado versus benefício clínico não medido;
- nova versão versus o que de fato mudou;
- desacordo documentado versus assimetria de evidência.

Escreva:

    top_line_supported:
    tension:
    evidence_that_supports_it:
    uncertainty_that_qualifies_it:
    claims_explicitly_excluded:

Todos os itens devem remeter a claim_id ou issue_id. Se não houver tensão
material, use enquadramento explicativo simples, sem fabricar conflito.

### 5. Definir o arco de leitura

Planeje a sequência: abertura pela decisão, problema ou limite aplicável; nut
graf delimitando pergunta/escopo/tensão; desenvolvimento que liga desenho a
resultado e resultado a significado; contraponto quando ele muda a decisão;
fecho com aplicabilidade, incerteza ou limite de escopo.

Use corpus/reviews-human-style-evidence.json como evidência graduada:

- REV-STYLE-001 favorece abertura pela decisão/problema/limite, não por
  importância abstrata;
- REV-STYLE-002 exige títulos clínicos e proporcionais, sem autoqualificação
  vazia no subtítulo;
- REV-STYLE-004 favorece fecho que acrescenta aplicação ou limite, desde que
  ele não remova condição, exceção, dano ou decisão nova.

Essas observações não são fórmulas; aplique somente quando compatíveis com a
fonte, tipo de edição e pergunta.

### 6. Produzir guardrails de título, lead e contexto

Crie planning/journalistic-framing.md com opções de enunciado, não texto final.
Para cada título/lead possível, indique:

- claim ou decisão que o sustenta;
- população, comparação, desfecho e tempo que precisam aparecer ou limitar;
- modalidade autorizada;
- contexto indispensável;
- palavra, promessa ou oposição proibida;
- condição que deve aparecer antes do fecho.

Rejeite título que prometa causalidade, benefício líquido, universalidade,
urgência ou resolução de controvérsia não sustentadas. Rejeite lead que usa
pergunta retórica sem resposta real, hiperbole ou falso equilíbrio.

Crie também planning/framing-memo.json com central_tension, reader_decision,
headline_options, selected_angle, counterpoint, evidence_boundary e
must_not_imply. Valide-o contra o ledger:

    python scripts/validate_framing.py <job_dir>/planning/framing-memo.json --ledger <job_dir>/extraction/claim-ledger.json --output <job_dir>/planning/framing-validation.json

### 7. Transferir a decisão para o brief

Crie planning/framing-handoff.md contendo motivo de atualidade, top line,
tensão, contexto selecionado, contraponto, riscos de distorção, guardrails e
claims permitidos/bloqueados. Passe-o a reviews-editorial-brief, que decide a
arquitetura final e valida seu schema.

## Contrato de saída, artefatos e ferramentas

| Artefato | Conteúdo obrigatório | Gate |
| --- | --- | --- |
| planning/context-source-log.json | fonte, papel, data, função, limite e decisão | nenhum contexto sem fonte/localizador |
| planning/journalistic-framing.md | pergunta, atualidade, top line, tensão, contraponto, guardrails | cada item factual tem claim/issue |
| planning/framing-memo.json | contrato estruturado de tensão, headline e limite | valida contra framing-memo.schema.json |
| planning/framing-validation.json | evidência de validação do memo | valid=true com ledger conferido |
| planning/framing-handoff.md | instruções limitadas para o brief | nenhuma promessa excede o bottom line |

O modelo completo e a taxonomia estão em references/framing-contract.md e
references/framing-taxonomy.md. Não há gerador próprio de framing neste
repositório: esses são artefatos editoriais preenchidos após leitura; use os
scripts existentes de proveniência e schema para verificar os materiais que os
sustentam.

## Stop conditions e caminho degradado

Pare e volte à proveniência/appraisal se não houver claim liberado para o
motivo de atualidade, se contexto essencial não tiver fonte, se a crítica
externa não estiver classificada, se a versão da diretriz for incerta ou se a
tensão depender de causalidade, benefício clínico ou mudança de prática não
sustentados.

Em modo degradado, reduza o framing a escopo e limitação: diga o que a fonte
relata e o que não permite concluir. Não use dados de mídia, nome de periódico
ou publicação recente como substitutos de evidência. Se não há acontecimento
novo, registre isso e escolha uma abertura explicativa.

## Proibições

É proibido:

- fabricar novidade, urgência, polarização ou uma pergunta retórica sem
  resposta;
- dar peso equivalente a fontes de autoridade desigual;
- esconder dano, condição, exceção ou incerteza material para proteger o arco;
- usar correção humana como fato científico ou regra automática;
- tratar conflito de interesse como prova de invalidez;
- alterar fatos, números, direção, modalidade ou força da recomendação.

## Interação com outras skills

Esta skill recebe facts de reviews-source-provenance e limites de
reviews-scientific-appraisal. Ela alimenta reviews-editorial-brief e depois
reviews-edition-writing. reviews-audit verifica se a candidata mantém os
guardrails; reviews-feedback-learning pode registrar uma preferência humana,
mas não modifica o framing automaticamente.

## Evals, exemplos e casos adversariais

references/examples-and-evals.md contém três exemplos concretos e três casos
adversariais. evals/cases.json contém positivo, negativo, limite e regressão.
Execute a checagem de provenance/appraisal das fontes usadas e compare os
artefatos do framing aos critérios objetivos. Aprovação exige que os quatro
casos mantenham top line proporcional, contexto rastreável e nenhuma novidade,
controversa ou conclusão fabricada.

## Checklist operacional executável

- Confirme que atualidade, contexto e top line têm claims ou issues localizáveis.
- Registre cada fonte contextual com papel, data, limite e decisão de inclusão.
- Compare desacordos por escopo, método, população e autoridade.
- Crie guardrails de título, lead e fecho antes de enviar o handoff.
- Verifique que observações humanas preservam sua fronteira e não viram fatos.
- Bloqueie o framing se depender de novidade, conflito ou causalidade não sustentados.
