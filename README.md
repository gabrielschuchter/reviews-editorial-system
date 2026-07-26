# Reviews Editorial System

> Sistema editorial Codex-native, auditável e orientado por evidências para transformar material científico em candidatas do Reviews — sem automatizar a decisão editorial humana.

O Reviews Editorial System organiza o trabalho que normalmente se perde entre documentos, versões, anotações e memória de equipe: recebe fontes, preserva evidências, constrói um ledger de claims, dimensiona a certeza científica, define o enquadramento jornalístico, redige uma candidata, audita riscos e prepara a revisão humana.

Ele não é um CMS nem uma ferramenta de publicação automática. É o sistema de trabalho que torna uma decisão editorial verificável.

## Para quem é

Este repositório serve a editores, redatores, revisores científicos e agentes Codex que trabalham com edições do Reviews baseadas em artigos, diretrizes, revisões, tabelas e materiais suplementares.

Use-o quando for necessário responder, com evidência localizável:

- de onde veio cada afirmação relevante;
- o que o estudo realmente mostra — e o que ele não mostra;
- qual é a força e a aplicabilidade de uma recomendação;
- onde a redação passa de dado para inferência;
- quais alterações humanas foram feitas e se podem, ou não, informar regras futuras.

## Princípios inegociáveis

| Princípio | Como o sistema aplica |
| --- | --- |
| Evidência antes de prosa | Nenhuma edição parte diretamente de PDF ou DOCX: a fonte é normalizada, revisada e extraída antes da redação. |
| Claim rastreável | Afirmações factuais relevantes precisam apontar para evidência no claim ledger. |
| Proporção | Título, lead, conclusão e recomendação não podem ser mais fortes que a evidência disponível. |
| Separação de papéis | Auditar não é corrigir; corrigir não é aprovar; aprender com feedback não é promover regra automaticamente. |
| Preservação factual | O humanizer não muda fatos, números, unidades, referências, direção de efeito, incerteza ou modalidade epistêmica. |
| Decisão humana | O fluxo termina em <code>AGUARDANDO REVISÃO EDITORIAL</code>. Somente uma pessoa pode aprovar ou publicar. |

## Estrutura do repositório

~~~text
.codex/skills/              Skills acionáveis pelo Codex
editorial/                  Constituição, estilo, metodologia e regras por edição
corpus/                     Metadados, evidências de estilo e curadoria
schemas/                    Contratos JSON Schema para artefatos editoriais
src/reviews_editorial/      Núcleo determinístico compartilhado pelos comandos
scripts/                    CLIs para executar e validar o fluxo
jobs/                       Um diretório isolado por edição em andamento
evals/                      Regressões editoriais versionadas
tests/                      Testes automatizados de contratos e comportamento
docs/                       Arquitetura, auditoria de implementação e adoção de fontes
~~~

O corpus guarda metadados e evidências de curadoria; não é uma cópia silenciosa do acervo nem substitui a consulta às fontes autorizadas.

## As 11 skills

<code>reviews-writer</code> é a entrada para qualquer trabalho editorial. Ela faz o preflight e seleciona as capacidades abaixo; não substitui seus gates.

| Skill | Responsabilidade | Principal resultado |
| --- | --- | --- |
| <code>reviews-writer</code> | Orquestrar etapas, checar pré-condições e impedir saltos | <code>capability-plan.json</code> |
| <code>reviews-source-provenance</code> | Mapear fonte, versão, papel, trecho e claim | relatório de proveniência e claim ledger |
| <code>reviews-scientific-appraisal</code> | Avaliar risco de viés, certeza, efeito, aplicabilidade e limites | appraisal por desfecho |
| <code>reviews-editorial-brief</code> | Definir leitor, decisão, escopo, promessa e claims permitidos | brief editorial |
| <code>reviews-journalistic-framing</code> | Criar ângulo proporcional, contraponto e título responsável | memo de framing |
| <code>reviews-edition-writing</code> | Redigir a candidata com claims sustentados | candidata editorial |
| <code>reviews-anti-ai-writing</code> | Auditar padrões artificiais sem reescrever ou atribuir autoria | relatório por ocorrência |
| <code>reviews-humanizer-ptbr</code> | Aplicar somente edições mínimas confirmadas e reauditar claims | diff e texto revisado |
| <code>reviews-audit</code> | Produzir findings independentes, com severidade e responsável | auditorias factual, inferencial e final |
| <code>reviews-document-presentation</code> | Preparar DOCX, tabelas e referências para inspeção | relatório de apresentação |
| <code>reviews-feedback-learning</code> | Transformar feedback em hipótese testável, nunca em regra automática | proposta de aprendizado pendente |

Cada bundle de skill contém gatilhos, situações de não uso, gates, contratos de saída, stop conditions, exemplos, casos adversariais e quatro evals mínimos: positivo, negativo, limite e regressão.

## Fluxo editorial

~~~mermaid
flowchart LR
    A[Fontes recebidas] --> B[Job isolado]
    B --> C[Normalização e revisão documental]
    C --> D[Extração curada e claim ledger]
    D --> E[Appraisal científico]
    E --> F[Brief e framing]
    F --> G[Redação da candidata]
    G --> H[Auditorias independentes]
    H --> I[Anti-IA e humanização mínima]
    I --> J[DOCX e inspeção visual]
    J --> K[AGUARDANDO REVISÃO EDITORIAL]
    K --> L[Feedback humano e aprendizado controlado]
~~~

### Gates que não podem ser ignorados

O sistema interrompe o avanço se o artigo completo, desfecho primário, comparador, direção do efeito ou tabelas essenciais não puderem ser confirmados. Também bloqueia um job com fonte trocada, claim sem base, número público sem correspondência no ledger, recomendação sem qualificador ou documento essencial ilegível.

Uma auditoria aprovada não significa publicação. Ela demonstra apenas que os checks definidos foram executados e registrados.

## Instalação

Requer Python 3.11 ou superior. O núcleo não depende de bibliotecas externas.

~~~powershell
git clone https://github.com/gabrielschuchter/reviews-editorial-system.git
cd reviews-editorial-system
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
~~~

Para normalização de PDF e exportação DOCX, instale o extra opcional:

~~~powershell
python -m pip install -e ".[documents]"
~~~

Sem esse extra, o sistema falha de forma explícita nas operações que exigem PDF/DOCX; ele não inventa uma extração alternativa.

## Início rápido: validar a instalação

Execute estes comandos a partir da raiz do repositório:

~~~powershell
python -m unittest discover -s tests -v
python scripts/run_checks.py
python scripts/run_evals.py
python scripts/run_skill_evals.py
python scripts/scan_skills.py
python scripts/run_integration_smoke.py
~~~

O smoke test percorre uma fixture completa até <code>candidate_for_review</code>, incluindo proveniência, appraisal, auditorias, anti-IA, humanização, DOCX e validação final do job. Ele não aprova nem publica uma edição.

## Primeiro job, passo a passo

### 1. Criar um job isolado

Um job conserva artefatos, decisões e auditorias de uma única edição. Não use uma pasta compartilhada para dois temas.

~~~powershell
python scripts/create_job.py --source "C:\fontes\artigo-principal.pdf" --topic "Tema da edição" --edition-type "analise" --editor "Nome do editor"
~~~

Anote o diretório retornado, por exemplo <code>jobs/2026-07-25-tema-da-edicao</code>.

### 2. Normalizar e confirmar os documentos

~~~powershell
python scripts/normalize_documents.py jobs\2026-07-25-tema-da-edicao
python scripts/validate_job.py jobs\2026-07-25-tema-da-edicao --confirm-documents "Nome do revisor"
~~~

Antes da confirmação, revise <code>normalized/missing-materials.md</code>, <code>page-map.json</code>, <code>table-map.json</code>, <code>figure-map.json</code> e <code>manual-document-review.json</code>. A confirmação exige campos explícitos; um nome de revisor sozinho não basta.

### 3. Extrair evidência e construir o ledger

Prepare um pacote curado de extração com trechos localizáveis e artefatos exigidos. O comando valida o pacote; ele não cria placeholders.

~~~powershell
python scripts/extract_evidence.py jobs\2026-07-25-tema-da-edicao --input C:\curadoria\extracao-validada.json
python scripts/verify_numbers.py jobs\2026-07-25-tema-da-edicao
python scripts/build_claim_ledger.py jobs\2026-07-25-tema-da-edicao
~~~

Quando a informação não estiver disponível, registre literalmente uma das formulações previstas nas regras editoriais, em vez de preencher uma lacuna com hipótese.

### 4. Planejar com o orquestrador

O orquestrador exige um contexto JSON (ou YAML no subconjunto JSON) e devolve o plano de capabilities aplicável ao estágio atual.

~~~powershell
python scripts/orchestrate_reviews.py C:\curadoria\contexto-do-job.json --output jobs\2026-07-25-tema-da-edicao\analysis\capability-plan.json
~~~

Em seguida, registre classificação do estudo, revisão metodológica, limites inferenciais, questões críticas, brief e framing. Consulte as skills especializadas e <code>README-OPERACIONAL.md</code> para os contratos de cada artefato.

### 5. Redigir, auditar e revisar o estilo

A redação só começa com pacote validado, plano editorial e exemplares selecionados. A ordem é importante:

1. auditoria factual;
2. auditoria estatística e metodológica;
3. revisão estrutural;
4. auditoria de estilo e anti-IA;
5. auditoria de coerência;
6. auditoria final.

Para a revisão de padrões artificiais, use o auditor separado:

~~~powershell
python scripts/audit_anti_ai.py --input jobs\2026-07-25-tema-da-edicao\final\candidate.md --output jobs\2026-07-25-tema-da-edicao\audits\anti-ai-report.json
~~~

O relatório classifica ocorrências como abertura genérica, transição formulaica, atribuição vaga, cadência uniforme, conclusão vazia e outros padrões. Ele não reescreve o texto e não alega detectar autoria por IA.

Depois de decisão humana por finding, o humanizer pode fazer uma edição limitada:

~~~powershell
python scripts/humanize_ptbr.py --input jobs\2026-07-25-tema-da-edicao\final\candidate.md --anti-ai-report jobs\2026-07-25-tema-da-edicao\audits\anti-ai-report.json --decisions C:\curadoria\decisoes-humanas.json --output jobs\2026-07-25-tema-da-edicao\audits\humanization-diff.json --rewritten-output jobs\2026-07-25-tema-da-edicao\final\candidate-humanized.md --ledger jobs\2026-07-25-tema-da-edicao\extraction\claim-ledger.json
~~~

O comando produz diff antes/depois, recusa edições não confirmadas ou excessivas e preserva tokens factuais protegidos.

### 6. Preparar a entrega editorial

~~~powershell
python scripts/export_docx.py jobs\2026-07-25-tema-da-edicao\final\candidate.md jobs\2026-07-25-tema-da-edicao\final\candidate.docx
python scripts/validate_job.py jobs\2026-07-25-tema-da-edicao
~~~

Inspecione o DOCX renderizado antes de entregar. Para Drive/Google Docs, prepare a transferência com <code>scripts/publish_to_drive.py</code>; esse comando prepara o artefato, mas não faz upload nem sobrescreve histórico. O conector deve ser usado somente na pasta de produção autorizada.

## Contratos e artefatos importantes

| Artefato | Pergunta que responde | Validador ou produtor |
| --- | --- | --- |
| <code>extraction/claim-ledger.json</code> | Este claim tem fonte, trecho e limites? | <code>build_claim_ledger.py</code> |
| <code>analysis/scientific-appraisal.json</code> | Qual é a certeza, efeito, risco e aplicabilidade? | <code>validate_scientific_appraisal.py</code> |
| <code>analysis/editorial-brief.json</code> | Para quem escrevemos e o que é permitido afirmar? | skill <code>reviews-editorial-brief</code> |
| <code>analysis/framing-memo.json</code> | Qual ângulo é proporcional e que contraponto é necessário? | <code>validate_framing.py</code> |
| <code>audits/anti-ai-report.json</code> | Quais padrões artificiais merecem revisão localizada? | <code>audit_anti_ai.py</code> |
| <code>audits/humanization-diff.json</code> | O que mudou, por quê e quais claims foram rechecados? | <code>humanize_ptbr.py</code> |
| <code>final/candidate.md</code> | Qual é a edição candidata auditável? | redação + auditorias |
| <code>final/editorial-report.md</code> | O que foi verificado, bloqueado ou devolvido? | auditoria final |

Os schemas em <code>schemas/</code> são contratos de máquina; as regras em <code>editorial/</code> explicam o julgamento humano que os schemas não conseguem substituir.

## Segurança, escopo e privacidade

- Originais e histórico do Drive são somente leitura.
- Não há autenticação, banco remoto, API de publicação ou serviço em nuvem neste projeto.
- O scanner local de skills procura instruções inseguras, exfiltração de credenciais, execução remota e comandos destrutivos sem escopo.
- A revisão anti-IA descreve padrões de escrita; não mede “humanidade” e não acusa autoria.
- Feedback humano vira apenas uma proposta local até ter hipótese, exemplo antes/depois, holdout, regressão e aprovação editorial explícita.

## Testes e qualidade

| Comando | O que cobre |
| --- | --- |
| <code>python -m unittest discover -s tests -v</code> | Núcleo determinístico, CLIs, contratos e integrações |
| <code>python scripts/run_checks.py</code> | Schemas, invariantes editoriais, corpus e estrutura das skills |
| <code>python scripts/run_evals.py</code> | Regressões editoriais determinísticas |
| <code>python scripts/run_skill_evals.py</code> | Manifests por skill, contratos de saída e rota do orquestrador |
| <code>python scripts/validate_skills.py .codex/skills</code> | Profundidade, referências, gatilhos, stop conditions e evals dos bundles |
| <code>python scripts/scan_skills.py</code> | Inspeção local de segurança e implementação das skills |
| <code>python scripts/run_integration_smoke.py</code> | Fluxo completo por fixture até revisão editorial |

Os manifests de skill validam contratos e produtores reais. Eles não são apresentados como uma avaliação semântica automática de texto gerado por LLM.

## Onde encontrar cada orientação

- Fluxo cotidiano e ordem de operações: <code>README-OPERACIONAL.md</code>
- Limites entre componentes: <code>docs/ARCHITECTURE.md</code>
- Auditoria antes/depois das skills: <code>docs/SKILL_IMPLEMENTATION_AUDIT.md</code>
- Fontes estudadas, adaptações e rejeições: <code>docs/SOURCE_ADOPTION_MAP.md</code>
- Resultado e limites da inspeção de segurança: <code>docs/SECURITY_SKILL_SCAN.md</code>
- Decisões que ainda exigem aprovação: <code>EDITORIAL_DECISIONS_PENDING.md</code>
- Regras detalhadas de método, fonte e estilo: <code>editorial/</code>

## Troubleshooting

| Situação | O que fazer |
| --- | --- |
| PDF/DOCX não normaliza | Instale <code>.[documents]</code>, confira legibilidade do arquivo e registre a limitação; não redija a partir de uma leitura parcial. |
| <code>validate_job.py</code> bloqueia o avanço | Leia o resultado do gate e corrija o artefato indicado. Não avance por override informal. |
| Claim sem fonte | Volte à extração, inclua localizador e reconstrua o ledger; se não houver base, retire ou qualifique o claim. |
| Humanizer recusa a alteração | Confirme o finding, reduza a operação ou preserve o texto. Não contorne os limites alterando o documento inteiro. |
| Título parece mais forte que os dados | Retorne ao framing e ao appraisal; o título deve refletir a certeza e as condições da evidência. |
| Há feedback humano recorrente | Registre como hipótese em <code>reviews-feedback-learning</code>; não transforme em regra global sem avaliação e aprovação. |

## Limites deliberados

Este sistema não substitui revisão por pares, análise estatística especializada, leitura clínica, decisão jurídica, aprovação editorial nem a relação com fontes humanas. Ele torna os limites explícitos, preserva a trilha de decisão e reduz o espaço para que uma candidata pareça mais certa do que a evidência permite.

---

Para começar um piloto, leia <code>README-OPERACIONAL.md</code>, crie um job e deixe que <code>reviews-writer</code> determine o próximo gate. A melhor edição não é a que avança mais rápido: é a que mantém cada afirmação verificável até a revisão humana.
