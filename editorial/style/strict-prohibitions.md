---
document_version: "1.0.1"
status: canonical
approval_status: approved-by-editorial-authority
updated_on: "2026-08-06"
---

# Proibições rígidas de estilo

Estas regras valem para toda edição do Reviews, em qualquer tipo, etapa ou formato. São regras bloqueadoras. A publicação fica impedida enquanto houver uma ocorrência.

## REV STYLE HARD 001. Antítese proibida

É proibido construir uma ideia por oposição retórica, negação corretiva ou substituição contrastiva.

O bloqueio inclui:

* “não é X, mas Y”;
* “não é X, e sim Y”;
* “não apenas X, mas também Y”;
* negação seguida de reformulação positiva, inclusive entre frases consecutivas;
* conectores adversativos ou contrastivos, como “mas”, “porém”, “contudo”, “entretanto”, “todavia”, “no entanto”, “ainda assim”, “por outro lado”, “ao contrário”, “em contrapartida”, “em vez de” e “em lugar de”;
* construções concessivas, como “embora”, “apesar de”, “ainda que”, “mesmo que”, “mesmo sem” e equivalentes;
* fórmulas como “não se resume”, “não se limita”, “não equivale”, “não implica”, “não significa”, “não representa”, “não constitui”, “não funciona como”, “não substitui”, “não autoriza”, “não sustenta”, “não demonstra”, “não oferece”, “não ocupa”, “não serve”, “não basta”, “não garante”, “não depende”, “não decide”, “não resolve” e “não exige” quando usadas para preparar uma afirmação alternativa.

Negativas clínicas diretas continuam permitidas quando expressam ausência, contraindicação, proibição, resultado ou recomendação sem construir oposição. Exemplos: “Não adicionar glutamina parenteral” e “Não foram encontrados estudos elegíveis”.

A correção deve declarar cada informação diretamente. Duas ideias em tensão podem permanecer no texto em frases independentes, sem moldura adversativa, concessiva ou corretiva.

## REV STYLE HARD 002. Traços e hífens proibidos no texto

São proibidos em texto corrido:

* hífen ASCII;
* meia risca;
* travessão;
* sinal de menos usado como recurso tipográfico;
* qualquer traço equivalente.

Faixas devem ser escritas por extenso, como “de quatro a seis semanas”. Compostos devem ser reformulados quando exigirem hífen. Incisos devem usar vírgula, ponto, dois pontos ou nova frase.

A exceção é restrita a elementos organizacionais. Um traço pode permanecer em título, cabeçalho, separador ou estrutura técnica quando sua função for exclusivamente organizacional e a decisão editorial justificar seu uso. Identificadores técnicos, endereços eletrônicos, DOI e URLs não contam como prosa editorial.

## Auditoria obrigatória

Execute `scripts/audit_strict_style.py`:

1. no primeiro rascunho;
2. depois de cada alteração material de conteúdo, estrutura ou estilo;
3. depois de humanização;
4. antes da auditoria de coerência;
5. na auditoria final;
6. depois de qualquer correção final.

Cada execução deve usar a versão exata do artefato e registrar seu hash. O relatório deve apresentar `passed: true`. Uma ocorrência não pode ser rejeitada como falso positivo. A única exceção possível é a classificação documentada de um traço como elemento exclusivamente organizacional.

## Regressão automatizada

O workflow `.github/workflows/strict-editorial-style.yml` executa os testes específicos e os checks estruturais do repositório em cada push para `main` e em cada pull request. Novos padrões devem ser acompanhados por teste de regressão.

## Gate de publicação

A edição não pode avançar para revisão humana ou publicação se qualquer relatório rígido estiver ausente, pertencer a outra versão ou apresentar `passed: false`.
