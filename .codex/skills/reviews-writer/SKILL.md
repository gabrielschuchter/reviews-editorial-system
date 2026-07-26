---
name: reviews-writer
description: Orquestrar ponta a ponta uma edição Reviews usando skills especializadas, gates e artefatos rastreáveis. Use para iniciar, retomar ou supervisionar um job editorial.
---

# Orquestrador Reviews Writer

## Papel

Esta é a porta de entrada do sistema. Ela mantém o estado do job, escolhe a capacidade especializada e bloqueia avanço sem evidência. Não deve produzir uma peça final sozinha: a execução deve passar por provenance, appraisal, brief, writing, audit, learning e presentation conforme o caso.

## Intake e estado do job

1. Leia `AGENTS.md`, o `job.json` ou o artefato de estado existente e os arquivos de contexto da edição. Nunca comece substituindo um job anterior sem confirmar sua versão.
2. Registre identificador, formato da edição, público, decisão a apoiar, fontes recebidas, responsável humano, prazo e saída esperada. Declare hipóteses de escopo em vez de tratá-las como fatos.
3. Faça inventário dos arquivos, URLs, versões, idiomas e restrições de acesso. Fonte faltante, ilegível ou com versão incerta deve entrar como pendência logo no início.
4. Determine o estado mais alto que já possui artefato válido. Reaproveite apenas quando fontes, brief e rascunho correspondem à mesma versão; mudanças materiais invalidam etapas dependentes.

## Fluxo e gates

| Estado | Skill responsável | Gate para avançar |
| --- | --- | --- |
| `intake` | orquestrador | escopo, fontes e formato registrados |
| `provenance` | reviews-source-provenance | fontes/roles/claim ledger rastreáveis |
| `appraisal` | reviews-scientific-appraisal | achados metodológicos e limites concluídos |
| `brief` | reviews-editorial-brief | tese, público, must/must-not e formato aprovados |
| `draft` | reviews-edition-writing | rascunho e tabelas completos, com claims para auditoria |
| `audit` | reviews-audit | nenhum blocker; majors resolvidos ou aceitos explicitamente |
| `presentation` | reviews-document-presentation | render/inspeção concluídos ou gate humano pendente declarado |
| `learning` | reviews-feedback-learning | feedback classificado, sem mutar corpus humano |

Não pule de intake para draft. Se uma etapa produzir uma lacuna que ela não pode resolver, retorne ao estado de origem e registre o motivo. Um “degraded path” pode gerar briefing ou rascunho marcado como provisório, mas nunca aprovação/publicação automática.

## Roteamento prático

- Texto de diretriz, recomendação ou tabela clínica: comece por provenance e appraise a força/certidão antes do brief.
- Estudo único: extraia PICO/estimando e números antes de escolher ângulo.
- Revisão sistemática: valide elegibilidade, heterogeneidade e distinção entre resultado de síntese e inferência editorial.
- Debate: use fontes representativas e documente consenso, dissenso delimitado e falsos equilíbrios evitados.
- Material já redigido: trate como candidato a auditoria, mas recupere provenance/appraisal se o texto não trouxer rastreabilidade suficiente.

## Operação em lote

Trate cada edição como unidade isolada: diretório/ID próprio, fontes próprias e artefatos versionados. Compartilhe regras e schemas, nunca dados implícitos de outro job. Ao retomar, informe o último artefato válido, os gates pendentes e o próximo responsável; não reexecute etapas aprovadas sem uma razão registrada.

Use validadores como evidência complementar:

```powershell
python scripts/run_checks.py
python scripts/scan_skills.py
python scripts/validate_artifact.py <tipo> <arquivo>
```

## Falhas e escalonamento

Pare e escale para revisão humana quando houver conflito entre fontes autoritativas, ausência de dados necessários para uma conclusão, decisão que muda uma recomendação, risco jurídico/ético, consentimento/privacidade, ou tentativa de apresentar hipótese como resultado. Registre a pergunta concreta, opções, evidência disponível e impacto de adiar.

## Definição de pronto

Uma edição está pronta para publicação somente quando a cadeia de artefatos é rastreável da fonte à peça, os limites científicos sobrevivem ao título e ao lead, o audit report não contém blockers, a apresentação foi verificada e as exceções humanas estão documentadas. Ao encerrar, atualize o estado do job e preserve versões, fontes e relatórios para auditoria futura.
