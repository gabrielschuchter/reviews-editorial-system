---
document_version: "0.1.0"
status: operational-from-master-prompt
approval_status: pending-editorial-approval
source_basis: master-prompt
updated_on: "2026-07-22"
---

# Interpretação estatística

## Pacote mínimo de uma estimativa

Registre valor, medida de efeito, comparação, direção favorável, unidade ou escala, denominador, tempo, intervalo de confiança, população de análise e se a estimativa é ajustada ou não ajustada. Confira coerência entre texto, tabela, figura e suplemento.

## Significância e precisão

- `p > 0,05` não demonstra ausência de efeito.
- `p < 0,05` não demonstra importância clínica, ausência de viés nem replicabilidade.
- Interprete estimativa e intervalo pela compatibilidade com benefício relevante, efeito trivial, ausência de efeito e dano.
- Não reduza intervalo de confiança a “inclui” ou “não inclui” o nulo; explique a amplitude e suas consequências.
- Poder planejado não corrige seletividade nem transforma resultado impreciso em evidência de ausência.

## Comparações

- Em desenho comparativo, priorize estimativa entre grupos, interação grupo × tempo, contraste ajustado, diferença de mudanças ou modelo correspondente.
- Mudança significativa dentro de um grupo e não significativa no outro não prova diferença entre grupos.
- Não alterne silenciosamente entre estimativas brutas e ajustadas, populações ou tempos.
- Preserve a direção de escalas: confirme se valores maiores significam melhora ou piora.

## Medidas e derivados

- Não trate odds ratio como risco relativo nem medida relativa como diferença absoluta.
- Em desfechos de tempo até evento, preserve horizonte e pressupostos da medida; não traduza uma razão instantânea diretamente em redução absoluta sem dados adequados.
- Efeitos padronizados precisam de escala e interpretação contextual; não ganham significado clínico apenas por convenção.
- Todo recálculo deve ser marcado como cálculo do sistema, com entradas, fórmula, unidade e verificação.

## Multiplicidade e exploração

Não selecione resultados por significância. Preserve hierarquia analítica, correções e estado exploratório conforme [multiplicity.md](multiplicity.md) e [subgroup-analysis.md](subgroup-analysis.md). A interpretação clínica final segue [clinical-relevance.md](clinical-relevance.md).
