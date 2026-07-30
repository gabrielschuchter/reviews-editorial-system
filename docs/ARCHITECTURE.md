# Arquitetura do sistema editorial

> Status desta documentação: núcleo local verificável `0.3.0`, com 11 skills operacionais, contratos e evals; ainda sem piloto editorial científico completo. Ela descreve o que o repositório implementa hoje e separa isso do que ainda depende do Codex, do conector do Google Drive ou de decisão editorial humana.

## Objetivo e limites

O Reviews Editorial System é um fluxo local, orientado a arquivos e operado pelo Codex. Seu objetivo é transformar documentos científicos em uma candidata auditável, preservando a origem de cada afirmação e mantendo a aprovação editorial como decisão humana.

O sistema não é uma aplicação web. Não há frontend, painel, API própria, autenticação, Supabase, banco remoto, fila distribuída ou publicação automática. O Google Drive funciona como biblioteca externa e destino autorizado; o Google Docs é uma superfície de revisão, não o banco de estado do pipeline.

## Mapa de componentes

```text
Google Drive — arquivo-fonte (somente leitura por política)
                         │
                         │ descoberta/obtenção mediada pelo Codex
                         ▼
fontes locais imutáveis ─┬─> inventário e classificação proposta
                         └─> job isolado JOB-YYYY-NNN
                                  │
                                  ▼
                    normalização e artefatos estruturados
                                  │
                                  ▼
              extração validada + números + claim ledger
                                  │
                                  ▼
                análise metodológica + plano editorial
                                  │
                                  ▼
                    redação Codex + auditorias em ordem
                                  │
                                  ▼
                    candidata Markdown/DOCX local
                                  │
                                  ▼
            manifesto de transferência + conector do Drive
                                  │
                                  ▼
              Google Drive — produção / Google Docs
                                  │
                                  ▼
                     revisão e aprovação humanas
```

## Camadas do repositório

| Camada | Responsabilidade | Natureza atual |
|---|---|---|
| `.codex/skills/reviews-*/` | Orquestrar e executar capacidades editoriais especializadas, com contratos e evals | 11 bundles Codex-native; cada um contém gates, referências, manifestos de eval e caminhos de artefatos |
| `editorial/` | Regras, contratos de edição, terminologia e checklists | Configuração versionada; itens provisórios não são canônicos |
| `schemas/` | Contratos de dados de jobs, estudos, claims, issues e ativos | 22 JSON Schemas Draft 2020-12 |
| `src/reviews_editorial/` | Núcleo determinístico compartilhado | Python 3.11+, sem dependências obrigatórias |
| `scripts/` | Entradas de linha de comando | Adaptadores finos sobre o núcleo Python |
| `corpus/` | Manifesto, curadoria, exemplares e holdout | Deve ser populado por inventário e aprovação; não contém autoridade automática |
| `jobs/` | Estado e artefatos de cada edição | Um diretório isolado por edição |
| `evals/` e `tests/` | Avaliação editorial, regressão e testes de código | Evidência de qualidade somente quando os comandos forem executados e os resultados registrados |
| `docs/` | Decisões e operação técnica | Documentação, não substitui gates executáveis |
| `.reviews/` | SQLite local, cache operacional e índice transacional | Privado e ignorado pelo Git; deriva e integra o estado dos jobs |
| `migrations/` | Evolução versionada do registro editorial | Aplicada automaticamente pela CLI e pelas integrações do núcleo |

## O que o núcleo determinístico faz

- cria jobs, calcula hashes das fontes e opcionalmente copia entradas sem alterar os originais;
- normaliza `.docx`, `.pdf`, `.md`, `.mdx`, `.txt` e HTML em texto e mapas auditáveis;
- exige confirmação manual da validação documental;
- valida a presença dos artefatos exigidos por estado e permite avanço de apenas um estado por vez;
- recomenda um tipo de edição por regras explícitas e registra incompatibilidades;
- valida registros numéricos, claims, feedback e um subconjunto de JSON Schema;
- valida proveniência por claim, appraisal por desfecho, framing proporcional e auditorias anti-IA por ocorrência;
- aplica humanização mínima somente após confirmação humana, com diff e reauditoria de claims;
- seleciona somente exemplares A/B que já tenham sido aprovados e anotados;
- exporta Markdown para um DOCX simples, compatível com importação no Google Docs;
- prepara um manifesto seguro de transferência para o Drive.

## O que o núcleo não faz sozinho

- não interpreta semanticamente um artigo nem produz uma extração científica completa;
- não confirma se o artigo, suplemento, protocolo ou guideline é a versão correta;
- não executa OCR, reconhecimento confiável de tabelas de PDF ou inspeção visual de figuras;
- não realiza pesquisa externa automaticamente a partir dos scripts locais;
- não redige, revisa ou aprova uma edição sem atuação do Codex e do editor;
- não agenda subagentes nem implementa um runtime próprio de agentes;
- não envia arquivos ao Drive: `publish_to_drive.py` apenas gera `drive-transfer.json`;
- não transforma frequência no corpus, feedback ou pontuação em regra canônica.

Essa separação é intencional. Scripts cuidam de invariantes verificáveis; julgamento editorial e metodológico permanece explícito e auditável.

## Registro editorial integrado

`job.yml` permanece a fonte operacional do estado do job. O registro SQLite não o substitui: ele normaliza identidades entre jobs, documentos, versões, execuções de agentes e fontes externas, além de fornecer histórico append-only, busca contextual e linhagem.

Os pontos de integração são `create_job`, `advance_job`, confirmação documental, registro de revisão e os comandos `sync-job`/`sync-all-jobs`. O arquivo privado do Drive fica fora do repositório; somente snapshot, contratos, metadados, classificações e relações são versionados. Papéis do registro são gates editoriais auditáveis, não autenticação ou segurança real.

## Estado do job e máquina de estados

O arquivo `job.yml` é a fonte local de estado. Ele registra solicitação, documentos, hashes, versões, gates e histórico. A sequência contém vinte estados, de `received` a `approved`.

`validate_pipeline()` verifica todos os outputs exigidos até o estado-alvo. `advance_job()`:

1. aceita somente o estado imediatamente seguinte;
2. bloqueia outputs obrigatórios ausentes;
3. exige validação documental confirmada a partir de `documents_validated`;
4. bloqueia erros críticos encontrados no job e em auditorias JSON;
5. exige registro de revisão humana nos estados finais;
6. exige `human_approval=True` e um artefato de aprovação para chegar a `approved`.

Arquivos Markdown de auditoria não são interpretados semanticamente pela máquina de estados. Se contiverem um bloqueio, ele também precisa ser registrado em um artefato JSON ou em `job.yml.gates.critical_errors`.

## Autoridade e fronteiras de confiança

Da maior para a menor autoridade normativa:

1. decisão explícita atual do editor humano;
2. constituição e regras canônicas aprovadas;
3. contratos e checklists versionados aprovados;
4. exemplares A/B aprovados e pertinentes;
5. materiais publicados históricos;
6. propostas, prompts antigos, padrões frequentes e inferências do sistema.

O modelo, o conector e os scripts são operadores, não autoridades editoriais. Uma candidata aprovada tecnicamente continua com o status `AGUARDANDO REVISÃO EDITORIAL` até decisão humana explícita.

## Versionamento e reprodutibilidade

Cada job registra versões do sistema, Skill, constituição, contrato de edição, metodologia, perfil de estilo, regras anti-IA, corpus, design system e modelo, além da data e dos hashes das fontes. Valores provisórios como `unapproved` ou `candidate-unverified` devem ser preservados enquanto não houver aprovação.

Mudanças futuras não reescrevem retroativamente jobs concluídos. Para reproduzir uma edição, preserve o job, seus artefatos, as versões registradas e as fontes identificadas pelos hashes.

## Decisões ainda pendentes

- quais itens do corpus serão A ou B;
- quais contratos de edição serão canônicos e quais títulos de seção serão aprovados;
- qual perfil de estilo representa o Reviews atual;
- se a documentação de design reversamente inferida será validada total ou parcialmente;
- quais permissões e propriedades de visibilidade existem na pasta de produção do Drive;
- quais pilotos demonstram que o MVP atende ao padrão editorial real.

Nenhuma dessas decisões deve ser preenchida silenciosamente por conveniência técnica.
