---
name: reviews-scientific-appraisal
description: Avaliar desenho, estimativas, validade, certeza, relevância clínica, aplicabilidade e limites de inferência de fontes do Reviews. Use ao analisar ensaios, estudos observacionais, diagnósticos, prognósticos, revisões, metanálises ou diretrizes.
---

# Avaliação científica do Reviews

Use esta skill depois de a extração e o claim ledger existirem. Ela produz julgamento explícito; não uma lista de limitações genéricas.

## Preparar

Ler `editorial/methodology/general-principles.md`, o arquivo do desenho em `editorial/methodology/`, `editorial/clinical-interpretation.md` e `references/judgment-contract.md`. Para diretrizes, ler também `clinical-guidelines.md`; para revisão/meta-análise, `systematic-reviews.md` e `meta-analysis.md`.

## Separar categorias

- **Dado:** informação extraída diretamente.
- **Resultado:** estimativa produzida pelo estudo.
- **Evidência:** resultado interpretado com desenho e limitações.
- **Inferência:** conclusão permitida pela evidência.
- **Hipótese:** explicação plausível, ainda não demonstrada.

Não trocar a categoria apenas suavizando o verbo.

## Fluxo de julgamento

### 1. Formular a pergunta respondível

Registrar população, intervenção/exposição, comparador, desfecho, tempo e estimando. Dizer o que o desenho permite e o que ele não permite. Uma associação observacional não responde sozinha a uma pergunta causal.

### 2. Conferir a estimativa

Para cada resultado prioritário, identificar comparação, escala, direção, intervalo, análise ajustada/não ajustada e população analítica. Diferenciar mudança intragrupo de diferença entre grupos. Um `p > 0,05` não prova ausência de efeito; intervalo compatível com dano e benefício é imprecisão.

### 3. Avaliar validade por resultado

Investigar seleção, confundimento, mensuração, perdas, análise, multiplicidade e seletividade conforme o desenho. Não escrever “amostra pequena”, “unicêntrico” ou “sem cegamento” sem explicar qual resultado é afetado, por que e com qual consequência provável.

### 4. Avaliar significado clínico

Perguntar se o desfecho importa ao paciente, se a magnitude é clinicamente relevante, se há segurança, carga da intervenção e valor aplicável ao contexto. Biomarcador, imagem ou escore não viram benefício clínico automaticamente.

### 5. Delimitar inferência

Para cada limite relevante, registrar:

```text
pergunta | evidência observada | localizador | julgamento | confiança |
resultado/claim afetado | consequência | limitação de cobertura
```

Vincular o julgamento aos IDs de claim. Dizer se reduz confiança, afeta apenas um desfecho ou impede uma inferência.

## Checagens transversais obrigatórias

- Subgrupo: procurar interação, pré-especificação, multiplicidade e replicação; não usar significância dentro do subgrupo.
- Substituto: nomear o marcador e não inferir morbidade, funcionalidade ou qualidade de vida sem validação.
- Causalidade: separar associação, predição, mecanismo, utilidade e implementação.
- Diretriz: separar força, certeza/qualidade, consenso e aplicabilidade local.
- Meta-análise: não recalcular mentalmente; usar ferramenta reproduzível quando o cálculo for necessário.

## Saída

Criar `analysis/methodological-review.json`, `analysis/inference-boundaries.md` e `analysis/critical-issues.md`. Só liberar o plano editorial quando todos os claims principais tiverem limite de inferência explícito.

## Caminho degradado

Quando o instrumento oficial, protocolo ou suplemento não estiver acessível, declarar a cobertura incompleta. Não emitir baixo risco de viés, alta certeza ou “sem crítica relevante” sem material suficiente.
