---
name: reviews-document-presentation
description: Preparar e verificar a apresentação de documentos Reviews sem degradar conteúdo científico, tabelas ou rastreabilidade. Use depois da auditoria textual.
---

# Apresentação documental Reviews

## Objetivo e limites

Esta skill prepara a edição para leitura e distribuição: hierarquia, tabelas, referências, exportação e inspeção visual. Ela não altera fatos, números, recomendações nem a conclusão aprovada. Se o layout exigir cortar conteúdo crítico, devolva para decisão editorial; não esconda a condição em fonte menor.

Entradas: edição auditada, tabelas validadas, referências/localizadores e formato de saída. Saídas: documento pronto para revisão visual, checklist de renderização e lista de problemas de apresentação.

## Montagem

1. Preserve uma hierarquia previsível: título, subtítulo/linha fina, lead, seções, tabelas, notas, referências e metadados. Não use peso tipográfico como substituto de lógica editorial.
2. Mantenha o vínculo entre afirmação e fonte próximo o bastante para ser verificável. Referências longas podem ir ao fim, mas localizadores de recomendações e ressalvas devem permanecer acessíveis.
3. Para tabelas, use cabeçalhos explícitos, largura que comporte qualificadores, repetição de cabeçalho em quebra de página e notas para abreviações. Não compacte uma recomendação a ponto de sumirem população, certeza ou exceções.
4. Controle quebras: não deixe título órfão, linha de recomendação dividida sem cabeçalho, nota separada da tabela ou referências truncadas. Evite widows/orphans quando o formato permitir.
5. Garanta contraste, tamanho legível, ordem semântica de leitura e alternativa textual quando a saída for digital acessível.

## Renderizar e inspecionar

Exporte para o formato de entrega e gere PDF/imagens de páginas quando o ambiente suportar. Inspecione em tamanho real e em viewport estreito se houver versão web. Verifique:

- nenhum texto, número, marcador, link ou referência foi cortado;
- tabelas conservam colunas e não escondem condições em overflow;
- títulos, notas e citações pertencem visualmente ao bloco correto;
- links e âncoras abrem o destino esperado;
- a primeira página comunica tema, população e escopo sem exigir leitura microscópica;
- as páginas finais mantêm referências completas e rastreáveis.

Registre página, elemento, impacto e captura quando houver defeito. Se não for possível renderizar no ambiente, declare a limitação, faça inspeção estrutural do arquivo e marque a revisão visual humana como gate pendente; nunca alegue validação visual por uma checagem de sintaxe.

## Liberação

Libere apenas quando a auditoria textual estiver aprovada, as tabelas passarem no validador e a inspeção visual não tiver problema blocker/major. Depois de qualquer reflow material, mudanças de fonte ou nova exportação, repita a inspeção das páginas afetadas.
