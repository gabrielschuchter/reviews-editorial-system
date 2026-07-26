---
name: reviews-source-provenance
description: Use quando for preciso receber, normalizar, conferir, classificar ou rastrear artigo, suplemento, protocolo, registro, diretriz, errata, crítica externa ou versão humana do Reviews. Cria a cadeia de proveniência e o claim ledger antes de qualquer interpretação, framing ou redação.
---

# Proveniência e extração rastreável do Reviews

## Propósito e fronteira

Esta skill transforma fontes fornecidas em um pacote factual verificável. Ela
não resume por impressão, não decide se uma evidência é convincente e não
redige uma edição. Seu produto é a cadeia que permite a outra pessoa localizar
cada fato, resultado, cálculo e limitação material.

Use-a para os gatilhos exatos abaixo:

- “de onde vem este dado?”, “mapear fontes”, “normalizar o artigo” ou
  “conferir suplemento/protocolo/registro”;
- uma nova pauta recebeu PDF, DOCX, HTML, DOI, registro, diretriz ou fontes
  externas;
- há números divergentes, versão possivelmente trocada, errata, retratação,
  crítica externa ou dúvida sobre qual fonte pode sustentar uma frase;
- o orquestrador iniciou um job e ainda não liberou a avaliação científica.

Não use esta skill para escolher ângulo, dizer se um resultado é clinicamente
relevante, reformular prosa, copiar estilo de exemplar ou aprovar publicação.
Para uma pergunta sem materiais identificáveis, peça as fontes ou registre
explicitamente a limitação; pesquisa genérica não substitui o pacote-fonte.

## Entradas obrigatórias e gates de entrada

Exija antes de iniciar:

1. diretório de job existente ou uma solicitação explícita para criá-lo;
2. pauta/pergunta editorial e lista de arquivos, URLs ou identificadores;
3. permissão somente de leitura para os originais e uma área de saída do job;
4. identidade mínima esperada da obra: título, autor/instituição, ano e tipo;
5. responsável pela conferência humana de legibilidade.

Leia, nesta ordem, AGENTS.md, editorial/constitution.md,
editorial/source-rules.md e docs/FACTUAL-SAFETY.md. Quando uma correção humana,
exemplar ou decisão de forma entrar no mapa de fontes, leia também
corpus/reviews-human-style-evidence.json e preserve a observação e a fronteira
que ela declara. Depois leia
references/contracts.md e references/source-hierarchy.md. Carregue
references/examples-and-evals.md ao resolver uma ambiguidade ou executar a
autochecagem da skill.

Use schemas/claim-provenance-report.schema.json e
scripts/validate_provenance.py para conferir a cadeia por claim contra os
papéis de fonte registrados.

Referências diretas obrigatórias: [contratos de proveniência](references/contracts.md),
[hierarquia de fontes](references/source-hierarchy.md) e
[exemplos e evals](references/examples-and-evals.md).

Não avance à extração se a fonte recebida não corresponde à pauta, se a versão
não pode ser identificada, ou se um documento essencial está corrompido,
ilegível ou trocado. O original nunca é renomeado, movido, anotado ou
sobrescrito.

## Hierarquia de fontes, decisões e critérios de julgamento

Há duas hierarquias independentes:

1. Para um resultado científico, priorize relatório completo, suplemento,
   protocolo, registro e plano de análise; use cada um para a função que de
   fato cumpre.
2. Para uma regra editorial, use a autoridade editorial do Reviews. Exemplar
   humano orienta forma, nunca comprova um fato científico.

Classifique cada fonte por papel, não por aparência. A regra operacional
completa, os papéis aceitos e os desempates estão em
references/source-hierarchy.md. Quando duas fontes divergem, preserve ambas,
registre localizadores e consequência; não selecione silenciosamente a versão
mais conveniente.

## Procedimento operacional

### 1. Abrir ou criar o job sem tocar nos originais

Se não houver job, crie-o com scripts/create_job.py e fontes explícitas. Se já
houver, confira job.json e source_documents antes de reutilizá-lo. Registre
para cada entrada: source_id, localização original, cópia de trabalho quando
existir, formato, identificador, data/versão, idioma, status de acesso e
relação com a pauta.

Crie ou complete:

- normalized/document-inventory.md;
- normalized/source-roles.json;
- normalized/missing-materials.md;
- extraction/source-map.md.

O contrato de campos e exemplos de preenchimento está em
references/contracts.md. Um nome de arquivo, URL solta ou snippet de busca não
é identificação suficiente.

### 2. Normalizar e confirmar a superfície de leitura

Execute os comandos reais abaixo, substituindo o runtime Python configurado no
projeto quando necessário:

    python scripts/normalize_documents.py <job_dir>
    python scripts/validate_job.py <job_dir> --confirm-documents "<revisor>"

Antes do segundo comando, revise efetivamente
normalized/document-validation.json, normalized/manual-document-review.json,
normalized/page-map.json, normalized/table-map.json,
normalized/figure-map.json e normalized/missing-materials.md. A confirmação
humana não é uma formalidade: ela verifica completude, legibilidade, versão e
se tabelas/figuras essenciais podem ser lidas.

PDF, DOCX e HTML continuam sendo superfícies de conferência. Extraia dos
artefatos normalizados e mantenha página, seção, tabela, figura ou outro
localizador verificável; não redija diretamente do arquivo bruto.

### 3. Atribuir papel e autoridade a cada fonte

Preencha normalized/source-roles.json com job_id e, para cada fonte,
source_id, source_role, authority_rank, location e rationale. Valide-o:

    python scripts/validate_schema.py <job_dir>/normalized/source-roles.json --schema source-roles

Separe evidência primária, autoridade metodológica, autoridade editorial,
correção humana, exemplar estrutural/estilístico, escrutínio externo, contexto
e fonte excluída. Um protocolo pode demonstrar pré-especificação, mas não
substitui o resultado publicado; uma notícia pode oferecer contexto, mas não
autoriza o claim central.

O corpus/reviews-human-style-evidence.json é evidência derivada de publicações
e correções humanas do Reviews. Quando ele orientar uma decisão de forma,
registre a observação aplicável e seu limite como human-correction ou exemplar;
ele nunca vira primary-evidence para um claim científico.

### 4. Submeter extração estruturada sem antecipar julgamento

Complete a extração estruturada a partir da leitura conferida e submeta-a ao
validador real:

    python scripts/extract_evidence.py <job_dir> --input <structured-extraction.json>

Para cada resultado potencialmente público, registre população, intervenção ou
exposição, comparador, desfecho, tempo, população de análise, denominador,
unidade, escala, estimativa, intervalo, direção, análise e localizador.
Distinga dado direto, resultado, cálculo derivado, interpretação, inferência,
hipótese, crítica externa e informação ausente.

Quando a informação não existir, use literalmente:

> Informação não localizada nos materiais consultados.

Quando a fonte for ambígua:

> Informação ambígua ou insuficientemente descrita no material disponível.

Essas frases descrevem a busca realizada; não autorizam preencher lacunas com
conhecimento externo.

### 5. Conferir números e material relacionado

Para cada número, confira valor, sinal, unidade, escala, grupo, denominador,
tempo, medida absoluta/relativa e se a comparação é entre grupos. Registre
todos os valores em extraction/number-records.json e execute:

    python scripts/verify_numbers.py <job_dir>

Compare texto, tabela, figura, suplemento, protocolo e registro quando cada um
declarar o mesmo elemento. Diferencie uma divergência de um número em contexto
distinto; ambos precisam de localizador. Não trate mudança intragrupo como
comparação entre grupos.

### 6. Construir autorização por claim

Registre as afirmações candidatas em extraction/proposed-claims.json e execute:

    python scripts/build_claim_ledger.py <job_dir>
    python scripts/validate_provenance.py <job_dir>/extraction/claim-ledger.json <job_dir>/normalized/source-roles.json --output <job_dir>/extraction/claim-provenance-report.json

O claim ledger é a autorização factual de cada frase pública. Só um claim
verified, com fonte, excerto, localizador e correspondência semântica
conferida, pode seguir para redação. Cálculo derivado precisa registrar entradas
e fórmula e deve ser apresentado como cálculo do sistema, nunca como número
relatado pelos autores.

Atualize extraction/source-map.md para relacionar cada claim_id liberado ao
documento, hash/versão, papel, localizador e status. Isso é um mapa de
auditabilidade, não uma bibliografia decorativa.

### 7. Tratar material ausente, externo e conflitante

Para suplemento, protocolo, registro, errata ou crítica externa ausente,
registre onde e quando foi procurado. Para escrutínio externo, guarde autoria,
data, alegação, resposta e classificação; ele não se converte em fato apenas
por ser repetido. Para errata, retratação ou expressão de preocupação, confirme
em fonte oficial e associe-a ao documento afetado.

Abra um registro de discrepância em analysis/critical-issues.md quando o
conflito puder alterar direção, magnitude, população, comparador, desfecho,
certeza ou possibilidade de publicação.

### 8. Aplicar o gate de liberação

Libere reviews-scientific-appraisal somente se:

- a identidade e versão de cada fonte relevante foram conferidas;
- documentos essenciais passaram pela revisão humana ou estão explicitamente
  bloqueados;
- papéis de fontes validam contra o schema;
- resultados e números prioritários têm localizador e status;
- o claim ledger foi construído e nenhum claim público é ambíguo, divergente,
  pendente, extrapolativo ou sem suporte;
- ausências, buscas externas e discrepâncias materiais estão registradas.

Registre no handoff quais claims e fontes estão liberados, quais estão
condicionais e quais são bloqueados.

## Contrato de saída, artefatos e ferramentas

Entregue, no mínimo, os seguintes artefatos do job:

| Artefato | Função | Gate objetivo |
| --- | --- | --- |
| normalized/document-inventory.md | identidade, versão e acesso das entradas | cada fonte tem status e relação com a pauta |
| normalized/source-roles.json | papel e autoridade | valida contra source-roles.schema.json |
| normalized/missing-materials.md | ausências e busca realizada | não contém ausência sem escopo de busca |
| extraction/*.json | dados/resultados rastreáveis | campos críticos ou ausência padronizada |
| extraction/number-verification.json | conferência numérica | valid=true ou divergência bloqueada |
| extraction/claim-ledger.json | autorização factual | claims públicos são verified |
| extraction/claim-provenance-report.json | cadeia claim-fonte-papel | valida contra claim-provenance-report.schema.json |
| extraction/source-map.md | ligação claim-fonte-localizador | cada claim liberado é localizável |

Não invente um script de geração para esses arquivos: os scripts listados
validam ou inicializam os artefatos que realmente existem; a conferência e a
decisão editorial continuam explícitas e rastreáveis.

## Stop conditions e caminho degradado

Pare e bloqueie a próxima etapa se houver troca de fonte, artigo completo
necessário mas indisponível, tabela ou desfecho essencial ilegível, direção do
efeito incerta, discrepância crítica, retratação não resolvida ou claim central
sem suporte. Registre a causa e o material necessário para destravar.

Em modo degradado, extraia apenas fatos que a fonte disponível sustenta
literalmente, marque cobertura incompleta e impeça claims dependentes de
material ausente. Abstract, press release, exemplo editorial e comentário
externo não são atalhos para liberar conclusão científica. Não escreva “não há
críticas” se não ocorreu busca registrada.

## Proibições

É proibido:

- inferir método ausente a partir de silêncio documental;
- substituir fonte primária por exemplar, resumo jornalístico ou autoridade
  editorial;
- descartar uma versão conflitante sem registro;
- atribuir cálculo do sistema aos autores;
- liberar para prosa um claim sem status verified;
- alterar originais, declarar que uma busca ocorreu quando não ocorreu, ou
  transformar crítica externa em fato estabelecido.

## Interação com outras skills

Esta skill recebe o job do reviews-writer e entrega o pacote factual a
reviews-scientific-appraisal. O appraisal devolve limites que podem bloquear
claims; reviews-editorial-brief usa apenas claims liberados; reviews-audit
reconfere a cadeia na candidata. Para fonte de estilo e correção humana, use
reviews-feedback-learning sem permitir que ela altere a autoridade científica.

## Evals, exemplos e casos adversariais

Os três exemplos concretos, três casos adversariais e seus resultados esperados
estão em references/examples-and-evals.md. Os quatro casos versionados
(positivo, negativo, limite e regressão) estão em evals/cases.json. Eles são
contratos declarativos executados com os scripts reais da seção de procedimento:
compare os artefatos produzidos aos critérios objetivos do caso e registre o
resultado no job. Não declare a skill pronta com base apenas em JSON bem
formado.

Critério de aprovação: os quatro casos produzem exatamente os artefatos
esperados, nenhum gate é contornado e todos os claims proibidos permanecem
fora do rascunho público.

## Checklist operacional executável

- Confirme identidade, versão e legibilidade de cada fonte relevante.
- Registre papéis, autoridade, ausências e discrepâncias em artefatos do job.
- Execute a normalização e a validação humana do documento.
- Valide source-roles, números e claim ledger com os scripts existentes.
- Crie o mapa de fontes que liga cada claim liberado ao seu localizador.
- Bloqueie a transferência se um claim central não puder ser auditado.
