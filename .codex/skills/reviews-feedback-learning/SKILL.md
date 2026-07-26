---
name: reviews-feedback-learning
description: Converter comparações entre candidata e revisão humana do Reviews em feedback rastreável, propostas limitadas e regressões verificáveis sem promover regras automaticamente. Use após revisão editorial, auditoria resolvida ou análise de correções humanas reais.
---

# Aprendizado editorial Reviews

## Propósito

Aprenda com decisão humana sem apagar sua origem, universalizar gosto isolado ou
alterar o corpus. Esta skill compara versões, explica o motivo de cada mudança,
classifica escopo e transforma apenas padrões aprovados em proposta testável. Ela
não modifica skills, checklists, fontes nem regras globais automaticamente.

Leia a [política de promoção](references/promotion-policy.md), os
[exemplos e evals](references/examples-and-evals.md) e a
[evidência humana derivada](references/corpus-evidence.md) antes de chamar uma
correção de padrão.

## Gatilhos

Acione esta skill quando:

- uma candidata recebe revisão ou comentário humano;
- auditoria devolve correção que pode representar falha recorrente;
- há versões antes/depois e se quer separar fato, estrutura, tom e preferência;
- uma correção local parece candidata a regra para outra edição;
- uma regressão conhecida precisa provar que não reapareceu.

## Quando não usar

Não use sem versão candidata e versão revisada identificáveis. Não use para
reescrever candidata, aplicar regra, alterar corpus canônico ou votar em estilo.
Não use correção humana para substituir fonte primária, appraisal ou auditoria.
Não use exemplo isolado como prova de comportamento geral.

## Entradas

Exija:

- candidata e revisão humana com hash, caminho e papel de versão;
- comentários humanos, audit report ou razão editorial registrável;
- job_id, edition_id, seção, editor e data da decisão;
- fontes/claims afetados por toda alteração factual ou metodológica;
- classificação inicial de mudança: fato, número, método, recomendação, framing,
  estrutura, estilo, português nativo, apresentação ou preferência local;
- localização de regressão existente ou proposta de caso novo.

Quando faltar razão ou fonte, registre hipótese local; não aumente confiança para
compensar ausência de evidência.

## Gates

Antes de propor regra, confirme:

1. diff reproduzível entre candidata e versão revisada;
2. cada versão tem hash e papel inequívocos;
3. mudança factual remete a fonte e ledger, não só ao editor;
4. mudança editorial informa decisão que melhora ou evita;
5. escopo, exceção e risco de falso positivo estão definidos;
6. regressão falha no comportamento anterior e passa com a regra candidata;
7. aprovação humana explícita existe para qualquer promoção geral.

Regra aprovada sem teste, exceção ou responsável continua apenas proposta.

## Hierarquia de fontes

A fonte primária governa verdade factual. A correção humana é soberana para a
edição específica e evidência graduada para hipótese editorial. Corpus derivado
mostra recorrência e limites, mas permanece referência B. A auditoria evidencia
risco e a regressão evidencia comportamento do sistema; nenhuma delas substitui
aprovação do editor para regra geral.

## Procedimento

1. Confirme hashes, paths, job_id, edition_id e papel candidato/revisado das
   duas versões antes de comparar texto.
2. Execute python scripts/compare_versions.py <candidate> <reviewed>
   --output <job>/feedback/version-comparison.json.
3. Leia diff, comentários e audit report para identificar a decisão por trás
   da mudança, não só a substituição de caracteres.
4. Classifique cada alteração em factual, estatística, metodológica,
   estrutural, estilo, anti-IA, linguagem, apresentação ou preferência local.
5. Compare mudança factual com ledger e fonte; devolva divergência para
   provenance, appraisal ou audit em vez de tratá-la como preferência.
6. Registre feedback/<id>.json com original, editado, razão, escopo,
   exceção, confiança, fontes, aprovação e destino proposto.
7. Crie proposta de aprendizado só quando houver gatilho, ação, exceção,
   risco, artefato alvo e caso de regressão observável.
8. Execute python scripts/incorporate_feedback.py <feedback>
   --output <job>/feedback/learning-proposals.json para validar a proposta sem
   mudar regra alguma.
9. Rejeite promoção automática, generalização baseada em uma ocorrência ou
   mudança que descaracterize voz humana aprovada.
10. Gere handoff ao editor com propostas, evidência, regressões, decisões
    pendentes e itens que devem permanecer locais.

## Decisões

Use confiança alta somente para padrão repetido, com razão, fonte ou auditoria e
regressão. Use média para decisão humana bem justificada em escopo delimitado.
Use baixa para impressão isolada ou preferência. Um texto que soa melhor sem
critério repetível fica como escolha local.

Quando correção elimina frase vazia, preserve fatos, números, unidades,
referências, modalidade, exceções e força de recomendação. Quando correção muda
qualquer um desses elementos, trate como fato/metodologia e reaudite claims
afetados antes de qualquer aprendizado de estilo.

## Contrato de saída

Entregue:

- feedback/version-comparison.json com diff e versões verificáveis;
- feedback/feedback-records.json com classificação e evidência por alteração;
- feedback/learning-proposals.json com regra candidata, escopo e status;
- referência de regressão com caso, comportamento anterior e aceitação;
- decisão humana: local-only, candidate, approved ou rejected;
- handoff que declare explicitamente automatic_rule_mutation_performed como falso.

Uma regra aprovada continua separada do corpus original e deve manter versão
anterior recuperável.

## Artefatos

Use somente caminhos do job:

- feedback/version-comparison.json;
- feedback/feedback-records.json e learning-proposals.json;
- feedback/regressions/<id>.json ou referência no conjunto de evals;
- audits/humanization-diff.json e claim-reaudit.json, se aplicáveis;
- final/review-status.json para decisão editorial.

Não edite corpus/canonical, corpus/holdout ou publicação humana durante este fluxo.

## Ferramentas

Use scripts/compare_versions.py para diff reproduzível e
scripts/incorporate_feedback.py para validar proposta sem mutar regras. Use
scripts/validate_schema.py quando o record usar schema feedback ou
learning-pattern. Use scripts/run_evals.py depois de incluir regressão
determinística. Use scripts/validate_skills.py antes de declarar que uma mudança
de skill está pronta; a aprovação humana permanece independente.

## Stop conditions

Pare a promoção quando:

- candidata ou revisão não tiver hash, caminho ou papel verificável;
- razão da alteração for desconhecida e não houver decisão humana recuperável;
- mudança factual não tiver fonte e reauditoria;
- regra não tiver gatilho, exceção, risco e regressão;
- a regra conflitar com fonte primária, limite metodológico ou voz humana aprovada;
- o feedback pedir alteração automática de corpus, skill ou publicação.

## Falhas

Se o diff for grande demais para classificação segura, divida por seção e
priorize mudanças blocker/major. Sem comentário humano, registre incerteza e
mantenha proposta como local. Se a regressão revelar falso positivo repetido,
reduza escopo ou rejeite a regra. Se o arquivo revisado estiver ilegível, preserve
metadados e peça nova exportação, sem inferir intenção editorial.

## Proibições

Não promova toda correção a regra. Não use estatística de frequência como prova de
qualidade. Não reescreva versão humana para parecer consistente. Não use holdout
para formular regra. Não aplique mudança proposta a outros jobs. Não esconda
conflito entre revisão humana e fonte científica.

## Interação

Receba versões de reviews-edition-writing, findings de reviews-audit e diffs
localizados de reviews-humanizer-ptbr. Devolva mudança factual para provenance,
appraisal ou audit. Envie proposta aprovada pelo editor à skill/arquivo alvo em
turno separado e sempre com regressão. Compartilhe padrões de apresentação com
reviews-document-presentation sem copiar decisões visuais como regra universal.

## Exemplos

Consulte os três fluxos de comparação em
[exemplos e evals](references/examples-and-evals.md#exemplos).

## Casos adversariais

Consulte os bloqueios de generalização em
[exemplos e evals](references/examples-and-evals.md#casos-adversariais).

## Evals

Use evals/cases.json para correção localizada positiva, promoção sem prova,
limite de preferência local e regressão de termo clínico com exceção. Avalie
sempre artefato, razão, escopo, fontes e ausência de mutação automática.
