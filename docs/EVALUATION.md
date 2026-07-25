# Avaliação e testes

## Princípio

Qualidade editorial não é uma única nota. O sistema combina invariantes de tolerância zero, testes determinísticos, avaliações semânticas, holdout, regressão e revisão humana. Uma pontuação alta nunca compensa erro factual crítico e nunca autoriza publicação.

## Camadas de verificação

| Camada | O que verifica | Evidência |
|---|---|---|
| Compilação e estrutura | Python válido, arquivos essenciais, schemas | saída de `scripts/run_checks.py` |
| Unidade | Funções de jobs, schemas, normalização, claims, roteador e feedback | relatório de `unittest` |
| Gate do job | Outputs, estado, confirmação documental e erros críticos | saída de `scripts/validate_job.py` |
| Auditoria factual | suporte, números, fontes, direção e referências | artefatos em `audits/` |
| Avaliação editorial | metodologia, estrutura, estilo, coerência e relevância | rubrica e relatório por caso |
| Holdout | generalização, cópia e estabilidade | comparação com casos reservados |
| Regressão | erros reais previamente observados | casos reexecutáveis |
| Visual | renderização de DOCX/Docs, tabelas e legibilidade | inspeção e, quando possível, imagens de referência |

## Comandos mínimos

```powershell
python -m unittest discover -s tests -v
python scripts/run_evals.py
python scripts/run_checks.py
python scripts/validate_job.py <job-dir>
```

Se `python` não apontar para 3.11+, use um interpretador compatível explicitamente. Dependências de documentos são opcionais:

```powershell
python -m pip install -e ".[documents]"
```

Não registre “testes passaram” apenas porque os comandos estão documentados. Preserve comando, data, ambiente, exit code e resumo real.

## O que `run_checks.py` cobre

O verificador agregado atual:

- exige arquivos-raiz e a Skill não vazios;
- exige exatamente 13 schemas;
- valida que os schemas declaram Draft 2020-12 e `$id` único;
- bloqueia `TODO` remanescente no `SKILL.md`;
- compila em memória todos os módulos de `src/` e `scripts/`;
- valida o template de job contra o contrato operacional;
- verifica o catálogo `Testes`, suas limitações, o holdout e a exclusão dele na seleção;
- executa os casos determinísticos de `evals/cases/`.

Ele não executa o pipeline, não valida semanticamente todos os YAMLs, não prova que um DOCX renderiza corretamente e não avalia qualidade científica.

## Rubrica editorial

Pesos iniciais sugeridos:

```yaml
factual_accuracy: 30
methodological_quality: 25
statistical_accuracy: 15
editorial_structure: 10
reviews_style_fidelity: 10
clinical_relevance: 5
coherence_and_naturalness: 5
```

A rubrica precisa conter exemplos e âncoras por nível. Até ser calibrada com corpus A/B e pilotos, esses pesos são provisórios.

## Invariantes de tolerância zero

Uma candidata falha se houver qualquer:

- número sem fonte;
- referência inventada;
- direção de efeito incorreta;
- população, intervenção ou comparador trocados;
- resultado de outro estudo;
- causalidade incompatível com o desenho;
- crítica externa apresentada como fato sem classificação;
- erro crítico pendente.

O gate é binário. Não calcule média ponderada depois de uma falha crítica.

## Suítes editoriais

### Factual e estatística

Casos devem testar população, desenho, amostra, intervenção, comparador, duração, desfecho primário, estimativa, IC, direção, segurança, denominadores, escalas, análise ajustada, intragrupo versus entre grupos, multiplicidade, subgrupos e interpretação de não significância.

### Metodologia

Casos devem distinguir risco de viés, seletividade, substitutos, aplicabilidade, causalidade, certeza, crítica genérica e extrapolação. A resposta esperada precisa indicar não apenas o rótulo, mas a consequência para a conclusão.

### Estrutura

Verifique seções exigidas pelo contrato selecionado, opcionais justificadas, progressão, redundância, posição dos resultados, posição da crítica e bottom line.

### Estilo e anti-IA

Compare com exemplares aprovados e revise naturalidade em português brasileiro, ritmo, títulos, transições, vocabulário e conclusão. O linter heurístico é um sinalizador; detector de IA não é critério de aprovação.

## Holdout e risco de cópia

Casos reservados não entram no contexto de redação. Avalie:

- manutenção do padrão em temas e desenhos diferentes;
- ausência de reprodução de frases características;
- capacidade de explicar incerteza sem fórmula fixa;
- seleção correta de resultados mesmo sem exemplo idêntico;
- estabilidade diante de mudança de ordem dos documentos.

Sem holdout aprovado, não declare fidelidade ao Reviews.

## Regressão a partir de feedback

Todo erro relevante de produção deve gerar:

1. versão mínima reproduzível;
2. classificação do erro;
3. resultado incorreto anterior;
4. comportamento esperado;
5. regra candidata e arquivo-alvo;
6. teste que falha antes da correção;
7. aprovação editorial quando a regra for geral.

`incorporate_feedback.py` valida a proposta e não modifica regras automaticamente.

## Piloto do MVP

Um piloto completo deve usar um artigo e seus materiais associados, passar pelos vinte estados e produzir candidata, mapas, auditorias, DOCX e feedback humano. Compare:

- artigo e suplemento;
- extração e claim ledger;
- edição candidata;
- edição publicada ou referência aprovada;
- correções do editor.

Registre tempo, bloqueios, falsos positivos, lacunas de automação e divergências editoriais. Um único piloto demonstra funcionamento básico, não generalização.

## Relatório de avaliação

Cada execução deve registrar:

```yaml
case_id:
system_version:
corpus_version:
contract_version:
sources_hash:
commands:
automated_results:
critical_failures:
rubric_scores:
human_reviewer:
decision:
follow_up_regressions:
```

Use `pass`, `fail` ou `blocked`; não converta material ausente em nota baixa quando o correto é bloquear.

## Limites atuais

- validação local de JSON Schema cobre apenas o subconjunto implementado;
- a auditoria factual usa correspondência literal e tokens numéricos;
- não há prova de busca externa sem log real;
- métricas de estilo são descritivas e ainda não calibradas;
- exportação DOCX exige inspeção renderizada;
- os casos determinísticos atuais cobrem gates críticos básicos, mas ainda não cobrem semanticamente metodologia, estrutura e qualidade editorial de uma edição completa;
- nenhuma avaliação autoriza publicação sem editor humano.
