---
name: reviews-edition-writing
description: Redigir uma candidata Reviews em português brasileiro a partir de claims autorizados, appraisal, brief e framing rastreáveis. Use após a evidência estar validada e antes de auditoria, humanização ou apresentação.
---

# Redação de edição Reviews

## Propósito

Transforme um pacote editorial aprovado em uma candidata legível, proporcional à
evidência e pronta para auditoria independente. Esta skill organiza prosa,
estrutura, tabelas e claims sensíveis; ela não busca para preencher lacunas, não
altera recomendação da fonte e não aprova publicação.

Leia o [contrato de redação](references/writing-gates.md) antes de abrir a
primeira frase. Para usar padrões concretos e limites de decisão, leia
[exemplos e evals](references/examples-and-evals.md).

## Gatilhos

Acione esta skill quando houver:

- brief aprovado e framing proporcional à evidência;
- pedido para elaborar primeira candidata ou reescrever seção após correção factual;
- necessidade de escolher estrutura por tipo de edição;
- tabela de recomendações que precisa preservar população, condição e exceções;
- candidata que precisa mapear cada claim sensível antes de auditoria.

## Quando não usar

Não use se fonte, versão, ledger, appraisal, brief ou framing estiverem ausentes.
Não use para corrigir finding de auditoria sem retornar ao estágio de origem. Não
use para humanizar texto: encaminhe sinais confirmados a reviews-humanizer-ptbr.
Não use para revisar autoria, aprovar publicação, trocar números por fluidez ou
inventar contexto clínico.

## Entradas

Exija os seguintes artefatos do mesmo job e mesma versão de fontes:

- extraction/claim-ledger.json com claims verified e permitidos;
- analysis/methodological-review.json e analysis/inference-boundaries.md;
- planning/editorial-brief.json ou YAML equivalente validado;
- planning/framing-memo.json, quando título, tensão ou contraponto importarem;
- planning/editorial-outline.md e tipo de edição selecionado;
- tabelas, dados de origem e exceções que devem ser preservadas;
- lista de palavras, claims e interpretações proibidas.

Registre qualquer campo ausente em extraction/missing-information.json. Não
converta ausência em generalização.

## Gates

Antes da prosa, confirme que:

1. cada claim prioritário possui documento, excerto e localizador;
2. população, comparador, desfecho, tempo e direção são conhecidos quando mudam o sentido;
3. o appraisal distingue resultado, evidência, inferência e hipótese;
4. o brief identifica o que deve entrar e o que não pode ser afirmado;
5. o framing não promete mais do que a fonte permite;
6. toda recomendação tem força, certeza, condições e exceções ou lacuna explícita.

Bloqueie título, lead, tabela ou conclusão que não resistam a uma conferência no
ledger. Um número sem unidade ou denominador é pendência factual, não problema de estilo.

## Hierarquia de fontes

Use o ledger e a fonte primária como autoridade factual. Use o appraisal para
limitar inferência. Use o brief para seleção, o framing para hierarquia e
exemplares B apenas para forma, nunca para preencher conteúdo. Correção humana
orienta a voz local, mas não autoriza alterar efeito, recomendação ou certeza.

Quando fontes divergem, mantenha a divergência visível e devolva para
reviews-source-provenance ou reviews-scientific-appraisal.

## Procedimento

1. Leia brief, framing, ledger e appraisal na mesma sessão antes de escrever.
2. Liste claims autorizados, números protegidos, limites obrigatórios e
   assertions que precisam de auditoria independente.
3. Selecione a arquitetura prevista para o tipo de edição e atribua função
   explícita a cada parágrafo: orientar, explicar, apresentar, interpretar ou limitar.
4. Crie drafts/v1-content.md com título provisório, lead, nut graf, corpo,
   tabela quando aplicável e referências localizáveis.
5. Escreva abertura pela decisão, problema ou limite que move o leitor, não
   por relevância abstrata ou sinopse burocrática.
6. Apresente método somente no nível necessário para interpretar a conclusão,
   preservando desenho, população, comparador, desfecho e horizonte relevantes.
7. Registre cada número sensível em drafts/claim-coverage.json com claim_id,
   trecho, unidade, denominador, tempo e status de cobertura.
8. Valide tabela com python scripts/validate_tables.py <tabela> e devolva
   ambiguidade de origem em vez de completar célula por inferência.
9. Compare título, lead e fecho com o ledger e os limites de inferência;
   coloque ressalva perto da afirmação que ela limita.
10. Gere drafts/sensitive-claims.json e encaminhe a candidata para
    reviews-anti-ai-writing e reviews-audit, sem fazer a própria aprovação.

## Decisões

Para estudo primário, estruture contexto, pergunta, método, achado,
interpretação e limites. Para diretriz, separe recomendação, população,
força/certidão, implementação e exceções. Para revisão, separe elegibilidade,
resultados, heterogeneidade, aplicabilidade e lacunas. Para debate, apresente
consenso, dissenso delimitado, evidência de cada lado e o que resolveria a
divergência.

Prefira efeito absoluto quando estiver disponível e relevante; se só houver
relativo, declare-o sem sugerir magnitude absoluta. Não use p maior que 0,05
como prova de ausência de efeito. Não chame desfecho substituto de benefício
clínico e não transforme associação em causa.

## Contrato de saída

Entregue:

- drafts/v1-content.md com prosa marcada por seção e referências localizáveis;
- drafts/claim-coverage.json com claims usados, omitidos e sensíveis;
- drafts/sensitive-claims.json para auditoria adversarial;
- tabela estruturada, quando houver recomendação, com fonte e condições;
- registro de lacunas que impedem uma frase ou seção segura;
- handoff que informa versão de entrada, mudanças e próxima skill.

A candidata deve ser claramente identificada como candidata e nunca como edição
aprovada.

## Artefatos

Mantenha dentro de <job>:

- planning/editorial-brief.json, framing-memo.json e editorial-outline.md;
- extraction/claim-ledger.json e number-verification.json;
- analysis/methodological-review.json e inference-boundaries.md;
- drafts/v1-content.md, claim-coverage.json e sensitive-claims.json;
- audits/ para achados devolvidos por outras skills.

Conserve versões anteriores; não sobrescreva rascunho auditado com versão sem
registro de mudanças.

## Ferramentas

Use scripts/validate_artifact.py para o brief e scripts/validate_tables.py para
linhas de recomendação. Use scripts/audit_inference.py apenas como sinalizador
antes da auditoria humana. Use scripts/verify_numbers.py quando registros
numéricos forem atualizados. Nenhum desses comandos cria argumento editorial ou
substitui a conferência com a fonte.

## Stop conditions

Pare antes de prosa ou devolva para a etapa correta quando:

- claim não tem localizador, excerto ou permissão pública;
- número diverge, perde unidade, denominador, grupo ou tempo;
- recomendação não conserva força, certeza, condição ou exceção;
- título ou lead excede o appraisal;
- conclusão exige causalidade, aplicabilidade ou benefício não demonstrado;
- uma tabela depende de cabeçalho para esconder uma condição crítica.

## Falhas

Sem full text, escreva apenas o que o material permite e declare a limitação
concreta. Sem dado necessário para uma linha de tabela, marque a ausência e
retorne para provenance. Se a prosa revelar problema metodológico, não o suavize:
regresse a appraisal. Se a fonte mudar, invalide claims dependentes antes de
continuar.

## Proibições

Não invente exemplos, mecanismo, cenário de paciente, número ou transição. Não
troque termos técnicos por sinonímia rotativa. Não esconda limite no fecho depois
de promessa forte no lead. Não faça auditoria da própria candidata. Não aplique
mudança anti-IA automaticamente e não transforme texto científico em promoção.

## Interação

Receba ledger de reviews-source-provenance, julgamento de
reviews-scientific-appraisal, seleção de reviews-editorial-brief e framing de
reviews-journalistic-framing. Entregue candidata a reviews-anti-ai-writing,
reviews-audit e, somente depois de findings confirmados, reviews-humanizer-ptbr.
Após auditoria textual aprovada, entregue conteúdo a reviews-document-presentation.
Devolva correções humanas a reviews-feedback-learning, sem promover regra.

## Exemplos

Consulte os três padrões de redação em
[exemplos e evals](references/examples-and-evals.md#exemplos).

## Casos adversariais

Consulte os retornos seguros em
[exemplos e evals](references/examples-and-evals.md#casos-adversariais).

## Evals

Use evals/cases.json para checar candidata apoiada, bloqueio factual, caso
limítrofe de tabela e regressão de sobreinterpretação. O eval exige artefato e
critério observável, não impressão de fluidez.
