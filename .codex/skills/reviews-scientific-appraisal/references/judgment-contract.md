# Contrato de julgamento científico

## Ficha por resultado

analysis/methodological-review.json deve conservar uma ficha para cada
resultado prioritário:

    result_id:
    claim_ids:
    question:
    population_and_analysis_set:
    intervention_or_exposure:
    comparator:
    outcome_and_time:
    estimand_and_design:
    estimate_and_interval:
    absolute_effect_or_status:
    outcome_role: primary | critical | secondary | exploratory | undetermined
    clinical_relevance:
    applicability:
    certainty_status:
    inference_boundary:
    linked_issue_ids:
    permitted_modality:

absolute_effect_or_status contém efeito absoluto e método/localizador, quando
disponível, ou a frase de ausência padronizada. certainty_status deve indicar se
é avaliação formal da fonte, avaliação própria documentada ou descrição de
limites sem rótulo formal.

## Issue metodológico individual

Cada arquivo em analysis/methodological-issues/ valida contra
methodological-issue.schema.json. Os campos exigidos significam:

| Campo | Exigência de decisão |
| --- | --- |
| problem | descreve o problema concreto, não “amostra pequena” isolada |
| where_identified | página/tabela/seção ou material externo localizável |
| methodological_importance | por que importa para este resultado |
| possible_consequence | como pode afetar estimativa ou inferência |
| effect_direction | somente quando inferível; use imprevisivel ou nao-inferivel se necessário |
| evidence_strength | potencial, provável ou demonstrada |
| conclusion_impact | distingue reduzir segurança de alterar/inutilizar conclusão |
| related_claim_ids | todos os claims cuja modalidade muda |
| sources/provenance | localizadores e método de busca/conferência |

Exemplo de consequência específica:

    problem: Perdas foram maiores no grupo intervenção e os motivos não são descritos.
    possible_consequence: Se as perdas estiverem ligadas a pior resposta, a estimativa pode superestimar benefício.
    effect_direction: superestima-beneficio
    evidence_strength: potencial
    conclusion_impact: reduz-seguranca

Não substitua “pode” por “demonstrou” sem evidência adicional.

## Fronteiras de inferência

| Categoria de claim | Pode dizer | Não pode dizer sem suporte adicional |
| --- | --- | --- |
| dado | o que a fonte registrou | que isso causa ou beneficia |
| resultado | a comparação/estimativa observada | que se aplica a outros tempos ou populações |
| evidência | resultado considerado com seus limites | certeza não documentada |
| inferência | conclusão proporcional e modalizada | recomendação universal |
| hipótese | explicação possível identificada como tal | mecanismo comprovado |
| crítica externa | alegação e estado de verificação | fato estabelecido |

## Gate de liberação

Não liberar se um resultado prioritário não tiver fonte, comparação, direção,
intervalo ou limite de inferência; se issue crítico estiver aberto; ou se
bottom line conflitar com a modalidade permitida.

## Appraisal consolidado

analysis/scientific-appraisal.json valida contra
schemas/scientific-appraisal.schema.json pelo comando:

    python scripts/validate_scientific_appraisal.py <job_dir>/analysis/scientific-appraisal.json --output <job_dir>/analysis/scientific-appraisal-validation.json

Ele deve conter appraisal_id, job_id, study_id, design, outcome_appraisals,
cross_cutting, human_judgment_required=true e provenance. Cada
outcome_appraisal preserva o resultado, fontes localizáveis, riscos de viés,
certeza, relevância, aplicabilidade e limite de inferência. O validador prova
presença e contrato; não converte uma avaliação automatizada em julgamento
humano.

## Verificação executável

    python scripts/validate_schema.py <issue_file> --schema methodological-issue
    python scripts/verify_numbers.py <job_dir>

O schema verifica estrutura. A correspondência entre issue e fonte ainda exige
revisão de localizadores e excertos.
