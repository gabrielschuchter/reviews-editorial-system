---
document_version: "0.1.0"
status: provisional
approval_status: pending-editorial-approval
corpus_preferences_applied: false
updated_on: "2026-07-22"
---

# Revisão de escrita anti-IA

## Referência e limite de uso

Consulte [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) como catálogo descritivo de sinais potenciais e fonte de exemplos. A página **não é detector, regra universal, prova de autoria nem lista prescritiva de palavras proibidas**. Seus próprios alertas dizem que os sinais são observações contextuais e podem aparecer em escrita humana.

Só aplique ao português brasileiro o que fizer sentido no texto concreto e, quando houver corpus curado, compare o sinal com exemplares aprovados do Reviews. Nenhum detector automático tem autoridade de aprovação.

## Ordem da revisão

1. Verifique evidência, hierarquia e função de cada afirmação.
2. Remova pensamento genérico, falsa completude e estrutura sem relação com o conteúdo.
3. Refaça progressão, conclusão e transições.
4. Só então trate repetições e marcas superficiais.

Trocar palavras para “parecer humano” sem corrigir a causa é uma falha de revisão.

## Sinais que exigem leitura contextual

- abertura genérica ou conclusão formulaica;
- títulos e listas em excesso;
- regra de três e paralelismo excessivamente simétrico;
- construções repetidas como “não apenas X, mas também Y”;
- repetição de “além disso”, “nesse contexto”, “é importante destacar”, “vale ressaltar” ou “de maneira geral”;
- “em suma” e “em conclusão” sem função;
- adjetivo vago, tom promocional, afirmação grandiosa ou metáfora desnecessária;
- transição que só recapitula ou anuncia a estrutura;
- negação artificial, travessões em excesso ou repetição da pergunta antes da resposta;
- lista genérica de limitações, título artificial, comentário editorial vazio ou fragmento de chatbot;
- vocabulário alheio ao português natural ou ao corpus aprovado;
- falso detalhe, referência fabricada ou citação que não sustenta a frase.

Os gatilhos operacionais estão em [prohibited-patterns.yml](prohibited-patterns.yml). Eles geram revisão, não veredicto automático.

## Critério de correção

A frase corrigida deve ganhar fonte, função, hierarquia, precisão ou naturalidade. Se nenhuma dessas dimensões melhora, a alteração é apenas cosmética. Falsos detalhes e referências fabricadas são erros factuais críticos e seguem a [constituição](../constitution.md), não apenas esta revisão de estilo.
