---
document_version: "1.0.0"
status: canonical
approval_status: approved-by-editorial-authority
updated_on: "2026-08-14"
---

# Recomendações de diretrizes sem atribuição institucional

## REV STRUCT HARD 004. Regra

Em edições baseadas em diretrizes, a formulação pública de uma recomendação deve apresentar diretamente a ação, a população, as condições e os qualificadores aplicáveis. A instituição, o documento, o painel ou os autores não devem funcionar como sujeito ou moldura de atribuição da recomendação.

A regra vale para recomendações em tabelas, listas, cards, resumos e no corpo do texto quando o trecho está enunciando a conduta recomendada.

## Formulações bloqueadas

São bloqueadas construções como:

* “A ASPEN recomenda triagem nutricional...”;
* “A ACG sugere...”;
* “Segundo a ESC, recomenda-se...”;
* “De acordo com a APA, deve-se...”;
* “A diretriz recomenda...”;
* “O documento orienta...”;
* “Os autores sugerem...”;
* “O painel recomenda...”;
* “A ASPEN diz que os pacientes devem...”;
* “A recomendação da ASPEN é...”.

O nome da instituição não deve ser substituído por sinônimos de atribuição como “a diretriz”, “o documento”, “o painel” ou “os autores” apenas para contornar a regra.

## Forma preferida

A recomendação deve ser declarada diretamente, preservando a modalidade original:

* “Realizar triagem nutricional na primeira apresentação e regularmente durante o tratamento e a recuperação.”
* “Recomenda-se consulta semanal com nutricionista durante a radioterapia.”
* “Pode ser considerada gastrostomia quando a duração esperada do suporte justificar essa via.”
* “Não adicionar glutamina parenteral até que novas pesquisas confirmem sua segurança.”

A retirada da atribuição nunca autoriza mudar força, certeza, população, condição, exceção, direção ou grau de obrigação da recomendação. Recomendações condicionais continuam condicionais; recomendações negativas continuam negativas.

## Onde a instituição continua permitida

A regra não proíbe identificar a fonte. A instituição pode ser citada quando ela própria é informação relevante, incluindo:

* introdução e contexto da edição;
* identificação e proveniência da diretriz;
* escopo e população do documento;
* metodologia, GRADE, consenso, busca e processo de elaboração;
* comparação entre diretrizes ou versões;
* referências, título, subtítulo e legenda de tabela quando a função é identificar a fonte.

Exemplos permitidos:

* “Publicada em 2026, a diretriz da ASPEN se aplica a adultos em tratamento oncológico.”
* “A ASPEN utilizou GRADE e consenso Delphi na elaboração.”
* “Tabela 1. Recomendações formais da ASPEN para o cuidado nutricional.”

## Auditoria obrigatória

Execute `scripts/audit_guideline_attribution.py` em toda candidata classificada como diretriz. O gate é executado automaticamente pelo pipeline a partir do primeiro rascunho e novamente sobre a versão vigente em cada validação.

O relatório deve pertencer ao hash da versão auditada e apresentar `passed: true`. Qualquer ocorrência é bloqueadora e deve ser corrigida pela reformulação direta da recomendação, sem apagar qualificadores clínicos ou epistêmicos.

## Vigência

A regra foi aprovada explicitamente pela autoridade editorial em 14 de agosto de 2026. Aplica-se a novas edições de diretrizes e a edições reabertas para alteração material após essa data. Versões históricas permanecem preservadas e não são silenciosamente reescritas; quando reutilizadas como exemplar, esta regra canônica mais recente tem precedência.
