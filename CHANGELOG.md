# Changelog

## 0.4.0 - 2026-07-30

- Adiciona registro editorial local integrado aos jobs, com identidades de edição e documento, versões imutáveis, eventos append-only, aprovações e publicação vinculada à versão exata.
- Adiciona taxonomia editorial, classificação corrigível, grafo de linhagem, comparação literal e semântica, memória histórica e memória validada com gates humanos.
- Preserva integralmente execuções de agentes e saídas descartadas sem promovê-las automaticamente.
- Adiciona importação recursiva, idempotente e retomável do Drive, com arquivo privado fora do Git, SHA-256, manifestos e exclusões estritas.
- Adiciona migração em lote de jobs, contratos JSON versionados e validação estrutural integrada aos checks.

## 0.3.0 - 2026-07-25

- Decompõe `reviews-writer` em sete capacidades com a fachada histórica preservada.
- Adiciona contratos e validadores de source roles, brief, findings, inferência e tabelas.
- Documenta pesquisa externa, licenças, migração, arquitetura e estratégia de eval.
- Mantém corpus e documentos humanos imutáveis; não realiza upload ou publicação.

## 0.2.0 - 2026-07-25

- Incorporado o catálogo incremental da pasta `Testes`: sete referências B próximas do ideal, sempre com limitações conhecidas; seis recuperáveis e uma reservada como holdout. A política também foi gravada na Skill `reviews-writer` 0.2.0.
- A Skill passou no validador oficial de estrutura e em um forward test independente que recusou perfeição presumida, excluiu o holdout e bloqueou redação sem guideline validada.
- Criado perfil de estilo candidato a partir das seis referências de treinamento, sem transformá-lo em cânone ou limite automático.
- Alinhados job e claim schemas ao runtime e ampliado o validador local de JSON Schema.
- Endurecidos hashes de origem, colisões de nomes, checklist documental, gates numéricos/factuais e histórico do job.
- Auditorias estatística, metodológica e de coerência agora exigem também gates JSON estruturados; Markdown isolado não libera o estado.
- Adicionado runner de avaliações determinísticas com casos de token de ferramenta, ledger/número sem fonte, limite 12/120, divergência numérica e exclusão do holdout.
- Reforçada a incorporação de feedback: regras gerais exigem regressão estruturada, arquivo existente e casos anteriores aprovados.
- Documentado honestamente que o piloto científico completo, a inspeção visual do DOCX e o upload/readback do Drive continuam pendentes.

## 0.1.0 - 2026-07-22

- Descoberta inicial das fontes locais e do Google Drive.
- Criação da Skill `reviews-writer`, contratos editoriais e arquitetura de jobs.
- Implementação do núcleo determinístico, scripts operacionais e testes-base.
- Registro explícito de decisões editoriais pendentes e limitações da integração com Drive.
