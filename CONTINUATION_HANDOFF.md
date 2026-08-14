# Handoff para retomada

Atualizado em 14/08/2026. Este arquivo substitui os números operacionais congelados em 25/07; resultados de testes, contagens de schemas e estado do CI devem ser obtidos por nova execução, não copiados de checkpoints antigos.

## Estado operacional atual

O Reviews Editorial System é um fluxo local, auditável e orientado a arquivos. `reviews-writer` continua sendo a porta de entrada e coordena as capacidades especializadas. `job.yml` permanece a fonte operacional de estado de cada job; o registro editorial local preserva versões, eventos, linhagem, execuções de agentes, memória histórica e memória validada.

A arquitetura vigente inclui:

- onze skills especializadas;
- normalização documental e confirmação manual antes da extração;
- extração estruturada, verificação numérica e claim ledger antes da redação;
- appraisal, brief e framing antes da candidata pública;
- auditorias factual, estatística, metodológica, estrutural, de estilo, coerência e final;
- aprovação humana como condição necessária para publicação;
- memória histórica separada de memória validada e promoção de aprendizado sujeita a gate humano.

## Regras canônicas adicionadas em agosto

Quatro gates rígidos merecem atenção especial em qualquer retomada:

1. `REV-STYLE-HARD-001`: antítese, oposição corretiva e construções contrastivas proibidas na prosa pública.
2. `REV-STYLE-HARD-002`: traços e hífens proibidos em texto corrido, ressalvadas funções organizacionais e identificadores técnicos documentados.
3. `REV-STRUCT-HARD-003`: introduções de diretrizes devem começar pelo problema clínico, carga, desafios do cuidado e necessidade da orientação; a metodologia fica subordinada à interpretação.
4. `REV-STRUCT-HARD-004`: recomendações de diretrizes devem ser formuladas diretamente, sem usar instituição, diretriz, documento, painel ou autores como sujeito ou moldura de atribuição. Formulações como `A ASPEN recomenda...`, `Segundo a ACG, recomenda-se...` e equivalentes são bloqueadoras. A instituição continua permitida em introdução, proveniência, escopo, metodologia, comparação entre documentos, título, legenda e referências quando sua identificação é informativa.

A remoção de atribuição institucional nunca autoriza mudar força, certeza, modalidade, população, condição, exceção ou direção da recomendação.

## Corpus e memória humana

A pasta `Testes` permanece uma fonte prioritária de aprendizado humano. As sete publicações históricas foram tratadas como referências B próximas do ideal, com limitações conhecidas. A edição `07-sii-acg-2021` permanece reservada como holdout enquanto não houver decisão editorial explícita em contrário.

A edição de prática psicológica baseada em evidências possui histórico humano comparável, revisão final preservada e propostas de aprendizado registradas. Observações derivadas de correções humanas continuam subordinadas à governança: uma preferência local ou um exemplar histórico não prevalece sobre uma regra canônica posterior.

A memória editorial no Google Drive funciona como camada humana legível de decisões, lições, casos e QA. O registro local do sistema continua responsável por identidade, versionamento, eventos, hashes e memória validada. Divergências entre essas camadas devem ser identificadas explicitamente.

## Verificação ao retomar

Execute a suíte atual a partir da raiz do repositório e registre os resultados da execução corrente:

```powershell
python -m unittest discover -s tests -v
python scripts/run_checks.py
python scripts/run_evals.py
python scripts/run_skill_evals.py
python scripts/scan_skills.py
python scripts/run_integration_smoke.py
python scripts/editorial_registry.py validate-registry
```

Para alterações em regras de diretrizes, confirme também as regressões específicas:

```powershell
python -m unittest tests.test_guideline_intro -v
python -m unittest tests.test_guideline_attribution -v
python -m unittest tests.test_strict_style -v
```

Não trate a existência de um workflow ou um PR mergeado como evidência de CI verde. Verifique a execução correspondente ao commit atual.

## Fluxo seguro para uma edição real

1. Confirmar o job e a identidade das fontes.
2. Normalizar os documentos e revisar manualmente paginação, tabelas, figuras e materiais ausentes.
3. Confirmar a validação documental.
4. Extrair evidência e verificar números.
5. Construir o claim ledger.
6. Produzir appraisal, limites de inferência, brief e framing.
7. Redigir a candidata com os contratos do tipo de edição vigente.
8. Executar os gates rígidos aplicáveis à versão exata.
9. Executar auditorias independentes na ordem definida.
10. Gerar e inspecionar o documento final.
11. Manter `AGUARDANDO REVISÃO EDITORIAL` até decisão humana explícita.

## Pontos que não devem ser inferidos a partir deste handoff

- Não declarar que existe corpus A canônico sem uma aprovação nova registrada.
- Não declarar concluído um piloto científico de vinte estados apenas porque uma edição foi revisada no Drive; confirmar o job e a trilha no registro editorial.
- Não declarar concluído upload/readback de produção sem evidência no registro ou no Drive.
- Não assumir que contagens antigas de testes, schemas, registros ou arquivos continuam atuais.
- Não promover observação de corpus, diff humano ou saída de agente a regra canônica sem decisão editorial explícita.

## Fontes operacionais

- Drive da memória editorial: usar como camada humana de leitura e decisão.
- Pasta `Testes`: `1-l8YAR19a9pu63rpysZ8BgqsZ6znzQv1`.
- Catálogo curado: `corpus/testes-learning-catalog.yml`.
- Evidência humana derivada: `corpus/reviews-human-style-evidence.json`.
- Regras canônicas: `editorial/`.
- Operação diária: `README-OPERACIONAL.md`.
- Arquitetura: `docs/ARCHITECTURE.md`.
- Registro e memória: `docs/EDITORIAL_REGISTRY.md`.

O princípio de retomada é conservador: primeiro reconstruir o estado verificável atual, depois continuar. Nenhum checkpoint histórico substitui a execução corrente dos gates.
