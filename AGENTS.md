# Instruções do agente (escopo: este diretório e subdiretórios)

## Regras permanentes

- Use `reviews-writer` para orquestrar qualquer trabalho editorial e a skill especializada indicada pelo mapa de capacidades para executar cada etapa.
- Preserve os documentos originais e trate o arquivo histórico do Drive como somente leitura.
- Nunca redija diretamente de PDF ou DOCX: normalize e registre paginação antes de extrair evidências.
- Nunca invente fatos, números, referências, métodos, mecanismos ou conclusões.
- Vincule cada afirmação factual relevante a uma fonte no claim ledger.
- Interrompa o avanço quando houver erro crítico, fonte trocada, direção de efeito incerta ou documento essencial ilegível.
- Execute as auditorias factual, numérica, metodológica, estrutural, de estilo e final na ordem definida.
- Em edições de diretrizes, aplique `REV-STRUCT-HARD-003` à introdução e `REV-STRUCT-HARD-004` às recomendações; nunca formule a recomendação como `A instituição recomenda`, `A diretriz orienta`, `Segundo a instituição...` ou equivalente.
- Não edite o corpus canônico nem promova feedback local a regra geral sem aprovação editorial.
- Não publique nem marque uma edição como aprovada sem autorização humana explícita.
- Registre cada artefato produzido no job; para saídas fora dele, use `scripts/editorial_registry.py register-output` com prompt, contexto, configuração e resultado integrais.
- Não construa frontend, API, autenticação, banco remoto ou serviço em nuvem neste repositório.
- Mantenha regras detalhadas em `editorial/`, `docs/` e na Skill; mantenha este arquivo curto.

## Estrutura principal

- `.codex/skills/reviews-writer/`: orquestração Codex-native e contratos operacionais.
- `editorial/`: regras editoriais, metodologia, estilo, tipos de edição e checklists.
- `corpus/`: metadados e curadoria; não contém cópias silenciosas das fontes.
- `schemas/`: contratos JSON Schema Draft 2020-12.
- `src/reviews_editorial/`: núcleo determinístico compartilhado pelos scripts.
- `scripts/`: comandos operacionais de entrada.
- `jobs/`: um diretório isolado por edição.
- `evals/` e `tests/`: avaliações editoriais e testes automatizados.

## Verificação

- Execute `python -m unittest discover -s tests -v`.
- Execute `python scripts/run_checks.py` para validar contratos, configurações e invariantes editoriais.
- Execute `python scripts/run_evals.py` e `python scripts/scan_skills.py` antes de declarar a arquitetura pronta.
- Execute `python scripts/validate_job.py <job-dir>` antes de avançar um job.
- Execute `python scripts/editorial_registry.py validate-registry` antes de declarar a trilha editorial concluída.
- Use o Python 3.11 ou superior. Dependências de PDF e DOCX são opcionais e devem falhar com instrução explícita quando ausentes.

## Documentação

- Consulte `README-OPERACIONAL.md` para o fluxo diário.
- Consulte `docs/ARCHITECTURE.md` para limites entre componentes.
- Não altere decisões marcadas como pendentes em `EDITORIAL_DECISIONS_PENDING.md` sem registrar aprovação.
