# Contrato de framing jornalístico

## Log de fontes de contexto

planning/context-source-log.json é uma lista de objetos:

    {
      "context_id": "CTX-01",
      "question_answered": "O que mudou em relação à versão anterior?",
      "source_id": "DOC-DIRETRIZ-2026",
      "source_role": "primary-evidence",
      "date_accessed": "2026-07-25",
      "authority": "fonte oficial da diretriz",
      "claim_ids": ["CLM-change-01"],
      "locator": "Seção 2; tabela 4",
      "limitation": "Não informa impacto clínico da mudança.",
      "inclusion_decision": "incluir no nut graf"
    }

Cada entrada precisa responder uma pergunta editorial concreta. “Contexto
interessante” não é função suficiente.

## Memo de framing

planning/journalistic-framing.md deve conter:

1. pergunta jornalística e leitor/decisão;
2. status de atualidade, fonte, data e o que ele não demonstra;
3. top_line_supported e claims/issue_ids que o sustentam;
4. tensão central e incerteza que a qualifica;
5. contexto, contraponto e conflito/incentivo material;
6. claims excluídos e riscos de distorção;
7. guardrails de título, lead, nut graf e fecho;
8. observação humana do corpus usada, se houver, e seu limite.

planning/framing-memo.json é a versão estruturada validável:

    {
      "central_tension": "benefício possível versus dano impreciso",
      "reader_decision": "discutir uso de Y em pacientes semelhantes",
      "headline_options": ["O que a estimativa permite concluir sobre Y"],
      "selected_angle": "A decisão depende da incerteza de segurança.",
      "counterpoint": "Eventos adversos são poucos e o intervalo é amplo.",
      "evidence_boundary": "O estudo não estabelece benefício líquido definitivo.",
      "must_not_imply": ["segurança universal", "mudança imediata de prática"]
    }

Substitua o conteúdo demonstrativo por claims reais. Execute:

    python scripts/validate_framing.py <job_dir>/planning/framing-memo.json --ledger <job_dir>/extraction/claim-ledger.json --output <job_dir>/planning/framing-validation.json

O schema garante os campos; o vínculo dos títulos a claims exige o ledger
fornecido ao validador.

## Handoff

planning/framing-handoff.md é um contrato para o brief:

    decisão do leitor:
    top line permitido:
    tensão:
    contexto indispensável:
    contraponto obrigatório:
    título/lead proibidos:
    claims permitidos:
    claims bloqueados:
    condição para o fecho:

Ele não contém parágrafo final pronto nem afirmação sem claim.

## Verificação

Antes de entregar, confira manualmente que toda fonte de contexto aparece em
source-roles/source-map, que toda alegação do memo aponta a claim_id/issue_id e
que a frase de atualidade tem fonte e data. Para mudanças em claims, rode os
comandos reais da proveniência:

    python scripts/verify_numbers.py <job_dir>
    python scripts/build_claim_ledger.py <job_dir>

O framing não possui schema/generator próprio; não simule uma validação
automática inexistente.
