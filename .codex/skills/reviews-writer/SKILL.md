---
name: reviews-writer
description: Orquestrar edições do Reviews com extração científica rastreável, análise metodológica, redação em português brasileiro, auditorias adversariais, revisão de edições existentes e incorporação controlada de feedback. Usar ao criar resposta clínica, síntese de diretriz, análise crítica de revisão ou estudo, edição temática, processar uma pasta ou lote de artigos, revisar uma candidata do Reviews ou comparar a candidata com correções editoriais.
---

# Reviews Writer

Produzir uma edição candidata auditável sem pular da fonte para a redação. Tratar o editor humano como autoridade final e o repositório como fonte normativa versionada.

## Preparação obrigatória

1. Localizar a raiz do repositório três níveis acima desta Skill.
2. Ler sempre:
   - `references/workflow.md`;
   - `references/source-hierarchy.md`;
   - `references/evidence-rules.md`;
   - `references/stop-conditions.md`;
   - `references/output-contracts.md`.
3. Ler `references/delegation-rules.md` antes de distribuir leitura ou auditorias.
4. Ler `references/drive-workflow.md` quando a origem ou o destino estiver no Drive.
5. Ler `references/visual-workflow.md` somente quando houver figuras, gráficos ou pedido visual.
6. Ler os contratos pertinentes em `editorial/edition-types/` e as regras metodológicas do desenho identificado.

Não carregar o corpus inteiro. Carregar `corpus/manifest.yml` com seus `curated_catalogs` e selecionar somente referências A/B aprovadas e pertinentes ao tipo, desenho e seção. Preservar `quality_status` e `known_limitations` no contexto: um B pode ser próximo do ideal sem ser perfeito. Nunca recuperar item marcado como `holdout`.

## Fluxo obrigatório

### 1. Receber e isolar

- Criar um `JOB-YYYY-NNN` com `scripts/create_job.py`.
- Registrar briefing, fontes, hashes, tipo solicitado e versões normativas.
- Preservar os originais; não editar, mover ou renomear o arquivo-fonte.
- Em lote, criar um job independente por artigo.

### 2. Validar e normalizar

- Executar `scripts/normalize_documents.py`.
- Confirmar artigo completo, versão, título, suplemento, protocolo, registro, tabelas, figuras e duplicatas.
- Nunca redigir diretamente de PDF ou DOCX.
- Não atribuir página a DOCX sem renderização confiável; usar parágrafo/seção e registrar a limitação.
- Obter confirmação humana, item a item, em `normalized/manual-document-review.json` antes de avançar.

### 3. Classificar e extrair

- Classificar o desenho antes de extrair conclusões.
- Inicializar os contratos com `scripts/extract_evidence.py --initialize`.
- Preencher população, intervenção, comparador, desfechos, tempos, estimativas, intervalos, segurança, perdas e população analítica apenas a partir das fontes.
- Usar `Informação não localizada nos materiais consultados.` quando faltar informação.
- Usar `Informação ambígua ou insuficientemente descrita no material disponível.` quando a descrição for insuficiente.

### 4. Verificar números e claims

- Conferir valor, unidade, direção, denominador, escala, tempo e análise entre grupos.
- Marcar todo cálculo derivado como cálculo do sistema e registrar o método.
- Construir o claim ledger com `scripts/build_claim_ledger.py`.
- Bloquear qualquer claim público sem fonte, excerto, localizador e status `verified`.
- Registrar discrepâncias entre texto, tabela, figura, suplemento, protocolo ou registro; nunca escolher silenciosamente.

### 5. Analisar metodologia e escrutínio externo

- Aplicar somente críticas específicas ao desenho e aos materiais reais.
- Separar problema demonstrado, possibilidade de viés, imprecisão, aplicabilidade e limite de inferência.
- Buscar registro, protocolo, plano de análise, errata, retratação, cartas, respostas e crítica metodológica pertinente.
- Registrar data, consulta e fonte. Se não houver acesso, declarar que a busca não foi realizada.
- Nunca apresentar PubPeer, fórum ou comentário externo como fato estabelecido.

### 6. Escolher arquitetura editorial

- Respeitar o tipo definido pelo editor salvo incompatibilidade crítica documentada.
- Sem tipo definido, usar `scripts/edition_router.py`, registrar justificativa e manter override.
- Planejar hierarquia de resultados: primários, críticos para decisão, segurança, secundários decisivos e exploratórios identificados.
- Não usar o título provisório da seção analítica I como decisão canônica.

### 7. Redigir

Redigir somente após pacote factual, análise metodológica, pesquisa externa, plano e exemplares estarem registrados. Usar exclusivamente:

- claims autorizados;
- limites de inferência;
- plano editorial;
- exemplares selecionados;
- regras editoriais aprovadas.

Escrever originalmente em português brasileiro. Conduzir a leitura sem preencher lacunas, suavizar incertezas ou repetir números sem função.

### 8. Auditar em sequência

1. auditoria factual adversarial;
2. auditoria estatística e metodológica;
3. revisão estrutural;
4. revisão de estilo Reviews;
5. revisão de português natural e anti-IA;
6. revisão de coerência;
7. auditoria final completa.

Usar `scripts/audit_draft.py` para o gate automático. Tratar o linter anti-IA como heurística, nunca como detector de autoria. Qualquer erro crítico bloqueia o avanço.

### 9. Finalizar e entregar

- Gerar todos os arquivos do estado candidato descritos em `references/output-contracts.md`.
- Exportar DOCX com `scripts/export_docx.py` e executar renderização/inspeção visual antes da entrega.
- Preparar a transferência com `scripts/publish_to_drive.py`; o script não executa o conector.
- Informar explicitamente o job, a candidata dentro de `final/` e os IDs de produção autorizados; nunca usar a pasta-fonte como destino.
- Importar como arquivo novo somente na pasta de produção autorizada e verificar o ID/URL retornado.
- Definir o status como `AGUARDANDO REVISÃO EDITORIAL`.
- Usar `APROVADA PARA PUBLICAÇÃO` somente após autorização humana explícita e registrada.

### 10. Incorporar feedback

- Comparar candidata e revisada com `scripts/compare_versions.py`.
- Classificar cada mudança com `scripts/incorporate_feedback.py`.
- Não alterar regras automaticamente.
- Promover regra somente com justificativa, destino, exemplo antes/depois, teste de regressão existente dentro do repositório, casos anteriores aprovados e aprovação editorial.

## Delegação

Paralelizar inventário, normalização e auditorias independentes quando houver benefício. Manter redação, consolidação e edição final sequenciais. Cada subagente deve receber somente o pacote necessário e devolver artefatos estruturados; nunca usar memória conversacional como fonte factual.

## Proibições

- Não inventar, completar lacunas ou criar referências.
- Não transformar ausência de relato em ausência do método.
- Não concluir ausência de efeito apenas por `p > 0,05`.
- Não usar mudança intragrupo como efeito entre grupos.
- Não promover exploratórios, subgrupos ou substitutos a benefício clínico sem suporte.
- Não criticar representatividade de forma automática.
- Não construir interface, API, autenticação, Supabase, banco remoto ou publicação automática.
- Não modificar o Drive histórico nem sobrescrever documentos.
- Não produzir edição real antes do pipeline factual mínimo.

## Saída ao bloquear

Não abandonar o job. Produzir o relatório do problema, os artefatos concluídos, os materiais faltantes e o caminho seguro de continuidade. Manter o último estado válido.
