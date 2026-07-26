# Referência operacional: auditoria anti-IA

## Fontes incorporadas e limite de uso

| Fonte | Uso local | Não usar para |
| --- | --- | --- |
| Revisão humana de sangramento GI baixo, Drive `1r-TewK_9W0s9SSlQ-4pm757uud7LjY5NoRcJNcQJfvU` | pares antes/depois, títulos neutros, poda de metacomentário | transformar redução de texto em meta fixa |
| Registro integral, Drive `1XX6_w41Snt-1WBIDbDNStQA_OJ8nW2HKSNmW-tTt-UE` | regressões de tabela, terminologia e seção redundante | editar sem confirmação humana |
| Manuscrito cru SII, Drive `1z8YzC4WgYVPhKSHhs-o30hMdmeBiSpJaIaGJvSw8LDU` | detecção de nota interna, autoria provisória e contaminação | inferir que todo texto cru é artificial |
| Avoid AI Writing e Blader Humanizer | catálogo de vícios de frase e edição mínima | substituir fatos por estilo |
| Wikipedia: Signs of AI writing | taxonomia de sinais e risco de falso positivo | detector de autoria ou score |

## Taxonomia aplicada

- **Abertura genérica / inflação de relevância / conclusão vazia:** moldura que caberia em qualquer tema, declara que o próprio texto é crucial ou encerra com importância abstrata sem efeito, limite ou condição.
- **Estrutura previsível / subtítulo conclusivo / excesso de headings:** o esqueleto antecipa a tese ou fragmenta leitura contínua.
- **Paralelismo, frase simétrica, enumeração e cadência:** repetir início, tríade retórica, lista ou tamanho pode sinalizar ritmo mecânico, não erro por si só.
- **Transição, metadiscurso e ressalva genérica:** “além disso”, “nesse contexto”, “vale destacar”, “é importante considerar” exigem função lógica concreta.
- **Repetição semântica, reexplicação, sinonímia rotativa:** registrar quando a segunda formulação não acrescenta condição, evidência ou consequência.
- **Promoção, falsa precisão e atribuição vaga:** pedir fonte, medida e limite; não tentar consertar no linter.
- **Tom de chatbot e token de ferramenta:** bloquear publicação.

## Exemplos concretos

### Exemplo 1 — subtítulo autoqualificador

Entrada anonimizada do par humano:

```text
Uma síntese crítica das principais recomendações atualizadas da sociedade clínica.
```

Saída esperada: uma ocorrência `self-importance-announcement`, confiança alta, risco de falso positivo baixo e recomendação “descrever conteúdo e fonte”. Não há reescrita nesta etapa.

### Exemplo 2 — transição repetida

```text
Além disso, a decisão depende do risco.
Além disso, depende da população.
Além disso, depende da aplicabilidade.
```

Saída esperada: três ocorrências `formulaic-transition`, todas com risco de falso positivo alto. A recomendação não é “substituir por sinônimos”; é verificar se a conexão continua clara sem a moldura.

### Exemplo 3 — vazamento de processo

```text
Segundo turn0search0, o resultado foi favorável.
```

Saída esperada: `tool-token-leak`, gravidade crítica, confiança alta, bloqueio de publicação e instrução para inserir referência pública localizável.

## Casos adversariais

### Adversarial 1 — texto humano aprovado com uma transição

```text
A decisão depende da população, da condição e da certeza disponível. Por fim, a aplicação precisa respeitar as exceções da fonte.
```

Não criar `formulaic-transition`: uma ocorrência isolada não prova cadência artificial.

### Adversarial 2 — força e certeza diferentes

```text
A recomendação é forte, embora a certeza da evidência seja muito baixa.
```

Não marcar como contradição, promoção ou precisão falsa. A separação entre força e certeza é metodológica e deve ser encaminhada ao appraisal, não alterada por estilo.

### Adversarial 3 — ressalva que muda conduta

```text
Quando há instabilidade hemodinâmica, a investigação não deve atrasar a ressuscitação.
```

Não remover “quando” nem “não deve”. A frase contém condição e modalidade clínica protegidas.

## Evals objetivos

`evals/cases.json` cobre positivo, negativo, limite e regressão do corpus. Os casos de repositório usam IDs anonimizados `DRV-*` e testam: ocorrência localizada, ausência de alarme por palavra isolada, bloqueio de token interno e preservação de limites humanos.
