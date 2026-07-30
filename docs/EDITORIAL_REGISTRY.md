# Registro editorial, memória e importação local

O registro editorial é uma camada local e determinística sobre a arquitetura de jobs. Ele não cria uma aplicação paralela: `job.yml` continua sendo a fonte operacional do estado de cada job, enquanto o SQLite em `.reviews/editorial-registry.sqlite3` funciona como índice transacional, trilha append-only e catálogo de entidades.

Papéis editoriais são gates auditáveis de fluxo e aprovação. Eles não são autenticação, autorização de sistema operacional nem segurança real.

## Entidades e invariantes

- uma edição agrega documentos, mas documento e edição mantêm identidades independentes;
- um documento possui versões numeradas; versões existentes não aceitam `UPDATE` nem `DELETE`;
- restaurar uma versão cria uma versão nova, ligada por `restored_from_version_id`;
- eventos editoriais não aceitam `UPDATE` nem `DELETE`;
- publicação registra a versão e a aprovação exatas;
- todo resultado de agente pode preservar prompt, contexto, configuração, resultado integral, documento e versão;
- memória histórica é automática e não normativa;
- memória validada exige gate humano e origem aprovada;
- lições permanecem propostas até aprovação, e não podem ser validadas a partir de rascunhos;
- classificações automáticas são sugestões com evidência, confiança e alternativas; uma correção humana gera evento e não apaga a sugestão.

Os contratos públicos do registro estão em `schemas/edition-record.schema.json`, `document-version.schema.json`, `editorial-event.schema.json`, `memory-item.schema.json` e `drive-import-manifest.schema.json`. As migrações versionadas estão em `migrations/`.

## Comandos

```powershell
python scripts/editorial_registry.py init
python scripts/editorial_registry.py dashboard
python scripts/editorial_registry.py edition EDITION-ID
python scripts/editorial_registry.py sync-job jobs\JOB-ID
python scripts/editorial_registry.py sync-all-jobs jobs
python scripts/editorial_registry.py search-memory "termo" --tier validated
python scripts/editorial_registry.py compare VERSION-A VERSION-B
python scripts/editorial_registry.py restore VERSION-ID --reason "Justificativa"
python scripts/editorial_registry.py approve-version VERSION-ID --rationale "Revisão concluída"
python scripts/editorial_registry.py publish-version VERSION-ID --rationale "Publicação autorizada"
python scripts/editorial_registry.py validate-registry
```

`create_job`, os avanços do pipeline, a confirmação documental e os registros de revisão sincronizam o job no registro automaticamente. `sync-all-jobs` migra jobs legados e pode ser executado novamente sem duplicar versões iguais.

## Registro de saídas de agentes

Use `register-output` para preservar uma execução fora dos produtores já integrados:

```powershell
python scripts/editorial_registry.py register-output `
  --edition-id EDITION-ID `
  --agent-name reviews-writer `
  --purpose "Produzir candidata" `
  --prompt-file prompt.txt `
  --context-file context.json `
  --result-file resultado.md `
  --output-type editorial-draft `
  --document-title "Candidata"
```

Resultados descartados continuam históricos quando `--discarded` é usado. Isso registra o que aconteceu sem promovê-lo como exemplo bom.

## Arquivo privado do Drive

O snapshot versionado contém IDs, URLs, caminhos, MIME types, datas, hashes da captura, classificações e relações. Os binários e exports reais ficam em um diretório privado fora do Git, definido por `--storage` ou `REVIEWS_PRIVATE_ARCHIVE_ROOT`.

```powershell
python scripts/editorial_registry.py `
  --storage "C:\arquivo-privado\reviews" `
  import-drive corpus\drive-source-snapshot-AAAAMMDD.json
```

A importação:

1. valida a política de exclusão antes de baixar qualquer conteúdo;
2. rejeita snapshots que contenham descendentes de `POPs` ou `Diretrizes/Estatutos`;
3. preserva diretrizes permitidas fora dessas árvores;
4. exporta documentos nativos do Google para formatos locais duráveis;
5. calcula SHA-256 e registra o caminho físico privado;
6. associa uma mesma versão física a todas as origens do Drive que compartilhem os bytes;
7. grava um manifesto verificável por execução;
8. aceita retomada por job parcial e reexecução idempotente.

O snapshot pode incluir `revisions` e `comments`. Quando o conector não os fornece, o manifesto registra essa limitação; a ausência nunca é apresentada como histórico recuperado.

Capturas privadas posteriores de histórico podem ser ingeridas sem reimportar os arquivos:

```powershell
python scripts/editorial_registry.py `
  --storage "C:\arquivo-privado\reviews" `
  import-drive-history "C:\arquivo-privado\history"
```

O comando é idempotente por `(fonte, ID da revisão)` e `(fonte, ID do comentário)`. O Git recebe apenas o manifesto e os hashes dos fragmentos; conteúdo de comentários e snapshots detalhados permanecem no arquivo privado.

## Validação

`validate-registry` confere migrações, triggers de imutabilidade, chaves estrangeiras, cadeias de versão, publicações exatas, fontes da memória validada, existência e hash das cópias privadas. Para o arquivo do Drive, acrescente `--require-external-storage`.

```powershell
python scripts/editorial_registry.py `
  --storage "C:\arquivo-privado\reviews" `
  validate-registry --require-external-storage
```

`scripts/run_checks.py` cria uma trajetória editorial completa em armazenamento temporário e executa a mesma validação como parte dos checks gerais.
