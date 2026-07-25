---
document_version: "0.1.0"
status: provisional-methodology
approval_status: pending-editorial-approval
source_basis: master-prompt
updated_on: "2026-07-22"
---

# Princípios metodológicos gerais

## Unidade de análise

Avalie o **resultado relevante**, não apenas o artigo como um todo. Um mesmo estudo pode sustentar resultados com graus diferentes de validade, precisão e aplicabilidade. Antes da crítica, classifique o desenho e a variante pertinente: paralelo, crossover, fatorial, cluster, superioridade, equivalência, não inferioridade, pragmático ou explicativo, quando aplicável.

## Sequência obrigatória

1. Definir pergunta, população, intervenção ou exposição, comparador, desfecho e tempo.
2. Identificar desenho, fonte do dado e população de análise.
3. Conferir estimativa, intervalo, unidade, escala, denominador e direção.
4. Avaliar validade interna e seletividade do resultado.
5. Avaliar precisão, multiplicidade, consistência e dados ausentes.
6. Separar relevância clínica de significância estatística.
7. Examinar aplicabilidade e transportabilidade sem confundi-las com validade interna.
8. Delimitar inferências permitidas e efeito de cada limitação na conclusão.

Não avance se um elemento crítico estiver ilegível, conflitante ou sem fonte verificável.

## Contrato de crítica específica

Cada problema metodológico registrado deve conter:

```yaml
issue_id:
result_or_claim:
source_location:
problem:
methodological_reason:
possible_consequence:
possible_direction:
consequence_status: potential | probable | demonstrated | indeterminate
effect_on_conclusion: changes | lowers-confidence | no-material-effect | indeterminate
```

Não inclua uma limitação só porque ela aparece em checklist. Diferencie falha de relato, falha demonstrada de condução e informação insuficiente. Ausência de relato nunca vira ausência do método.

## Seleção e interpretação

Priorize desfechos primários, desfechos críticos para a decisão, eventos adversos importantes, resultados secundários que mudem a interpretação e sensibilidades decisivas. Achados exploratórios entram apenas quando relevantes e explicitamente identificados. Significância estatística, tamanho de efeito isolado, destaque dos autores ou facilidade de explicação não bastam para selecionar um resultado.

## Rastreamento

Toda crítica, inferência e cálculo deve se ligar ao claim ledger e às fontes descritas em [../source-rules.md](../source-rules.md). Pesquisa externa registra consulta e data; alegações de terceiros permanecem atribuídas e não se tornam fatos por repetição.

## Módulos específicos

Use a regra correspondente ao desenho ou problema: [ensaios randomizados](randomized-trials.md), [estudos observacionais](observational-studies.md), [revisões sistemáticas](systematic-reviews.md), [metanálise](meta-analysis.md), [diretrizes](clinical-guidelines.md), [subgrupos](subgroup-analysis.md), [multiplicidade](multiplicity.md), [dados ausentes](missing-data.md), [validade interna](internal-validity.md), [transportabilidade](transportability.md), [relevância clínica](clinical-relevance.md), [certeza](certainty-of-evidence.md) e [interpretação estatística](statistical-interpretation.md).
