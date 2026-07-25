# Integração com Google Drive

## Estado verificado na descoberta

| Papel | Pasta | Estado conhecido |
|---|---|---|
| Arquivo-fonte | `1eIfDPteYjjijHv-u9JPMkgfvVSY0fv6f` | Biblioteca do Reviews; política obrigatória de somente leitura |
| Produção | `1q1DoS2nm9JKq-zreLaNk7i5YO1-rqo7s` | Vazia nas leituras de 22/07 e 25/07/2026 |

A superfície de ferramentas disponível inclui operações de escrita. Isso não confirma, por si só, propriedade, audiência, herança de compartilhamento ou permissão efetiva em cada item da pasta de produção. Esses detalhes não foram verificados de forma suficiente nesta entrega.

Até essa confirmação, trate a integração como `read + local export + write pending verification`.

## Separação obrigatória

O arquivo-fonte contém edições, artigos e materiais históricos. O sistema pode ler, inventariar e classificar, mas não pode:

- editar conteúdo ou comentários;
- mover, renomear ou reorganizar arquivos;
- sobrescrever versões;
- usar a pasta como destino de candidata;
- alterar compartilhamento.

A produção é o único destino possível para novos outputs, depois da verificação de identidade e permissão. A estrutura abaixo é proposta, não criada automaticamente:

```text
Reviews — Produção/
├── 00 — Sistema editorial
├── 01 — Entrada
├── 02 — Em processamento
├── 03 — Aguardando revisão
├── 04 — Em correção
├── 05 — Aprovadas
├── 06 — Feedback incorporado
└── 07 — Arquivo
```

Não crie essa árvore sem autorização e sem confirmar a pasta-alvo real.

## Implementação atual

`scripts/publish_to_drive.py` tem nome operacional, mas não faz upload. Ele chama `prepare_drive_transfer()` e gera um manifesto com:

- arquivo local e SHA-256;
- pasta de destino;
- pastas-fonte proibidas;
- nome solicitado com job e versão;
- modo de importação;
- proibição de overwrite;
- necessidade de verificação pós-escrita.

O campo `performed` permanece `false` e a operação é `connector-import-required`. O upload só existe depois que o Codex usa o conector e registra o ID/URL realmente retornado.

O manifesto só é preparado quando:

- `job.yml`, o argumento `--job-id` e o nome do diretório concordam;
- o job está em `candidate_for_review`, `human_review` ou `approved`;
- a candidata está fisicamente dentro de `<job>/final/`;
- o destino está na lista explícita `--authorized-production-folder-id`;
- o destino não coincide com nenhuma pasta-fonte declarada.

Exemplo de preparação local, sem upload:

```powershell
python scripts/publish_to_drive.py `
  jobs\JOB-2026-001\final\candidate.docx `
  --job-dir jobs\JOB-2026-001 `
  --job-id JOB-2026-001 `
  --version v01 `
  --destination-folder-id 1q1DoS2nm9JKq-zreLaNk7i5YO1-rqo7s `
  --authorized-production-folder-id 1q1DoS2nm9JKq-zreLaNk7i5YO1-rqo7s `
  --source-archive-folder-id 1eIfDPteYjjijHv-u9JPMkgfvVSY0fv6f
```

## Fluxo seguro de publicação

1. Confirmar que o job chegou a `candidate_for_review` sem erro crítico.
2. Gerar `final/candidate.md`, `final/candidate.docx`, relatório e mapa de fontes.
3. Inspecionar o DOCX renderizado.
4. Confirmar a identidade da pasta de produção pelo ID, não apenas pelo nome.
5. Ler metadados e permissões disponíveis da pasta-alvo.
6. Confirmar quem verá o arquivo criado e se a herança de compartilhamento é aceitável.
7. Gerar `drive-transfer.json`.
8. Importar como arquivo novo; nunca substituir ou atualizar um item histórico.
9. Para DOCX, solicitar conversão para Google Docs quando o conector oferecer esse fluxo.
10. Reler metadados do arquivo criado e registrar ID, URL, parent, MIME type e nome observados.
11. Manter o status `AGUARDANDO REVISÃO EDITORIAL`.

Nome sugerido:

```text
JOB-YYYY-NNN - candidata - vNN
```

O nome não substitui o ID. Não deduza URL ou ID antes do retorno do conector.

## Variáveis locais

`.env.example` reserva:

```dotenv
REVIEWS_PRODUCTION_FOLDER_ID=
REVIEWS_SOURCE_ARCHIVE_FOLDER_ID=
REVIEWS_EDITOR_NAME=
```

Esses valores são configuração, não credenciais. A integração usa o conector do Codex; não armazene tokens, cookies ou chaves do Drive no repositório.

## Fallback local

Se a escrita não estiver efetivamente disponível ou a visibilidade não puder ser confirmada:

1. mantenha a candidata local;
2. exporte `.md` e `.docx`;
3. preserve `drive-transfer.json` com `performed: false`;
4. documente a pasta pretendida e o passo manual de envio;
5. não declare que o documento foi entregue no Drive.

Essa saída local é um resultado válido do MVP; upload não verificado não é.

## Leitura e inventário

Para cada item lido do Drive, registre ID, nome, MIME type, parent/caminho quando disponível, URL observada, datas e escopo da inspeção. Metadados ausentes devem permanecer ausentes, não inferidos.

Arquivos nativos do Google Docs devem ser obtidos pelo método apropriado do conector. PDFs, imagens, ZIPs e arquivos Office são binários não nativos e não devem ser tratados como exportação de Google Docs.

## Movimentação e feedback

Antes de mover um arquivo, leia os parents atuais. Adicione somente o destino confirmado e remova apenas o parent verificado que deve deixar de existir; preserve parents não relacionados. Depois, releia os metadados.

Comentários ou alterações humanas no Google Docs não se transformam automaticamente em regra. Primeiro exporte/obtenha a versão revisada, compare com a candidata, classifique cada mudança e submeta qualquer generalização à aprovação editorial.

## Critério para considerar a integração validada

A integração só pode ser descrita como funcional depois de um teste controlado que:

- crie um arquivo descartável na produção autorizada;
- confirme nome, tipo, parent, proprietário/organização e audiência relevantes;
- releia o arquivo criado;
- confirme que nenhum item do arquivo-fonte foi modificado;
- registre e, se autorizado, arquive/remova o artefato de teste por uma operação recuperável.

Esse teste não foi comprovado por esta documentação.
