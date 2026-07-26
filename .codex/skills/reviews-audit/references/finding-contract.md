# Contrato de findings

## Campos mínimos

Cada finding contém id, job_id, modo, categoria, severidade, confiança, status,
trecho auditado, localização, claim_ids afetados, evidência, localizador, issue,
why_it_matters, consequência, recommended_fix, etapa responsável, cobertura e
necessidade de reauditoria. Use status confirmed, suspected ou unresolved; não
use linguagem conclusiva para o que não foi conferido.

## Categorias

Use source_fidelity, numeric_accuracy, methodology, inference, recommendation,
framing, style, table, provenance ou presentation. Uma categoria não dispensa
outra: uma tabela pode ter finding de recommendation e presentation, com efeitos
distintos e claims relacionados.

## Severidade

| Severidade | Definição | Ação |
| --- | --- | --- |
| blocker | muda verdade, segurança ou sentido material | bloquear e devolver |
| major | perde nuance clínica, população ou certeza | corrigir ou aceitar explicitamente |
| minor | melhora clareza sem alterar significado | corrigir quando possível |
| note | documenta risco ou falso positivo | manter rastreabilidade |

## Cobertura

Declare elementos cobertos, não cobertos e razão. Cobertura factual não equivale
a cobertura metodológica, visual ou anti-IA. Quando uma fonte faltar, indique
qual claim fica sem conclusão e qual material permitiria completar a leitura.

## Separação de papéis

O auditor descreve a correção e destino; quem redigiu ou humanizou aplica a
mudança. Reaudite versão nova contra o mesmo finding e suas dependências. Não
sobrescreva finding antigo nem mude sua severidade sem nova evidência.
