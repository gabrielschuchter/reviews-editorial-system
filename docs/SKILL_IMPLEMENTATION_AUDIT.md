# Auditoria de implementação das skills

## Escopo e método

Este relatório separa a constatação inicial da reconstrução em andamento. Uma
skill só é tratada como operacional quando tem instruções acionáveis, contratos
de saída, caminhos de artefatos, recursos locais resolvíveis, evals versionados e
evidência de execução. Nome de pasta, frontmatter, lista de links ou arquivo
curto não são prova de implementação.

A auditoria inicial foi feita sobre o clone no commit auditado 109174a. Ela
encontrou oito bundles existentes em .codex/skills/, todos rasos: seus
SKILL.md tinham entre 20 e 51 linhas úteis e descreviam passos genéricos, sem
uma cadeia completa de gates, contratos, degradação e avaliação. Três
capabilities obrigatórias não existiam: reviews-journalistic-framing,
reviews-anti-ai-writing e reviews-humanizer-ptbr.

Naquele momento, o repositório tinha catálogos e manifests do corpus, mas não
trazia o conteúdo editorial do Drive no clone. Isso impedia inferir estilo,
julgamento humano ou regras de reescrita a partir de nomes de arquivo. A
reconstrução deve usar evidência derivada e rastreável do material lido, sem
copiar silenciosamente documentos vivos para o repositório.

## Baseline executado na auditoria inicial

| Comando ou inspeção | Resultado observado no baseline | Limite da evidência |
| --- | --- | --- |
| python -m unittest discover -s tests -v | 27 testes passaram | Cobria o código já existente, não profundidade das skills. |
| python scripts/run_checks.py | Passou; 17 schemas e 7 evals legados foram verificados | Não validava os contratos de cada skill. |
| python scripts/run_evals.py | 7 de 7 casos passaram | Os casos não cobriam todas as capabilities obrigatórias. |
| python scripts/scan_skills.py | Executado; a versão inicial restringia-se a três verificações regex | Não era uma inspeção recursiva suficiente de conteúdo externo ou de implementação. |
| Validador profundo por skill | Não existia uma checagem integrada que distinguisse bundle operacional de frontmatter, links e texto curto | A reconstrução precisava criar validação de triggers, seções, referências, contratos, stop conditions e evals. |
| CLIs de artefato e tabela | validate_artifact.py e validate_tables.py falhavam quando chamados diretamente por falta de bootstrap de importação | Falha de integração de CLI, não aprovação do comportamento. |

Como inspeção posterior de estrutura, antes da validação integrada final, há agora
11 diretórios de skills e 11 manifestos evals/cases.json; os SKILL.md atuais
têm de 74 a 217 linhas não vazias. Essa contagem não substitui a execução
integrada de todos os gates.

## Inventário por capability

| Skill | Estado anterior | Problemas | Fontes necessárias | Implementação exigida / realizada | Evals manifestos | Status final |
| --- | --- | --- | --- | --- | --- | --- |
| reviews-writer | Existia; raso, na faixa de 20–51 linhas úteis | Orquestração sem seleção verificável, sem retorno por gate e sem handoff de job | Corpus Reviews; OpenAI Skills/Skill Creator; Codex; guia de prompting | Orquestrador com preflight, plano de capabilities, estados de job, handoff e bloqueios explícitos; integração com capabilities especializadas | evals/cases.json presente; deve cobrir plano, bloqueio, limite e regressão | Implementada e validada; ver addendum |
| reviews-source-provenance | Existia; raso, na faixa de 20–51 linhas úteis | Fonte, papel, versão, localizador e claim não eram um contrato operacional completo | Corpus Reviews; regras de fonte; K-Dense; ASReview; RobotReviewer | Hierarquia de autoridade, inventário, normalização, extração localizável, claim ledger e retorno seguro para lacunas | evals/cases.json presente; deve cobrir proveniência positiva, fonte ausente, ambiguidade e regressão | Implementada e validada; ver addendum |
| reviews-scientific-appraisal | Existia; raso, na faixa de 20–51 linhas úteis | Listas de risco de viés e certeza sem julgamento por desfecho, limites ou contrato | EQUATOR; Cochrane RoB; GRADE; metafor; corpus Reviews | Roteamento por desenho, risco de viés, certeza, efeito absoluto, multiplicidade, subgrupo, dados ausentes, causalidade e aplicabilidade | evals/cases.json presente; deve cobrir desenho, incerteza, limite e regressão | Implementada e validada; ver addendum |
| reviews-editorial-brief | Existia; raso, na faixa de 20–51 linhas úteis | Pauta não vinculava decisão, leitor, escopo, claims permitidos e cobertura | Edições finais e auditorias humanas do Reviews; regras de fonte e de título | Brief estruturado com pergunta, leitor, promessa proporcional, escopo, critérios de inclusão, riscos e autorização de passagem | evals/cases.json presente; deve cobrir brief suficiente, briefing incompleto, ambiguidade e regressão | Implementada e validada; ver addendum |
| reviews-journalistic-framing | Ausente | Não havia capability para ângulo, conflito, contraponto, título proporcional e limites jornalísticos | Corpus Reviews; correções humanas; regras de fonte; títulos e subtítulos | Memo de framing, teste de título/subtítulo, distinção de fato/inferência/hipótese, contraponto proporcional e retorno para appraisal quando necessário | evals/cases.json presente; deve cobrir framing proporcional, exagero, conflito e regressão | Implementada e validada; ver addendum |
| reviews-edition-writing | Existia; raso, na faixa de 20–51 linhas úteis | Redação não exigia inputs suficientes, preservação de claims, estrutura por tipo ou reauditoria | Corpus Reviews; brief; framing; claim ledger; appraisal | Procedimento por tipo de edição, estrutura de parágrafo/tabela, controle de modalidade e encaminhamento de lacunas aos responsáveis | evals/cases.json presente; deve cobrir redação sustentada, claim sem suporte, caso-limite e regressão | Implementada e validada; ver addendum |
| reviews-anti-ai-writing | Ausente | Não havia auditoria separada de padrões artificiais nem risco de falso positivo | Corpus Reviews; Avoid AI Writing; Blader Humanizer; Wikipedia como taxonomia descritiva | Auditoria sem reescrita, por ocorrência, com trecho, categoria, evidência, gravidade, confiança, risco de falso positivo e recomendação localizada | evals/cases.json presente; deve cobrir texto humano preservado, sinal artificial, limite e regressão | Implementada e validada; ver addendum |
| reviews-humanizer-ptbr | Ausente | Não havia edição mínima com preservação factual, diff e possibilidade de rejeição | Corpus Reviews; correções humanas; Avoid AI Writing; Blader Humanizer; taxonomia anti-IA | Confirmação humana de finding, alteração localizada, diff antes/depois, reauditoria de claims afetados e proteção de fatos, números e modalidade | evals/cases.json presente; deve cobrir correção mínima, rejeição, claim protegido e regressão | Implementada e validada; ver addendum |
| reviews-audit | Existia; raso, na faixa de 20–51 linhas úteis | Auditoria misturava correção e veredito e não cobria dimensões independentes | Corpus Reviews; claim ledger; Cochrane; GRADE; regras factuais e de tabela | Findings independentes com cobertura, categoria, severidade, confiança, evidência, responsável, retorno e reauditoria; sem editar a candidata | evals/cases.json presente; deve cobrir finding sustentado, blocker, cobertura parcial e regressão | Implementada e validada; ver addendum |
| reviews-document-presentation | Existia; raso, na faixa de 20–51 linhas úteis | Exportação não era tratada como gate de legibilidade, tabela, referência e renderização | Edições finais do Reviews; sistema visual; Anthropic DOCX Skill | Preparação de candidato, DOCX, renderização, inspeção de tabelas e referências, relatório de apresentação e bloqueio de conteúdo oculto | evals/cases.json presente; deve cobrir apresentação íntegra, quebra crítica, limite de render e regressão | Implementada e validada; ver addendum |
| reviews-feedback-learning | Existia; raso, na faixa de 20–51 linhas úteis | Correções humanas podiam virar regra sem comparação, hipótese, holdout ou aprovação | Corpus Reviews; pares antes/depois; Promptfoo; princípios de avaliação | Comparação versionada, classificação de mudança, hipótese limitada, proposta de regra, holdout e promoção somente após aprovação humana | evals/cases.json presente; deve cobrir aprendizado aceito, promoção indevida, caso ambíguo e regressão | Implementada e validada; ver addendum |

## Critérios de fechamento ainda obrigatórios

A validação integrada final permanece pendente neste relatório. Ela deve rodar
depois de estabilizadas todas as alterações compartilhadas e precisa demonstrar,
no mínimo:

1. todos os bundles passam o validador de skills, sem exceção por skill;
2. os manifestos de eval são sintaticamente válidos e seus contratos são
   exercitados pelo runner apropriado;
3. testes unitários, checks, evals determinísticos e scanner passam na mesma
   árvore de trabalho;
4. referências locais citadas são resolvíveis e caminhos de scripts/contratos
   existem;
5. o orquestrador seleciona e encadeia capabilities em um job de ponta a ponta;
6. anti-IA e humanizer demonstram relatório por ocorrência, diff mínimo e
   reauditoria factual;
7. nenhuma capability é declarada pronta somente por volume de texto ou pela
   existência de arquivos.

Consulte também [SOURCE_ADOPTION_MAP.md](SOURCE_ADOPTION_MAP.md) para a prova de
leitura, adaptação e rejeição das fontes externas e do corpus.

## Addendum: validação integrada de fechamento

As células `pendente` na tabela acima registram o snapshot estrutural feito
antes da execução conjunta; foram superadas pelos resultados abaixo. As 11
skills estão implementadas e validadas. Os `SKILL.md` atuais têm de 70 a 213
linhas úteis e, com recursos locais diretamente ligados, de 172 a 385 linhas
operacionais. Cada uma possui quatro casos versionados: positivo, negativo,
limite e regressão.

| Verificação executada | Resultado real |
| --- | --- |
| `python -m unittest discover -s tests -v` | 57 testes passaram |
| `python scripts/run_checks.py` | 22 schemas, 11 skills e 15 regressões aprovados |
| `python scripts/run_evals.py` | 15 de 15 regressões runtime passaram |
| `python scripts/run_skill_evals.py` | 11 manifests e 44 de 44 contratos declarativos aprovados; 15 de 15 regressões runtime e a rota das 11 skills passaram; sem execução de LLM |
| `python scripts/validate_skills.py .codex/skills` | 11 de 11 bundles válidos, sem referência ou artefato local ausente |
| `python scripts/scan_skills.py` | 75 arquivos inspecionados, 0 achados críticos e validação de implementação aprovada |
| `python scripts/run_integration_smoke.py` | Job completo de `received` a `candidate_for_review`, com DOCX válido, diff humanizado e `validate_job.py` aprovado; continua aguardando revisão humana |

O validador profundo reprova bundle vazio/superficial, marcador de placeholder,
trigger, contrato de saída, stop condition, eval ou recurso local ausente. O
runner de manifestos não se apresenta como avaliação de LLM: valida contratos,
critérios e produtores/schemas reais; as regressões determinísticas e a suíte
de testes exercitam o comportamento implementado.
