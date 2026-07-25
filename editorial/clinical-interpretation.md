---
document_version: "0.1.0"
status: canonical-operational
authority: master-prompt
updated_on: "2026-07-22"
---

# Interpretação clínica

## Cadeia de raciocínio

Use e registre estas categorias sem misturá-las:

| Categoria | Função |
|---|---|
| Dado | Informação ou número diretamente extraído da fonte. |
| Resultado | Comparação ou estimativa produzida pelo estudo. |
| Evidência | Resultado interpretado à luz do desenho, risco de viés, precisão, consistência e demais limitações. |
| Inferência | Conclusão sustentada pela evidência disponível. |
| Hipótese | Explicação possível, ainda não demonstrada. |

Uma hipótese plausível não pode ser redigida como mecanismo comprovado. Uma conclusão dos autores deve ser identificada como tal e reavaliada, não apenas repetida.

## `bottom_line` obrigatório

Antes da redação, registre:

```yaml
bottom_line:
certainty:
main_reason:
main_limitation:
practical_meaning:
```

Cada campo deve derivar do claim ledger e da revisão metodológica. Se a incerteza impedir resposta firme, o `bottom_line` deve dizer claramente o que permanece incerto e por quê.

## Como chegar à conclusão

1. Defina a pergunta clínica, a população e a comparação.
2. Priorize desfechos primários e críticos para a decisão, eventos adversos importantes, resultados secundários que mudem a interpretação e sensibilidades decisivas.
3. Interprete estimativa e intervalo, não apenas o limiar de significância.
4. Separe importância estatística de relevância clínica; ver [methodology/clinical-relevance.md](methodology/clinical-relevance.md).
5. Aplique os limites do desenho e da validade interna antes de usar linguagem causal.
6. Examine precisão, consistência, aplicabilidade e transportabilidade.
7. Identifique se cada ressalva muda a conclusão ou apenas reduz sua segurança.
8. Redija a implicação prática sem extrapolar população, intervenção, comparador, desfecho ou horizonte observados.

## Limites obrigatórios

- `p > 0,05` não demonstra ausência de efeito; ver [methodology/statistical-interpretation.md](methodology/statistical-interpretation.md).
- Mudança intragrupo não demonstra diferença entre grupos.
- Achado exploratório permanece exploratório.
- Mudança em marcador substituto não equivale automaticamente a benefício percebido ou redução de eventos; ver [methodology/surrogate-outcomes.md](methodology/surrogate-outcomes.md).
- Amostra pouco representativa não é falha automática de validade interna; ver [methodology/transportability.md](methodology/transportability.md).
- Recomendação, força da recomendação e certeza da evidência não podem ser inventadas nem inferidas uma da outra.

## Quando pedir mais estudos

Evite a fórmula vazia “mais estudos são necessários”. Quando ela for justificada, identifique a incerteza concreta, a limitação que impede maior segurança e o desenho ou dado capaz de avançar a resposta.
