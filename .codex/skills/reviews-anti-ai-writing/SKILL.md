---
name: reviews-anti-ai-writing
description: Auditar rascunhos do Reviews em português brasileiro para padrões de escrita artificial, metadiscurso, repetição e estrutura mecânica sem reescrever, atribuir autoria ou calcular “humanidade”. Use antes de uma revisão editorial material, ao revisar textos com tom de chatbot, e para gerar ocorrências confirmáveis que podem ser encaminhadas ao reviews-humanizer-ptbr.
---

# Auditoria anti-IA do Reviews

## Propósito e limite

Classificar ocorrências localizadas que podem reduzir precisão editorial ou soar artificiais. A saída é um `anti-ai-report`: cada achado contém trecho, categoria, evidência, gravidade, confiança, motivo, risco de falso positivo e recomendação localizada. Esta skill não reescreve texto, não decide autoria humana/IA e não produz score global.

Use-a para manuscrito em PT-BR, título, subtítulo, tabelas convertidas em texto, lead, seções e conclusão. Não a use para auditar fato, número, força de recomendação, risco de viés ou layout: encaminhe essas perguntas a `reviews-source-provenance`, `reviews-scientific-appraisal`, `reviews-audit` ou `reviews-document-presentation`.

## Gatilhos exatos

Acione quando o pedido incluir “tom de IA”, “humanizar”, “texto robótico”, “muito genérico”, “metadiscurso”, “repetição”, “subtítulos demais”, “parece chatbot”, “audite sem reescrever” ou quando uma edição entrar na passagem de estilo antes da publicação.

Não acione apenas porque há uma palavra como “além disso”, “por fim” ou “importante”. O sinal depende de repetição, função no contexto e risco editorial.

## Pré-condições e entradas

Antes de auditar, confirme:

1. o rascunho está normalizado em UTF-8 e tem um `artifact_id` rastreável;
2. a versão do texto é a que seguirá para revisão, não uma cópia obsoleta;
3. fontes, claim ledger e brief permanecem disponíveis para checagens que ultrapassem estilo;
4. nenhum achado será tratado como autorização de reescrita automática.

Entradas obrigatórias: texto do rascunho e identificador de artefato. Entradas recomendadas: tipo de edição, brief, claim ledger e contexto da fonte. A ausência de fontes não impede a detecção de estilo, mas impede resolver atribuição vaga ou falsa precisão como se fossem apenas problemas de voz.

## Hierarquia de fontes

1. Fonte primária e claim ledger definem fatos e condições; nunca são corrigidos pelo linter.
2. Versões humanas revisadas do Reviews definem preferência editorial local com confiança e escopo explícitos.
3. Publicações finais mostram estrutura e cadência aprovadas.
4. Manuscritos crus e auditorias fornecem regressões, não modelos a copiar.
5. `avoid-ai-writing`, `blader/humanizer` e Wikipedia servem como taxonomia descritiva; nenhum autoriza detector de autoria.

Leia [referências operacionais](references/operational-guide.md) antes de classificar caso ambíguo, usar corpus ou escolher uma recomendação de alta gravidade.

## Quando não usar

Não use esta auditoria para decidir autoria, para substituir leitura humana, nem quando o único objetivo for deixar uma frase "mais bonita". Encaminhe conflitos factuais, uma recomendação clínica, uma citação ou uma diferença entre versões ao fluxo de proveniência e auditoria.

- Confirme que a passagem contém sinal observável, não apenas uma impressão de estilo.
- Compare a ocorrência com a frase anterior e a seguinte antes de abrir uma decisão.
- Registre a categoria e o risco de falso positivo sem propor uma reescrita.
- Verifique se número, citação, modalidade ou condição tornam a decisão editorial dependente do claim ledger.
- Bloqueie a publicação se houver token interno, instrução de ferramenta ou fala de assistente exposta.
- Roteie a correção confirmada ao humanizer somente com revisor humano identificado.
- Audite novamente a passagem depois de uma edição confirmada, sem tratar a redução de alertas como prova de qualidade.
- Rejeite o achado quando a suposta fórmula for necessária para contrastar fonte, exceção ou condição clínica.

## Procedimento operacional

1. Preserve o arquivo de entrada e calcule/registre seu hash no relatório.
2. Execute:

   ```powershell
   python scripts/audit_anti_ai.py --input jobs/JOB-2026-001/draft.md --artifact-id JOB-2026-001:draft --output jobs/JOB-2026-001/audits/anti-ai-report.json
   ```

3. Leia cada ocorrência. Classifique-a como `confirmed`, `rejected` ou mantenha `candidate`; anote revisor humano, decisão e motivo fora do texto-fonte.
4. Confirme o problema subjacente. Exemplo: “estudos mostram” pode ser atribuição vaga, mas pode estar sustentado por citação na frase seguinte; não corrija sem procurar a fonte.
5. Encaminhe somente ocorrências `confirmed` ao `reviews-humanizer-ptbr`, junto de decisões humanas e claim ledger quando a frase contiver conteúdo protegido.
6. Arquive o relatório ao lado do draft. Após mudança material, rode novamente esta auditoria no texto revisado.

## Critérios de julgamento

- `critical`: token interno de ferramenta ou fala de chatbot exposta ao leitor; bloqueia publicação até resolução.
- `moderate`: autoqualificação, abertura vazia, promoção, atribuição vaga ou precisão absoluta que pode alterar a leitura; exige revisão humana.
- `minor`: transição repetida, paralelismo, enumeração mecânica, cadência uniforme ou conclusão recapitulatória; pode ser aceitável se cumprir função real.
- Confiança alta não elimina revisão humana. Risco de falso positivo alto exige recomendar inspeção, nunca remoção automática.

Não confunda: força “forte” com certeza alta, uma ressalva clínica necessária com hedge genérico, ou uma tabela seletiva com omissão automática.

## Contrato de saída e caminhos

Grave `anti-ai-report.schema.json` válido em `jobs/<job-id>/audits/anti-ai-report.json` ou caminho equivalente. O relatório deve incluir:

- `report_id`, hash do artefato, fontes de referência e proibições;
- uma ocorrência por trecho, com localização estável;
- `review_status: candidate` até decisão humana;
- `passed: false` somente quando houver bloqueio crítico; ausência de score global.

Use `schemas/anti-ai-report.schema.json` para validar o contrato. Os evals executáveis ficam em `evals/cases/anti-ai-*.json`; os casos declarativos desta skill ficam em `evals/cases.json`.

## Falhas, caminhos degradados e stop conditions

Pare e devolva ao responsável quando o draft não corresponde ao hash do relatório, o texto estiver ilegível, houver token interno crítico, a ocorrência exigir conferência factual ou o revisor não puder explicar por que confirmou o sinal.

Em caminho degradado (sem corpus ou sem fonte), gere apenas candidatos com risco de falso positivo explícito. Não converta inferência de estilo em correção. Se o linter não encontrar ocorrências, registre que isso não certifica voz humana nem qualidade editorial.

## Proibições

- Não usar “detector de IA”, porcentagem de humanidade ou atribuição de autoria.
- Não aplicar sinônimos, suavizar recomendações ou alterar fatos durante a auditoria.
- Não punir uma expressão isolada sem padrão/contexto.
- Não apagar condição, incerteza, referência, número ou ressalva para deixar a prosa mais curta.
- Não promover uma correção humana isolada a regra universal.

## Integração com outras skills

`reviews-writer` orquestra a etapa. `reviews-edition-writing` entrega o draft. Esta skill devolve diagnóstico; `reviews-humanizer-ptbr` trata apenas confirmações; `reviews-audit` revisa de forma independente o resultado; `reviews-feedback-learning` registra padrão candidato e regressão sem promoção automática.

## Exemplos rápidos

1. “Uma síntese crítica das principais recomendações...” → `self-importance-announcement`; sugerir subtítulo descritivo, sem tocar no conteúdo.
2. Três frases consecutivas iniciadas por “Além disso” → uma ocorrência `formulaic-transition` por frase, com falso positivo alto.
3. “Segundo turn0search0...” → `tool-token-leak` crítico; bloquear até substituir por fonte pública.

Veja três exemplos completos e três casos adversariais em [referências operacionais](references/operational-guide.md). Execute `python -m unittest discover -s tests -p "test_anti_ai_humanizer.py" -v` e `python scripts/audit_anti_ai.py --help` antes de declarar a skill utilizável.
