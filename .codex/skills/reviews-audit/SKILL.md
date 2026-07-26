---
name: reviews-audit
description: Auditar independentemente uma candidata Reviews contra fontes, claim ledger, appraisal, framing e apresentação, classificando findings sem corrigi-los. Use antes de revisão humana, após mudança material ou para regressão de falha editorial conhecida.
---

# Auditoria independente Reviews

## Propósito

Faça uma leitura adversarial rastreável. Localize a afirmação, a fonte, o
localizador, o julgamento e a consequência antes de registrar um finding. Esta
skill entrega pedido de correção separado da correção; não reescreve a candidata
nem concede aprovação editorial.

Leia o [contrato de findings](references/finding-contract.md), os
[exemplos e evals](references/examples-and-evals.md) e a
[evidência humana aplicável](references/corpus-evidence.md) antes de auditar
estrutura, tabela, fecho ou apresentação.

## Gatilhos

Acione esta skill quando:

- uma candidata, título, lead, tabela ou recomendação estiver pronta para revisão;
- uma mudança factual, metodológica, estrutural ou de humanização for proposta;
- uma regra de regressão precisar confirmar que falha anterior não reapareceu;
- a fonte, suplemento, correção ou versão de documento tiver mudado;
- a apresentação puder ter ocultado condição, exceção, referência ou número.

## Quando não usar

Não use para escrever, humanizar, aprovar publicação ou buscar nova evidência
silenciosamente. Não use relatório de auditoria para substituir decisão clínica.
Não use um linter como veredito de verdade. Devolva fonte incompleta à
provenance, limite de inferência ao appraisal e escolha de ângulo ao framing.

## Entradas

Exija versão identificada de:

- candidata em Markdown e, se houver, título, lead, tabelas e DOCX;
- extraction/claim-ledger.json e source-roles.json;
- analysis/methodological-review.json e inference-boundaries.md;
- editorial brief, framing memo e lista de claims sensíveis;
- anti-ai report e humanization diff, quando revisão de estilo ocorreu;
- fonte primária, suplemento, protocolo, registro, errata e pesquisa externa pertinentes.

Registre hash ou versão de cada entrada no report. Sem esse vínculo, não alegue
cobertura completa.

## Gates

Comece somente quando o auditado e seus insumos forem da mesma versão. Antes de
liberar candidata, exija:

1. cobertura do título, lead, resumo, pull quotes, tabelas e conclusão;
2. conferência de claims factuais, numéricos, causais, normativos e de aplicabilidade;
3. reconciliação de cada finding com fonte e appraisal;
4. status explícito para cada blocker e major;
5. reauditoria de claims afetados por correção;
6. gate humano pendente, mesmo sem finding automático.

## Hierarquia de fontes

O artigo, diretriz, suplemento, protocolo, registro e errata governam fatos. O
claim ledger localiza esses fatos. O appraisal governa limites de inferência; o
brief e framing governam intenção editorial, não verdade. Correções humanas e
corpus derivado ajudam a julgar estrutura e edição mínima, mas não podem alterar
fato científico. Crítica externa deve ser identificada como crítica, não atribuída
aos autores.

## Procedimento

1. Confirme a versão da candidata, fontes, ledger, appraisal, brief e framing.
2. Registre escopo, dimensões cobertas, trechos não auditáveis e razão da
   cobertura incompleta em audits/<modo>-coverage.json.
3. Execute python scripts/audit_draft.py com draft, ledger e caminhos de
   saída separados para suporte factual e sinais heurísticos.
4. Verifique título, subtítulo, lead, tabelas, notas e fecho antes do corpo,
   pois esses elementos concentram promessas fora de contexto.
5. Compare cada claim público com claim_id, excerto, localizador, população,
   comparador, tempo, unidade, direção e permissão de uso.
6. Audite causalidade, risco de viés, imprecisão, multiplicidade, subgrupos,
   dados ausentes, desfechos substitutos, aplicabilidade e recomendações contra
   o appraisal, não contra preferência pessoal.
7. Valide cada tabela de conduta com python scripts/validate_tables.py
   <tabela> e confira força, certeza, condição e exceção no material fonte.
8. Classifique findings por categoria, severidade, confiança, status,
   evidência, consequência e responsável pela correção.
9. Gere audits/<modo>-audit.json e audits/<modo>-audit.md sem editar a
   candidata; encaminhe cada finding à skill ou etapa responsável.
10. Reaudite apenas os claims e dependências modificados depois da correção,
    mantendo o report anterior como evidência histórica.

## Decisões

Classifique como blocker promessa sem suporte, número errado, fonte trocada,
causalidade indevida, recomendação alterada ou omissão que inverte leitura.
Classifique como major perda material de população, certeza, aplicabilidade,
condição ou exceção. Classifique como minor clareza que não muda sentido. Use
note para risco documentado sem mudança exigida.

Não converta finding suspected em erro confirmado sem prova. Não converta
ausência de relato em falha de condução. Quando a fonte não permite concluir,
registre cobertura insuficiente e preserve a incerteza.

## Contrato de saída

Entregue audit-report validável com:

- audit_id, job_id, modo, versão e cobertura;
- finding_id, categoria, severidade, confiança e status;
- trecho/localização na candidata e evidência/localizador da fonte;
- claim_ids afetados, julgamento, consequência e correção solicitada;
- responsável e etapa de retorno, incluindo reauditoria necessária;
- blockers, majors pendentes, limitações de cobertura e decisão de liberação.

Entregue Markdown narrativo quando o finding exigir explicação metodológica; o
JSON estruturado é o gate. Um report vazio só é aceitável se cobertura indicar o
que foi realmente verificado.

## Artefatos

Mantenha no job:

- audits/factual-audit.json e factual-audit.md;
- audits/statistical-audit.json e methodological-audit.json;
- audits/anti-ai-audit.json e humanization-claim-reaudit.json, se aplicáveis;
- audits/structural-audit.json, coherence-audit.json e final-audit.json;
- audits/<modo>-coverage.json e recheck-<versão>.json;
- final/review-status.json com gate humano, nunca aprovação automática.

## Ferramentas

Use scripts/audit_draft.py para sinalizadores de suporte e escrita artificial,
scripts/audit_inference.py para padrões que exigem leitura humana,
scripts/validate_tables.py para linhas de recomendação e
scripts/validate_artifact.py audit-report para forma do relatório. Execute
scripts/verify_numbers.py quando registros numéricos tiverem sido atualizados.
Ferramenta detecta padrão; fonte e auditor documentam o julgamento.

## Stop conditions

Pare a liberação quando encontrar:

- blocker não resolvido ou sem aceite editorial explícito;
- claim sem fonte, localizador ou versão compatível;
- número divergente, direção incerta ou população/comparador trocado;
- recomendação sem força, certeza, condição ou exceção verificável;
- fonte materialmente atualizada após o draft;
- apresentação que esconde conteúdo clínico ou referência relevante;
- evidência insuficiente para confirmar ou rejeitar risco material.

## Falhas

Se fonte estiver indisponível, marque finding como unresolved e cobertura
incompleta, em vez de declarar passagem. Se o draft não tiver ledger, devolva à
provenance. Se appraisal estiver ausente, devolva a appraisal; não improvise
crítica genérica. Se o linter gerar falso positivo, registre por que o trecho
permanece e mantenha o finding como nota rastreável.

## Proibições

Não corrija texto no report. Não apague alerta para obter saída limpa. Não use
estilo do corpus como fonte clínica. Não trate título curto como automaticamente
proporcional. Não exija falsa simetria em controvérsia real. Não transforme a
ausência de evidência em evidência de ausência.

## Interação

Receba fontes de reviews-source-provenance, limites de
reviews-scientific-appraisal, intenção de reviews-editorial-brief e
reviews-journalistic-framing, prosa de reviews-edition-writing e diffs de
reviews-humanizer-ptbr. Devolva cada finding à capability causadora. Entregue
apenas candidata auditada a reviews-document-presentation. Envie decisões humanas
e regressões para reviews-feedback-learning.

## Exemplos

Consulte os três cenários de finding em
[exemplos e evals](references/examples-and-evals.md#exemplos).

## Casos adversariais

Consulte os bloqueios por fonte, tabela e falso positivo em
[exemplos e evals](references/examples-and-evals.md#casos-adversariais).

## Evals

Use evals/cases.json para verificar finding sustentado, bloqueio crítico, limite
de cobertura e regressão de encerramento vazio. O resultado esperado é report
rastreável, não texto corrigido.
