---
name: reviews-strict-style-gate
description: Bloquear qualquer edição do Reviews que contenha antítese, oposição corretiva, contraste concessivo ou traço em texto corrido. Use no primeiro rascunho, depois de toda mudança material, após humanização, antes da coerência, na auditoria final e depois de correções finais.
---

# Gate rígido de estilo do Reviews

## Autoridade

As regras REV STYLE HARD 001 e REV STYLE HARD 002 são políticas editoriais canônicas aprovadas. Elas não são sinais contextuais e não admitem rejeição como falso positivo.

Leia `editorial/style/strict-prohibitions.md` e `editorial/style/prohibited-patterns.yml` antes de executar o gate.

## Regras

### REV STYLE HARD 001

Proibir qualquer antítese ou estrutura equivalente. O escopo inclui oposição adversativa, concessão, negação corretiva, substituição contrastiva e oposição distribuída entre frases consecutivas.

Negativas clínicas diretas podem permanecer quando expressam ausência, contraindicação, proibição, resultado ou recomendação sem preparar uma afirmação alternativa.

### REV STYLE HARD 002

Proibir hífen, meia risca, travessão, sinal de menos e traços equivalentes em texto corrido. A exceção é estreita e limitada a elementos exclusivamente organizacionais ou identificadores técnicos.

## Momentos obrigatórios

Execute o gate:

1. assim que o primeiro rascunho existir;
2. depois de qualquer mudança factual, metodológica, estrutural ou estilística;
3. depois do humanizer;
4. antes da auditoria de coerência;
5. sobre a candidata usada pela auditoria final;
6. depois de qualquer correção final.

## Execução

```powershell
python scripts/audit_strict_style.py --input <artefato> --output <relatorio.json> --artifact-id <id-da-versao>
```

Use `audits/strict-style-audit.json` durante a revisão de estilo e `audits/strict-style-final.json` na auditoria final.

## Gate

Exija `passed: true`. Confirme que `artifact_sha256` corresponde exatamente ao arquivo auditado. Uma ocorrência produz bloqueio crítico e exige reescrita.

A correção deve preservar fatos, números, unidades, referências, direção de efeito, modalidade epistêmica, força de recomendação e certeza da evidência. Reescreva o raciocínio em afirmações diretas.

## Saída

O relatório deve validar contra `schemas/strict-style-report.schema.json` e conter localização, regra, categoria, motivo e ação obrigatória para cada ocorrência.

## Stop conditions

Interrompa o avanço quando:

* o relatório estiver ausente;
* o hash pertencer a outra versão;
* houver qualquer finding;
* o artefato tiver mudado depois da auditoria;
* uma correção introduzir nova antítese ou novo traço.

## Integração

`reviews-edition-writing` deve acionar este gate no primeiro rascunho. `reviews-humanizer-ptbr` deve acioná lo após alterações. `reviews-audit` deve exigir os dois relatórios rígidos. `reviews-document-presentation` não deve receber candidata bloqueada. O pipeline impede o avanço enquanto os relatórios obrigatórios não apresentarem aprovação.
