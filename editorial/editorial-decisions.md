---
document_version: "0.1.0"
status: canonical-governance
authority: master-prompt
updated_on: "2026-07-22"
---

# Decisões editoriais e aprovação de regras

## Estados permitidos

| Estado | Pode orientar produção? | Significado |
|---|---:|---|
| `pending` | Não | Decisão humana necessária. |
| `candidate` | Somente como hipótese registrada | Padrão observado ou proposta ainda não aprovada. |
| `provisional` | Sim, quando o escopo e a autorização operacional estiverem explícitos | Regra temporária, reversível e identificada como tal. |
| `approved` | Sim | Regra aprovada pelo editor humano para o escopo declarado. |
| `rejected` | Não | Proposta examinada e recusada. |
| `deprecated` | Não em novos trabalhos | Regra anterior mantida apenas para reconstruir versões históricas. |

Frequência no corpus não equivale a qualidade. Publicação anterior não equivale a aprovação atual.

## Registro mínimo de uma regra

Toda regra deve informar:

```yaml
rule_id:
version:
status:
origin:
rationale:
scope:
positive_examples: []
negative_examples: []
proposed_on:
approved_on:
approved_by:
supersedes:
```

Campos desconhecidos permanecem nulos; não devem ser preenchidos por inferência. Mudanças de regra não alteram retroativamente edições antigas, que preservam as versões registradas no job.

## Fluxo de decisão

1. Registrar observação, correção humana ou conflito com sua fonte.
2. Separar correção local de regra potencialmente generalizável.
3. Propor formulação, escopo, exemplos e teste de regressão.
4. Verificar conflito com regras aprovadas e materiais de nível superior.
5. Submeter ao editor humano.
6. Versionar a decisão; só então atualizar perfil, checklist e testes afetados.

## Decisões pendentes conhecidas

| ID | Tema | Estado | Tratamento provisório |
|---|---|---|---|
| `ED-PEND-001` | Título definitivo da Seção I da resposta clínica analítica | `pending` | Manter o título configurável no contrato; não canonizar uma formulação. |
| `ED-PEND-002` | Perfil de estilo derivado do corpus | `candidate` | [style/reviews-style-profile.md](style/reviews-style-profile.md) permanece não aprovado até curadoria e decisão humana. |

Novas pendências devem ser registradas somente quando houver uma alternativa real com impacto editorial amplo; ambiguidades menores usam defaults conservadores documentados.
