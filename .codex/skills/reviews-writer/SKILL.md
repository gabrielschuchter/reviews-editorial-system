---
name: reviews-writer
description: Orquestrar uma edição Reviews auditável do intake ao aprendizado, escolhendo capacidades especializadas, preservando gates e artefatos por job. Use ao iniciar, retomar, coordenar ou verificar um fluxo editorial completo ou parcial.
---

# Reviews Writer

## Propósito

Use esta skill como porta de entrada do sistema editorial. Ela cria uma cadeia
inspecionável de trabalho para um job, escolhe a capability responsável por cada
etapa e impede que uma etapa posterior esconda uma falha anterior. Ela não
redige uma edição, não aprova publicação e não substitui revisão humana.

Leia o [mapa de capacidades](references/capability-map.md) antes de rotear o
trabalho. Para cenários e critérios de aceitação, leia
[exemplos e evals](references/examples-and-evals.md). Para selecionar uso seguro
do corpus humano, leia a [evidência humana derivada](references/corpus-evidence.md).

## Gatilhos

Acione esta skill quando o pedido pedir para:

- iniciar uma edição Reviews a partir de fontes, pauta ou pacote do Drive;
- retomar um job interrompido, mudado de versão ou com gates pendentes;
- selecionar skills e ordem de execução para um pedido editorial;
- transformar pedido amplo em artefatos, responsáveis, limites e estados;
- verificar se uma candidata pode seguir para auditoria, apresentação ou revisão.

## Quando não usar

Não use como atalho para escrever uma peça isolada sem fontes e sem job. Não use
para decidir risco de viés, escolher título, corrigir estilo, humanizar prosa ou
aprovar edição: encaminhe cada questão à skill especializada. Não use para
publicar, fazer upload ou modificar o arquivo histórico do Drive.

## Entradas

Exija, antes de criar ou retomar o fluxo:

- job_dir com job.yml, ou fontes locais identificáveis para criar um job;
- pedido editorial, leitor, decisão a apoiar e tipo de entrega desejada;
- fontes com origem, versão, acesso e responsável humano conhecidos;
- estágio solicitado: full, evidence, planning, writing, audit, presentation ou learning;
- caminhos dos artefatos existentes, quando houver retomada;
- restrições de confidencialidade, prazo, formato e destino.

Se ainda não houver job, crie-o com python scripts/create_job.py --source
<arquivo> --topic <tema>. Registre o diretório retornado; não use job.json,
pois o contrato operacional é job.yml.

## Gates

Só avance quando o artefato do estágio anterior for compatível com as mesmas
fontes, versão e escopo. Exija, no mínimo:

1. fontes identificadas antes de provenance;
2. claim ledger verificável antes de appraisal, framing ou redação;
3. appraisal e limites de inferência antes de qualquer tese editorial;
4. brief e framing aprovados antes do rascunho;
5. auditoria independente após mudanças materiais;
6. aprovação humana explícita antes de publicação.

Trate critical_errors, hash divergente, fonte ilegível, direção de efeito incerta
e claim sem localizador como bloqueios, não como pendências cosméticas.

## Hierarquia de fontes

Priorize fonte primária, suplemento, protocolo, registro e errata para fatos do
estudo. Use autoridade metodológica para julgar método, correção humana para
entender uma mudança local e exemplares aprovados apenas para estrutura e voz.
Material de contexto não sustenta claim central. Um texto publicado, press release
ou exemplo de estilo não substitui dado original ausente.

Conserve o nível do corpus e as limitações associadas a cada exemplar. O holdout
nunca entra na recuperação para redigir ou formular regra.

## Procedimento

1. Confirme o escopo, o estágio pedido, o job.yml e a identidade das fontes.
2. Registre lacunas de acesso, versão, idioma, direitos e responsável humano
   no contexto do job antes de escolher uma capability.
3. Crie planning/orchestration-context.json com stage, job_dir, caminhos de
   brief/source roles e routing_context quando aplicável.
4. Execute python scripts/orchestrate_reviews.py <contexto> --output
   <job>/planning/capability-plan.json.
5. Verifique preflight_passed, blocked_reasons e a ordem de
   selected_capabilities; não substitua a seleção por memória informal.
6. Roteie cada capability para a skill indicada e entregue somente os
   artefatos que ela pode consumir.
7. Valide o job com python scripts/validate_job.py <job> após cada estágio
   que produzir artefatos de pipeline.
8. Bloqueie o avanço quando houver lacuna factual, versão divergente ou
   finding crítico; devolva ao estágio que pode resolver a causa.
9. Audite novamente claims afetados após redação, humanização, reflow de
   tabela ou alteração de título e lead.
10. Gere no encerramento um handoff com estado, artefatos válidos,
    bloqueios, próxima capability e aprovação humana ainda necessária.

Use a ordem do plano; paralelo só é seguro para leituras independentes de fontes
ou auditorias que não editam a mesma candidata. Consolidação de evidência,
framing, prosa e decisão de publicação permanecem sequenciais.

## Decisões

Escolha full quando a solicitação inicia ou reabre uma edição. Escolha estágio
menor apenas quando artefatos anteriores forem válidos e vinculados ao mesmo hash
de fontes. Para título ou contraponto, inclua reviews-journalistic-framing; para
sinais artificiais, inclua primeiro reviews-anti-ai-writing e só depois
reviews-humanizer-ptbr para findings confirmados. Nunca transforme hipótese de
processo em regra geral sem reviews-feedback-learning, caso de regressão e
aprovação humana.

## Contrato de saída

Entregue planning/capability-plan.json com:

- estágio selecionado e rationale;
- lista ordenada de capabilities, entradas, saídas e stop conditions;
- preflight_passed, checks executados e blocked_reasons;
- próximo passo seguro, sem alegar que etapa humana foi concluída;
- referência ao job, às versões e aos artefatos consumidos.

Entregue também resumo de estado: ready, blocked ou awaiting-human-review,
acompanhado da evidência que justifica esse estado.

## Artefatos

Use caminhos dentro de <job>:

- planning/orchestration-context.json e planning/capability-plan.json;
- normalized, extraction e analysis para evidência;
- planning/editorial-brief.json, planning/framing-memo.json e outline;
- drafts para versões de texto;
- audits para relatórios independentes e diffs;
- final para candidata, DOCX, apresentação e status;
- feedback para comparação e propostas de aprendizado.

Não grave artefatos de um job em outro job e não reutilize claim ledger sem
confirmar fonte, versão e hash.

## Ferramentas

Use scripts/orchestrate_reviews.py para preflight e seleção de capabilities.
Use scripts/validate_job.py para gates de pipeline,
scripts/validate_artifact.py para contratos modulares,
scripts/run_checks.py para invariantes do repositório,
scripts/run_evals.py para regressões determinísticas e
scripts/validate_skills.py para bundles de skills. Os scripts são evidência
complementar; nenhum decide qualidade clínica ou aprovação humana.

## Stop conditions

Pare e devolva uma pergunta objetiva ao editor quando houver:

- fonte essencial ausente, ilegível, trocada ou sem versão confirmada;
- conflito entre tabela, texto, suplemento, protocolo ou errata;
- direção de efeito, população, comparador ou desfecho principal incerto;
- título, lead ou recomendação mais forte que a evidência;
- tentativa de publicar, promover regra ou alterar fonte histórica automaticamente;
- risco de privacidade, consentimento, direito autoral ou conflito relevante sem decisão.

## Falhas

Quando o preflight falhar, preserve o último estado válido, registre a causa e
informe o menor insumo que destrava a etapa. Sem full text, prossiga somente com
claims permitidos pelo material disponível e marque cobertura incompleta. Se um
script não estiver disponível, não simule saída: registre comando, erro, artefato
ausente e gate humano necessário.

## Proibições

Não pule provenance para draft. Não combine fontes de jobs diferentes. Não
descarte finding crítico para manter prazo. Não use corpus humano como prova de
fato científico. Não reescreva auditoria como correção. Não trate saída limpa de
linter como evidência de naturalidade, segurança factual ou aprovação editorial.

## Interação

| Capability | Acione quando | Receba de volta |
| --- | --- | --- |
| reviews-source-provenance | fonte não está rastreável | roles, extração e ledger |
| reviews-scientific-appraisal | há ledger e pergunta respondível | limites e julgamentos |
| reviews-editorial-brief | evidência e decisão claras | brief e seleção |
| reviews-journalistic-framing | há tese, título ou contraponto | framing memo |
| reviews-edition-writing | brief/framing autorizam prosa | rascunho e claims sensíveis |
| reviews-anti-ai-writing | candidata precisa de diagnóstico | ocorrências classificadas |
| reviews-humanizer-ptbr | finding confirmado exige mudança | diff e reauditoria |
| reviews-audit | texto ou tabela mudou materialmente | findings independentes |
| reviews-document-presentation | conteúdo auditado precisa entregar | render report |
| reviews-feedback-learning | existe revisão humana comparável | proposta e regressão |

## Exemplos

Consulte os três cenários operacionais em
[exemplos e evals](references/examples-and-evals.md#exemplos).

## Casos adversariais

Consulte os três bloqueios e retornos seguros em
[exemplos e evals](references/examples-and-evals.md#casos-adversariais).

## Evals

Use o manifesto local em evals/cases.json. Cada execução deve demonstrar plano,
bloqueio ou handoff verificável; não considere a mera existência do arquivo como
resultado de uma execução.
