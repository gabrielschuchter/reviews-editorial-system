# Segurança factual

## Regra central

Fluidez nunca justifica invenção. População, método, números, resultados, intervalos, mecanismos, referências, financiamento, limitações, recomendações e conclusões só entram quando há suporte identificável.

Quando a informação não existe ou não pode ser localizada, use exatamente:

> Informação não localizada nos materiais consultados.

Quando a descrição é ambígua:

> Informação ambígua ou insuficientemente descrita no material disponível.

Conflitos entre texto, tabela, figura, suplemento, protocolo ou registro devem gerar uma discrepância; não se escolhe silenciosamente a versão mais conveniente.

## Cadeia de proveniência

```text
arquivo original + hash
  -> texto normalizado + mapas
  -> extração estruturada
  -> conferência numérica
  -> claim ledger
  -> draft
  -> auditoria adversarial
  -> source-map da candidata
```

O original permanece imutável. Cada transformação registra sua origem. Um localizador precisa usar página, tabela, figura, seção ou, em DOCX sem paginação confiável, índice de parágrafo/renderização verificável.

## Normalização e seus limites

- PDF usa `pypdf` quando o extra `documents` está instalado. Página sem texto é marcada para inspeção visual; não há OCR automático.
- A extração de PDF não reconhece tabelas ou figuras de forma confiável.
- DOCX é lido diretamente do pacote XML e preserva parágrafos, tabelas, mídia e quebras explícitas.
- Paginação de DOCX não é confiável sem renderização. O sistema não inventa números de página.
- HTML recebe remoção simples de tags, inadequada para layouts complexos sem revisão.
- Um arquivo “normalizado” ainda exige confirmação manual de completude, versão e legibilidade.

`document-validation.json` começa como `requires_manual_review`; apenas `confirm_document_validation()` pode marcá-lo como `passed`, desde que não existam falhas críticas automáticas.

## Categorias conceituais

Mantenha estas categorias separadas:

| Categoria | Definição operacional |
|---|---|
| Dado | Informação extraída diretamente |
| Resultado | Comparação ou estimativa produzida pelo estudo |
| Evidência | Resultado interpretado à luz do desenho e das limitações |
| Inferência | Conclusão sustentada pela evidência |
| Hipótese | Explicação possível, não demonstrada |

O `claim_type` implementado usa `direct-fact`, `result`, `derived-calculation`, `interpretation`, `inference`, `hypothesis`, `external-criticism` e `missing-information`.

## Claim ledger

Cada claim potencial registra texto, tipo, documento, localizador, excerto, status, permissão de uso público e notas. Status aceitos:

- `verified`;
- `partially-verified`;
- `unsupported`;
- `ambiguous`;
- `divergent`;
- `extrapolative`;
- `pending`.

Um claim público factual precisa estar integralmente `verified` e conter documento, excerto e ao menos um localizador. Claims parcialmente verificadas, ambíguas, divergentes, extrapolativas, pendentes ou sem suporte não podem entrar no draft público. Número público sem fonte é erro crítico. Cálculo derivado precisa registrar o método e ser apresentado como cálculo do sistema.

`build_claim_ledger.py` valida esse contrato e produz `extraction/claim-ledger.json`. Isso não prova que o excerto sustenta semanticamente o texto; essa correspondência ainda exige auditoria humana/adversarial.

## Verificação numérica

Cada registro numérico deve conter valor relatado, documento, localizador, unidade, direção e status de conferência. Verifique também:

- denominador e população de análise;
- escala e sentido de melhora/piora;
- tempo de seguimento;
- medida absoluta e relativa;
- análise ajustada ou não ajustada;
- contraste entre grupos, não apenas mudança intragrupo;
- intervalo de confiança e compatibilidade com benefício/dano;
- multiplicidade, subgrupos e interação;
- divergências entre texto, tabela e figura.

Ausência de significância não demonstra ausência de efeito. Resultado intragrupo não demonstra diferença entre intervenções. Desfecho substituto não equivale automaticamente a benefício clínico. Resultados exploratórios permanecem identificados como exploratórios.

## Auditoria do draft

`audit_draft_text()` realiza duas verificações mecânicas:

1. impede que o texto exato de um claim não autorizado apareça no draft;
2. procura tokens numéricos do draft que não aparecem no conjunto de claims públicos.

Limites importantes:

- a comparação de claims é literal e não detecta paráfrases sem suporte;
- a expressão regular de números pode tratar datas, números de seção ou anos como valores e pode não reconhecer todas as notações científicas;
- presença do mesmo token no ledger não comprova que ele está ligado à frase correta;
- referências fabricadas, causalidade indevida e direção do efeito exigem revisão semântica;
- auditorias Markdown não bloqueiam a máquina de estados se o erro não for também registrado em JSON ou nos gates do job.

O linter reduz risco, mas não substitui auditoria factual adversarial linha por linha.

## Crítica metodológica segura

Cada crítica relevante responde:

1. qual é o problema;
2. onde aparece;
3. por que importa;
4. qual consequência pode produzir;
5. em que direção, quando inferível;
6. se a consequência é potencial, provável ou demonstrada;
7. se muda a conclusão ou apenas reduz sua segurança.

Ausência de relato não é ausência do método. Restrição de amostra não é automaticamente defeito de validade interna; aplicabilidade e transportabilidade exigem um modificador de efeito plausível e uma população-alvo identificada.

## Escrutínio externo

Registre busca e data para protocolo, registro, plano de análise, errata, retratação, expressão de preocupação, cartas e críticas. Classifique qualquer crítica externa como:

- documentada;
- preocupação plausível;
- alegação não confirmada;
- problema reconhecido pelos autores;
- discrepância verificada.

Comentário externo nunca substitui a conferência na fonte primária.

## Condições de interrupção

Bloqueie a redação final se houver somente resumo quando o artigo completo é necessário, PDF incompleto, tabela principal ilegível, desfecho primário indefinido, mistura de estudos, intervenção/comparador incertos, discrepância crítica, direção de efeito incerta, guideline sem versão confirmada, retratação não tratada ou risco de fonte trocada.

Registre o bloqueio em `analysis/critical-issues.md` e também em um gate estruturado quando precisar impedir avanço automático.

## Critérios de saída

Uma candidata exige zero:

- número sem fonte;
- referência inventada;
- direção de efeito incorreta;
- população, intervenção ou comparador trocados;
- resultado pertencente a outro estudo;
- causalidade incompatível com o desenho;
- crítica externa apresentada como fato sem classificação;
- erro crítico pendente.

Mesmo com zero erros detectados, o status permanece `AGUARDANDO REVISÃO EDITORIAL`.
