---
document_version: "1.0.0"
status: operational
approval_status: approved-by-editorial-authority
corpus_preferences_applied: true
updated_on: "2026-08-06"
---

# Revisão de escrita anti IA

## Proibições que precedem a revisão contextual

Leia primeiro [strict-prohibitions.md](strict-prohibitions.md). Antítese e traços em texto corrido são falhas críticas. Elas bloqueiam a edição e precisam ser removidas antes da análise contextual de outros sinais.

Execute:

```powershell
python scripts/audit_strict_style.py --input <artefato> --output <relatorio> --artifact-id <id>
```

O resultado exigido é `passed: true`. Uma ocorrência de antítese não pode ser aceita como contraste necessário. O conteúdo deve ser reorganizado em afirmações diretas. Um traço só pode permanecer quando tiver função exclusivamente organizacional ou fizer parte de identificador técnico, endereço eletrônico, DOI ou URL.

## Referência e limite de uso

Consulte [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing) como catálogo descritivo de sinais potenciais e fonte de exemplos. A página não funciona como detector, regra universal, prova de autoria ou lista prescritiva de palavras. Seus alertas são contextuais e podem aparecer em escrita humana.

Só aplique ao português brasileiro o que fizer sentido no texto concreto e, quando houver corpus curado, compare o sinal com exemplares aprovados do Reviews. Nenhum detector automático tem autoridade de aprovação. As duas proibições rígidas constituem política editorial explícita e possuem tratamento diferente dos sinais contextuais.

## Ordem da revisão

1. Execute a auditoria rígida e resolva todos os bloqueios.
2. Verifique evidência, hierarquia e função de cada afirmação.
3. Remova pensamento genérico, falsa completude e estrutura sem relação com o conteúdo.
4. Refaça progressão, conclusão e transições.
5. Trate repetições e marcas superficiais.
6. Execute novamente a auditoria rígida depois de qualquer alteração.

Trocar palavras para parecer humano sem corrigir a causa constitui falha de revisão.

## Sinais que exigem leitura contextual

* abertura genérica ou conclusão formulaica;
* títulos e listas em excesso;
* regra de três e paralelismo excessivamente simétrico;
* repetição de “além disso”, “nesse contexto”, “é importante destacar”, “vale ressaltar” ou “de maneira geral”;
* “em suma” e “em conclusão” sem função;
* adjetivo vago, tom promocional, afirmação grandiosa ou metáfora desnecessária;
* transição que só recapitula ou anuncia a estrutura;
* repetição da pergunta antes da resposta;
* lista genérica de limitações, título artificial, comentário editorial vazio ou fragmento de chatbot;
* vocabulário alheio ao português natural ou ao corpus aprovado;
* falso detalhe, referência fabricada ou citação que não sustenta a frase.

Os gatilhos operacionais estão em [prohibited-patterns.yml](prohibited-patterns.yml). Os sinais contextuais geram revisão. As regras REV STYLE HARD 001 e REV STYLE HARD 002 geram bloqueio automático.

## Critério de correção

A frase corrigida deve ganhar fonte, função, hierarquia, precisão ou naturalidade. Se nenhuma dessas dimensões melhora, a alteração é apenas cosmética. Falsos detalhes e referências fabricadas são erros factuais críticos e seguem a [constituição](../constitution.md).
