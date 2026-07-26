---
name: reviews-humanizer-ptbr
description: Aplicar em português brasileiro correções mínimas e reversíveis a ocorrências confirmadas pelo reviews-anti-ai-writing, preservando fatos, números, unidades, referências, direção, modalidade, condições e exceções. Use somente após decisão humana registrada e antes da reauditoria factual/final de uma edição Reviews.
---

# Humanizer PT-BR do Reviews

## Propósito e limite

Transformar um achado já confirmado em uma mudança localizada e auditável. O resultado obrigatório é `humanization-diff`: antes/depois, motivo, revisor, conteúdo protegido, reauditoria de claims e texto revisado em arquivo separado.

Não use esta skill para “deixar o texto mais humano” em massa, trocar palavras por sinônimos, alterar estilo de uma versão humana aprovada, corrigir fatos ou solucionar problema metodológico. Para encontrar sinais, use `reviews-anti-ai-writing`; para fatos, use provenance/appraisal/audit.

## Gatilhos exatos

Acione quando houver “aplique apenas os achados confirmados”, “faça edição mínima”, “gere diff”, “preserve números/referências”, “revisão humana aprovou estas ocorrências” ou quando o anti-AI report contiver decisões humanas por `finding_id`.

Não acione com relatório apenas `candidate`, sem `reviewed_by`, sobre texto sem versão verificável ou se a solicitação for reescrever o documento inteiro. Nesses casos, pare e solicite confirmação ou devolva ao redator.

## Gates e entradas obrigatórias

Exija antes de editar:

1. texto original imutável e hash compatível com o `anti-ai-report`;
2. relatório anti-IA com localização por ocorrência;
3. arquivo de decisões humanas contendo `finding_id`, `status: confirmed` e `reviewed_by`; uma decisão pode declarar `disposition: rejected`;
4. claim ledger se a frase toca número, unidade, referência, direção, modalidade ou condição;
5. limite de operações e de caracteres alterados.

Entradas: draft, anti-AI report, decisões e caminhos de saída. Entrada condicional: claim ledger. Saídas: texto revisado separado e `humanization-diff` validável.

## Hierarquia de fontes

1. Fonte primária/claim ledger são invioláveis para conteúdo factual.
2. Pares candidato→correção humana do Reviews informam mudanças locais e sua confiança, não regra automática.
3. Publicação final humana é preservada por padrão; erros inequívocos exigem a menor correção possível.
4. Anti-AI report define onde olhar, mas não autoriza edição sozinho.

Leia [referência de preservação](references/preservation-guide.md) antes de editar claim, título, tabela ou versão humana aprovada.

## Procedimento operacional

1. Gere ou abra `anti-ai-report.json`; não altere o draft nessa etapa.
2. Registre decisões humanas, por exemplo:

   ```json
   {
     "decisions": [
       {"finding_id": "AAI-001", "status": "confirmed", "reviewed_by": "editora-humana"},
       {"finding_id": "AAI-002", "status": "confirmed", "disposition": "rejected", "reviewed_by": "editora-humana", "reason": "Citação histórica."}
     ]
   }
   ```

3. Execute sem sobrescrever a fonte:

   ```powershell
   python scripts/humanize_ptbr.py --input jobs/JOB-2026-001/drafts/v2-structure.md --anti-ai-report jobs/JOB-2026-001/audits/anti-ai-report.json --decisions jobs/JOB-2026-001/audits/humanizer-decisions.json --ledger jobs/JOB-2026-001/extraction/claim-ledger.json --output jobs/JOB-2026-001/audits/humanization-diff.json --rewritten-output jobs/JOB-2026-001/drafts/draft-humanized.md
   ```

4. Leia integralmente o `unified_diff`. Aceite a mudança somente se ela é menor que o problema e não cria nova prosa promocional, coloquial ou vaga.
5. Verifique `protected_content.preserved` e `claim_reaudit`. Se o ledger falhar, o texto fica inalterado e o resultado é `blocked`.
6. Rode novamente anti-AI, auditoria factual e auditoria final nos trechos afetados. Arquive a decisão, inclusive quando a edição foi rejeitada.

## Transformações permitidas e critérios

O núcleo automatiza somente operações localmente seguras:

- “Uma síntese crítica das ...” → “As ...”; remove autoqualificação.
- “Vale destacar que ...”, “Além disso, ...” ou “Em conclusão, ...” → remove a moldura somente quando a frase continua completa.
- “Seção I. Domínio: tese antecipada” → “Seção I. Domínio”.

Categorias como atribuição vaga, falsa precisão, promoção, recomendação clínica, paralelismo que sustenta contraste ou repetição semântica ambígua retornam `manual-only`. Nunca invente exemplo, aumente certeza, reduza ressalva ou reestruture seção inteira.

## Checagem de edição mínima

- Confirme que o `finding_id` confirmado corresponde exatamente ao hash do draft auditado.
- Compare o before/after sem aceitar mudança fora da unidade textual marcada.
- Verifique a preservação de cada número, unidade, referência e termo modal antes de aceitar o diff.
- Valide o `humanization-diff` contra o schema antes de gravar o arquivo final.
- Bloqueie a alteração se a mesma ocorrência exigir duas transformações diferentes.
- Rejeite a sugestão quando a versão humana aprovada mostrar que a formulação é deliberada.

## Contrato de saída e caminhos

Grave:

- `jobs/<job-id>/audits/humanization-diff.json`, validável por `schemas/humanization-diff.schema.json`;
- `jobs/<job-id>/drafts/<nome>-humanized.md`, sempre distinto do original;
- decisões humanas junto ao diff.

Cada mudança tem `finding_id`, status, before/after, razão, localização, revisor, conteúdo protegido e reauditoria. `completed` exige ao menos uma mudança aplicada; `no-confirmed-findings` não altera o texto; `blocked` nunca grava mutação sem revisão explícita.

## Stop conditions e caminhos degradados

Pare quando a localização divergir do draft, decisão não tiver revisor, a mudança atingir conteúdo protegido sem ledger, operações se sobrepuserem, a alteração exceder orçamento ou a reauditoria falhar.

Sem claim ledger, aplique apenas mudança que não toca nenhum conteúdo protegido; do contrário, devolva bloqueio com motivo. Sem corpus humano, continue com o contrato de preservação, mas não amplie transformações automáticas.

## Proibições

- Não editar ocorrência `candidate` nem inferir confirmação de um pedido genérico.
- Não trocar termos técnicos por sinônimos nem adicionar coloquialismo.
- Não alterar números, unidades, referências, efeitos, negação, força, certeza, condição, exceção ou modalidade.
- Não consolidar vários problemas em uma reescrita integral.
- Não esconder rejeição humana; registre-a no diff.

## Integração com outras skills

`reviews-anti-ai-writing` fornece candidatos; esta skill recebe confirmações e devolve diffs; `reviews-audit` reavalia de forma independente; `reviews-feedback-learning` guarda a hipótese com escopo e regressão. `reviews-writer` mantém a ordem do fluxo.

## Exemplos rápidos

1. Subtítulo confirmado → remover “síntese crítica”, produzir um diff de uma linha.
2. “Vale destacar que” antes de claim com `7 g/dL` → exigir ledger, remover só o prefixo e reauditar o número.
3. Ocorrência confirmada mas `disposition: rejected` → manter texto e registrar rejeição.

Os três exemplos completos e três adversariais estão em [referência de preservação](references/preservation-guide.md). Valide com `python -m unittest discover -s tests -p "test_anti_ai_humanizer.py" -v` e `python scripts/humanize_ptbr.py --help`.
