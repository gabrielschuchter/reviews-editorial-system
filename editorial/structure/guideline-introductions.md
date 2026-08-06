---
document_version: "1.0.0"
status: canonical
approval_status: approved-by-editorial-authority
updated_on: "2026-08-06"
---

# Introduções de edições baseadas em diretrizes

## Princípio

A introdução apresenta primeiro o problema clínico que torna a diretriz necessária. O leitor deve compreender a doença, a população, a carga epidemiológica ou assistencial, os desafios do cuidado e a função prática da orientação antes de receber informações sobre o processo de elaboração do documento.

## Cobertura obrigatória

Uma introdução de diretriz deve cobrir, quando as fontes permitirem:

1. escopo da doença, condição ou população;
2. epidemiologia, frequência, gravidade ou carga assistencial;
3. desafios clínicos e relação com o tema central da edição;
4. consequências relevantes para prognóstico, função, qualidade de vida, tratamento ou uso de serviços;
5. motivo para existir uma orientação formal e utilidade esperada para o cuidado;
6. escopo da diretriz e particularidades metodológicas que realmente modificam a interpretação.

A ausência de informação contextual na fonte deve ser registrada. O sistema não autoriza preencher lacunas por conhecimento geral sem uma fonte aprovada para contexto.

## Ordem canônica

1. doença e população;
2. carga epidemiológica ou assistencial;
3. desafios clínicos e relação com o tema central;
4. complexidade das decisões e necessidade da diretriz;
5. apresentação breve da diretriz e do ângulo editorial.

## Regra de proporção

Devem existir pelo menos dois parágrafos de contexto clínico antes do primeiro parágrafo dedicado à diretriz ou aos métodos.

Informações sobre bases pesquisadas, período de busca, número de estudos, painéis, consenso e ferramentas metodológicas entram somente quando modificam a leitura das recomendações. Esse conteúdo fica limitado a um parágrafo e a no máximo vinte e cinco por cento das palavras da introdução.

## Antipadrão bloqueador

A introdução é bloqueada quando:

* começa pela descrição burocrática da diretriz;
* dedica aos métodos espaço igual ou superior ao contexto clínico;
* apresenta menos de dois parágrafos de contexto antes da diretriz;
* omite carga epidemiológica ou assistencial disponível nas fontes;
* deixa genérica a relação entre a doença e o tema central;
* apresenta a organização emissora sem demonstrar a necessidade prática da orientação.

## Auditoria obrigatória

Execute `scripts/audit_guideline_intro.py` sobre toda candidata classificada como diretriz. O relatório deve registrar o hash do artefato, a introdução extraída, a cobertura das dimensões obrigatórias, a ordem dos parágrafos, a proporção metodológica e cada finding bloqueador.

A auditoria deve ser repetida após qualquer alteração na introdução e na auditoria final. A edição não pode avançar com relatório ausente, pertencente a outra versão ou com `passed: false`.
