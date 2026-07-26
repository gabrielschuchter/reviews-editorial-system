---
name: reviews-document-presentation
description: Preparar, exportar e inspecionar a apresentação de uma candidata Reviews sem degradar claims, tabelas, referências ou acessibilidade. Use após auditoria textual e quando DOCX, PDF, página web ou material visual precisar de verificação rastreável.
---

# Apresentação documental Reviews

## Propósito

Prepare uma edição auditada para leitura e distribuição preservando hierarquia,
legibilidade, links, tabelas, notas e rastreabilidade. Esta skill pode exportar
e inspecionar; ela não encurta condição clínica, não altera recomendação e não
declara validação visual sem renderização ou revisão humana documentada.

Leia os [gates de apresentação](references/presentation-gates.md), os
[exemplos e evals](references/examples-and-evals.md) e a
[evidência humana de tabelas](references/corpus-evidence.md) antes de decidir
layout, quebra ou compactação.

## Gatilhos

Acione esta skill quando:

- candidata auditada precisa virar DOCX, PDF, página ou pacote de entrega;
- tabela, notas, referências, links ou cabeçalhos podem perder contexto no reflow;
- houver pedido de inspeção de renderização, acessibilidade ou viewport estreito;
- mudança de fonte, exportador, largura, imagem ou estrutura exigir nova inspeção;
- uma apresentação anterior tiver cortado conteúdo ou separado nota crítica.

## Quando não usar

Não use antes de auditoria textual. Não use para resolver claim incorreto,
certeza ausente, recomendação ambígua ou título exagerado; devolva para a etapa
editorial adequada. Não use para esconder excesso de conteúdo com fonte menor,
overflow, abreviação não explicada ou remoção de condição. Não publique ou faça
upload por conta própria.

## Entradas

Exija:

- final/candidate.md ou candidata auditada com versão identificada;
- auditorias factual, metodológica, estrutural e final aplicáveis;
- tabela estruturada e fonte/localizadores de cada recomendação;
- final/visual-plan.md com origem, permissão e risco de interpretação;
- especificação de destino: DOCX, PDF, web, impressão ou Google Docs;
- requisitos de acessibilidade, viewport e identidade visual aprovados;
- lista de mudanças desde a última inspeção.

Se o conteúdo não tiver aprovação de auditoria, produza somente lista de riscos;
não exporte versão que pareça pronta para publicação.

## Gates

Antes de liberar apresentação, confirme:

1. candidata, tabelas e referências pertencem à mesma versão auditada;
2. nenhuma tabela perde população, condição, ação, força, certeza ou exceção;
3. título, subtítulo, notas e referências permanecem ligados ao bloco correto;
4. links e âncoras são verificáveis no formato de destino;
5. contraste, tamanho mínimo e ordem de leitura são adequados;
6. renderização existe ou revisão visual humana está explicitamente pendente.

Uma checagem de sintaxe de DOCX não prova renderização, contraste ou legibilidade.

## Hierarquia de fontes

O conteúdo auditado e o ledger continuam governando o que pode aparecer. A fonte
original governa texto de recomendação e referência. O visual plan governa origem
e permissão de imagem. A evidência humana derivada pode orientar tabela e fecho,
mas não autoriza redesenhar conteúdo científico. Requisito de acessibilidade e
formato de entrega prevalece sobre preferência estética.

## Procedimento

1. Confirme a versão auditada da candidata, tabelas, notas e visual plan.
2. Leia a especificação do destino e identifique páginas, viewport e recursos
   que precisam de inspeção humana.
3. Valide linhas de recomendação com python scripts/validate_tables.py
   <tabela> antes de reduzir largura, colunas ou tipografia.
4. Crie final/presentation-plan.json com formato, páginas, tabelas, links,
   requisitos de acessibilidade, riscos e responsável pela inspeção.
5. Execute python scripts/export_docx.py <candidate.md> <candidate.docx>
   somente quando a candidata estiver apta e as dependências estiverem disponíveis.
6. Verifique a auditoria estrutural do exportador, mas trate-a como evidência
   parcial e não como inspeção visual.
7. Renderize o formato final quando o ambiente permitir e inspecione página,
   tabela, nota, referência, link, quebra, contraste e leitura estreita.
8. Registre cada defeito com página ou viewport, elemento, captura, impacto,
   severidade e destino de correção em final/presentation-audit.json.
9. Bloqueie entrega se condição clínica, exceção, link, número ou referência
   relevante estiver cortado, oculto, ilegível ou separado do seu contexto.
10. Gere handoff para auditoria ou revisão humana após reflow material,
    mantendo a exportação anterior e o report de inspeção.

## Decisões

Prefira estrutura que preserve significado a compactação visual. Divida tabela
longa, repita cabeçalho e use nota explícita quando necessário. Não use largura
fixa que empurre qualificadores para fora da página. Para web estreita, recomponha
ou ofereça alternativa acessível; não declare responsividade só porque o texto
encolheu.

Use imagem de fonte somente com origem, permissão e legenda apropriadas. Uma
recriação de gráfico exige dados completos, dupla conferência, rótulo de
recriação e fonte. Ilustração editorial não pode parecer resultado científico.

## Contrato de saída

Entregue:

- final/presentation-plan.json com destino, requisitos e riscos;
- final/candidate.docx ou artefato equivalente, quando a exportação for possível;
- final/presentation-audit.json com checks, defeitos, status e evidência visual;
- final/presentation-audit.md com leitura humana das limitações;
- capturas ou referências de renderização quando foram realmente obtidas;
- handoff de reflow, correção editorial ou revisão humana pendente.

O status só pode ser passed quando não houver blocker/major e a evidência
declarada sustentar o tipo de inspeção realizado.

## Artefatos

Mantenha em final:

- candidate.md e candidate.docx;
- visual-plan.md e presentation-plan.json;
- presentation-audit.json, presentation-audit.md e capturas de renderização;
- links-and-anchors-check.json, quando aplicável;
- review-status.json com aprovação humana pendente.

Mantenha em audits a versão textual que autorizou a candidata. Não substitua o
DOCX sem registrar versão da fonte Markdown e data de exportação.

## Ferramentas

Use scripts/export_docx.py para exportação estruturada e sua auditoria interna,
scripts/validate_tables.py para linhas de recomendação e scripts/validate_job.py
para gates do job. Use renderizador disponível do ambiente para inspeção visual.
Se PDF, OCR ou renderizador estiver ausente, registre o erro e peça revisão
humana; não gere uma captura fictícia.

## Stop conditions

Pare a liberação quando:

- a candidata não tiver auditoria textual compatível;
- tabela cortar condição, certeza, exceção ou referência;
- texto, número, marcador, link ou nota estiver truncado;
- visual representar dado sem fonte, permissão ou rótulo;
- contraste, ordem de leitura ou tamanho tornar conteúdo crítico inacessível;
- renderização necessária não estiver disponível e o risco não puder ser avaliado.

## Falhas

Sem exportador DOCX, entregue plano e checklist estrutural, marque renderização
como pendente e não alegue apresentação concluída. Sem acesso a viewport web,
valide estrutura e links localmente e deixe inspeção mobile para humano. Se uma
tabela não couber, devolva a decisão de estrutura; não omita colunas ou exceções.

## Proibições

Não use fonte menor para caber condição crítica. Não transforme uma nota em
rodapé invisível. Não recorte gráfico seletivamente. Não modifique fatos durante
layout. Não confunda exportação, abertura do arquivo ou XML válido com inspeção
visual. Não declarar aprovação de publicação a partir de render report.

## Interação

Receba conteúdo de reviews-edition-writing somente após reviews-audit. Devolva
claim, título ou tabela que perdeu significado para redação/auditoria. Consulte
reviews-humanizer-ptbr apenas se a correção for textual e tiver finding
confirmado; apresentação não humaniza. Envie defeitos observados e versões
humanas para reviews-feedback-learning após decisão editorial.

## Exemplos

Consulte os três cenários de exportação e inspeção em
[exemplos e evals](references/examples-and-evals.md#exemplos).

## Casos adversariais

Consulte os bloqueios de tabela, renderização e gráfico em
[exemplos e evals](references/examples-and-evals.md#casos-adversariais).

## Evals

Use evals/cases.json para verificar exportação apta, bloqueio por condição
oculta, limite sem renderizador e regressão de tabela seletiva. Não marque eval
como aprovado sem o artefato e evidência definidos.
