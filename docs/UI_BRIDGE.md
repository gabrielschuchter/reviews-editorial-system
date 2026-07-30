# Ponte JSON para interfaces locais

`scripts/reviews_ui_bridge.py` é o contrato público, local e versionado entre o
Reviews Editorial System e clientes como o Reviews Desktop. A ponte não cria
servidor, não expõe o SQLite ao cliente e não replica regras editoriais.

## Contrato

Toda resposta usa `schema_version: "1.0.0"` e contém `ok`, `command`, `data`,
`warnings`, `errors` e `meta`. O schema está em
`schemas/ui-bridge-response.schema.json`.

```powershell
python scripts/reviews_ui_bridge.py doctor
python scripts/reviews_ui_bridge.py list-editions
python scripts/reviews_ui_bridge.py inspect-edition `
  --arguments '{"edition_id":"EDITION-ID"}'
```

Erros são retornados em JSON e classificados como `usage_error`,
`editorial_block`, `environment_failure` ou `internal_failure`. Detalhes não
incluem credenciais nem variáveis sensíveis.

## Comandos de leitura

- `doctor`, `workspace-info`, `dashboard`;
- `list-editions`, `inspect-edition`, `list-jobs`, `inspect-job`;
- `list-documents`, `list-versions`, `compare-versions`;
- `list-events`, `list-approvals`, `list-publications`, `list-agent-runs`;
- `list-pending-decisions`, `list-classification-queue`;
- `search-memory`, `list-lessons`;
- `list-drive-imports`, `inspect-drive-import`, `validate-drive-archive`.

## Comandos de escrita delegados

- `create-job`, `validate-job` e `advance-job` compõem os scripts oficiais;
- `correct-classification`, `propose-lesson` e `approve-lesson` usam o serviço
  transacional existente.

O desktop não escreve em `job.yml`, no SQLite, em versões ou em eventos. Ele
também não chama modelos para consultas, validações, diffs, hashes ou
watchers. Papéis continuam sendo gates editoriais auditáveis, não
autenticação.

## Estabilidade

Alterações incompatíveis exigem uma nova `schema_version`. Campos podem ser
adicionados de forma retrocompatível dentro de `data` somente quando o cliente
tolera propriedades desconhecidas. Versões e eventos permanecem imutáveis ou
append-only conforme os triggers do registro.
