# Referência de preservação: humanizer PT-BR

## Contrato absoluto

Uma mudança só pode passar se preservar literalmente, quando presentes, fatos, números, unidades, referências, direção de efeito, incerteza, força de recomendação, modalidade, população, condição, exceção e negação. O núcleo compara tokens protegidos antes/depois e usa o claim ledger para reauditar enunciados que os contenham.

O escopo máximo padrão é seis operações e até 15% do texto ou 120 caracteres, o que for mais protetivo para o documento. Operações sobrepostas ou extensas são bloqueadas, não parcialmente aplicadas.

## Pares do corpus incorporados

| ID anonimizado | Sinal humano | Regra local |
| --- | --- | --- |
| `DRV-HDB-HUMAN-01` | “Uma síntese crítica ...” virou subtítulo descritivo | remover autoqualificação, não adicionar promessa |
| `DRV-HDB-HUMAN-02` | título “Avaliação inicial: gravidade antes da etiologia” foi encurtado | separar título de tese quando o corpo sustenta a tese |
| `DRV-HDB-HUMAN-03` | “antiagregantes não aspirina” virou “antiagregantes (exceto aspirina)” | ajustar termo natural apenas quando distinção farmacológica é preservada |
| `DRV-HDB-HUMAN-04` | versões humanas mantiveram recomendações e condições | não fazer compressão clínica automática |

## Exemplos concretos

### Exemplo 1 — autoqualificação confirmada

Antes:

```text
Uma síntese crítica das principais recomendações atualizadas.
```

Decisão: `confirmed`, revisora identificada. Depois:

```text
As principais recomendações atualizadas.
```

Aceitar apenas se o diff registrar uma operação `self-importance-announcement`, `protected_content.preserved=true` e nenhuma alteração além do subtítulo.

### Exemplo 2 — prefixo metadiscursivo antes de claim

Antes:

```text
Vale destacar que a estratégia restritiva usa limiar de 7 g/dL.
```

Depois permitido:

```text
A estratégia restritiva usa limiar de 7 g/dL.
```

Exigir claim ledger porque há número e unidade. O diff deve preservar `7 g/dL` e a reauditoria precisa passar.

### Exemplo 3 — rejeição humana documentada

Uma ocorrência pode estar correta como sinal, mas não caber nesta edição. Com `disposition: rejected`, o resultado mantém o texto original e guarda motivo/revisora. Rejeitar não é falha do fluxo.

## Casos adversariais

### Adversarial 1 — condição clínica

```text
Quando houver instabilidade, a investigação não deve atrasar a ressuscitação.
```

Não remover “Quando” ou “não deve”, mesmo que a frase pareça direta demais. São condição e modalidade protegidas.

### Adversarial 2 — força e certeza

```text
A recomendação é forte, com evidência de baixa qualidade.
```

Não suavizar “forte”, trocar “baixa” por outra palavra ou tratar a combinação como incoerência estilística.

### Adversarial 3 — tabela seletiva

Uma legenda “principais recomendações” pode deixar decisões no corpo por escolha humana. Não completar, desmembrar ou deletar linhas pelo humanizer; encaminhar ao audit/provenance.

## Evals objetivos

`evals/cases.json` contém casos positivo, negativo, limite e regressão do corpus. Os testes exigem: nenhum candidato não confirmado muta texto; mudança confirmada produz diff; conteúdo protegido requer ledger; rejeição humana fica registrável; lote amplo é bloqueado.
