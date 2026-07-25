# Plano de implementação

## Estado em 25/07/2026

| Fase | Estado | Entregue / próximo gate |
|---|---|---|
| 0 — Descoberta | concluída para arquitetura; acervo histórico parcial | snapshot-base de 301 registros e inspeção aprofundada da pasta `Testes` |
| 1 — Esqueleto | concluída | diretórios, AGENTS, Skill validada, 13 schemas, documentação e scripts |
| 2 — Corpus | operacional, ainda sem cânone A | 7 referências B próximas do ideal com limitações; 6 recuperáveis, 1 holdout; perfil candidato |
| 3 — Pipeline factual | núcleo endurecido | job/schema alinhados, hashes imutáveis, nomes sem colisão, checklist manual, números e claim ledger com gates; falta piloto real |
| 4 — Metodologia | regras implementadas, não pilotadas | aplicar ao primeiro estudo e criar regressões semânticas |
| 5 — Arquitetura editorial | contratos implementados | faltam decisões do modelo preferencial e do título da Seção I |
| 6 — Redação/auditoria | base local verificável | eval runner, linter, gates e DOCX; falta candidata científica real e inspeção visual |
| 7 — Drive | preparação protegida | destino deve ser a produção autorizada; falta upload/readback controlado |
| 8 — Pilotos | não iniciada | escolher pacote não-holdout e executar os vinte estados |
| 9 — Estabilização | parcial técnica | regressões determinísticas iniciadas; depende dos erros do piloto editorial |

## Verificação técnica atual

- 13 schemas carregados;
- template e jobs validados contra o contrato;
- catálogo efetivo com 308 registros;
- 7 referências B com limitações obrigatórias;
- 1 holdout excluído da seleção;
- suíte determinística em `evals/cases/`;
- unit tests em `tests/`;
- nenhuma publicação automática.

## Próxima sequência mínima

1. Executar novamente testes, evals e checks.
2. Selecionar um dos seis pacotes `Testes` não reservados.
3. Criar job e confirmar a checklist documental item a item.
4. Executar extração estruturada, verificação numérica e claim ledger.
5. Fazer auditoria qualitativa adversarial, porque correspondência automática não prova suporte semântico.
6. Planejar, redigir, auditar e gerar DOCX.
7. Inspecionar o DOCX renderizado.
8. Com autorização explícita, testar importação como novo Google Doc e readback na produção.

## Critério de saída do primeiro piloto

Uma candidata só pode existir com todos os outputs dos estados 1–18, zero erro crítico, claim ledger e mapa de fontes completos, DOCX inspecionado visualmente e status `AGUARDANDO REVISÃO EDITORIAL`. A publicação final continua exclusivamente humana.
