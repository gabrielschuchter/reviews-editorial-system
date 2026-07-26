# Exemplos e evals do orquestrador

## Exemplos

### Exemplo 1 — Nova diretriz clínica

**Entrada:** diretriz, suplemento e pedido para orientar decisão em adultos.
**Ação:** crie job, rode preflight full e encaminhe provenance, appraisal, brief,
framing, writing, anti-IA, humanizer, audit e apresentação. **Saída:** plano com
corrente completa e bloqueio se força/certidão não estiverem localizáveis.
**Não aceite:** título ou recomendação antes de source roles.

### Exemplo 2 — Retomada após mudança de suplemento

**Entrada:** candidata já redigida e suplemento substituído. **Ação:** compare
hashes, invalide extração, ledger, appraisal, brief, framing e auditorias
dependentes. **Saída:** handoff para provenance, não correção textual local.
**Critério:** explique por que o rascunho antigo não é mais válido.

### Exemplo 3 — Pedido limitado de auditoria

**Entrada:** candidata, ledger e appraisal válidos; o pedido é somente auditoria.
**Ação:** rode estágio audit, selecione anti-IA e audit conforme plano e não
inicie pesquisa ou reescrita. **Saída:** plano limitado com reports esperados e
status bloqueado se faltar fonte de uma afirmação relevante.

## Casos adversariais

### Caso adversarial 1 — Fonte troca de versão silenciosamente

O arquivo tem mesmo título, mas hash e tabela diferem. Pare, registre source
identity mismatch, retorne a provenance e invalide claims dependentes. Não
reutilize briefing para acelerar produção.

### Caso adversarial 2 — Solicitação para pular o ledger

Prazo apertado não é exceção. Pare antes do draft, registre claim ledger complete
como gate pendente e ofereça somente lista de materiais faltantes.

### Caso adversarial 3 — Linter verde usado como aprovação

O texto não contém sinal heurístico, mas uma recomendação perdeu condição de
população. Encaminhe para audit; ausência de finding anti-IA não autoriza
apresentação nem revisão humana.

## Evals

Os casos em evals/cases.json verificam cadeia completa com artefato de plano,
bloqueio de fonte, escopo limítrofe de auditoria e regressão por troca de hash.
Inspecione selected_capabilities, blocked_reasons, next_action e a ausência de
qualquer estado de publicação.
