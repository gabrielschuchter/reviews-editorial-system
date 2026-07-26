# Contrato do brief editorial

planning/editorial-brief.json valida contra editorial-brief.schema.json. Todos
os campos abaixo são obrigatórios e precisam de decisão específica:

| Campo | Conteúdo aceitável |
| --- | --- |
| edition_type | tipo selecionado ou escolha humana documentada |
| primary_source | source_id/documento central, não uma descrição vaga |
| central_question | pergunta respondível e delimitada |
| reader | leitor e nível de explicação necessários |
| clinical_or_intellectual_decision | decisão real ou função conceitual declarada |
| editorial_angle | tensão sustentada, não adjetivo promocional |
| why_now / what_changed | fato, contexto temporal ou ausência de mudança relevante |
| strongest_supported_takeaway | conclusão limitada a claims liberados |
| most_important_uncertainty | limite que muda a leitura |
| must_include / must_not_claim | arrays de claims, condições e razões |
| context_needed | fonte, função, data e limite de cada contexto |
| numbers_that_need_context | número, unidade, grupo, tempo e comparação requeridos |
| counterevidence_or_disagreement | contraponto e diferença de escopo/método |
| source_incentives_or_conflicts | relevância sem atribuição especulativa |
| omissions_to_avoid | ausência que distorceria a decisão |
| headline_constraints | limites que título e subtítulo devem respeitar |
| lead_strategy / nut_graf / ending_function | funções, não prosa pronta sem fonte |

## Exemplo mínimo estrutural

    {
      "edition_type": "clinical-answer-analytical",
      "primary_source": "DOC-ARTIGO",
      "central_question": "Em adultos X, a intervenção Y comparada a Z altera o desfecho W em 12 meses?",
      "reader": "Profissional que precisa interpretar a estimativa sem extrapolar o contexto.",
      "clinical_or_intellectual_decision": "Usar ou não Y em pacientes semelhantes aos estudados.",
      "editorial_angle": "A estimativa sugere benefício, mas o desfecho de segurança limita a decisão.",
      "why_now": "Novo resultado completo disponível na fonte central.",
      "what_changed": "A análise inclui o desfecho de segurança ausente em relato anterior.",
      "central_tension": "Possível benefício versus incerteza sobre dano.",
      "strongest_supported_takeaway": "A evidência permite discutir Y, sem concluir benefício líquido definitivo.",
      "most_important_uncertainty": "Eventos de segurança são poucos e o intervalo é amplo.",
      "must_include": ["CLM-primary", "CLM-safety"],
      "must_not_claim": ["Y é seguro para todos os pacientes."],
      "context_needed": ["População e seguimento do estudo."],
      "numbers_that_need_context": ["Estimativa primária com grupo, unidade e 12 meses."],
      "counterevidence_or_disagreement": [],
      "source_incentives_or_conflicts": [],
      "omissions_to_avoid": ["O desfecho de segurança."],
      "headline_constraints": ["Não afirmar benefício líquido ou universal."],
      "lead_strategy": "Abrir pela decisão e pela estimativa delimitada.",
      "nut_graf": "Explicar comparação, escopo e incerteza que organiza a análise.",
      "ending_function": "Delimitar qual dado de segurança ainda falta."
    }

Substitua os valores de exemplo por fontes e claims reais; o formato é
ilustrativo, não conteúdo reutilizável.

## Controles de seleção

planning/selection-rationale.md deve manter uma tabela:

| Item | claim_id/fonte | função | inclusão/omissão | razão | modalidade |
| --- | --- | --- | --- | --- | --- |

Uma omissão é aceitável se não muda a decisão, é periférica, redundante ou
exploratória sem impacto; a razão ainda deve ser registrada. Uma inclusão não
é válida apenas porque o resultado é estatisticamente significativo.

## Verificação executável

    python scripts/validate_schema.py <job_dir>/planning/editorial-brief.json --schema editorial-brief
    python scripts/edition_router.py <context.json> --output <job_dir>/planning/edition-routing.json

O schema assegura presença e tipo dos campos; o revisor ainda confere a
correspondência semântica com ledger, appraisal e framing.
