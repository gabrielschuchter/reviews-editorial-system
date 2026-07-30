# Reviews Core sidecar

`reviews-core.exe` é o invólucro de distribuição Windows do núcleo editorial.
Ele não altera a fronteira arquitetural da aplicação: a interface chama a
ponte JSON versionada, que continua delegando regras e persistência ao pacote
`reviews_editorial`.

## Contrato

```json
{
  "desktop_version": "0.1.0",
  "core_version": "0.4.0",
  "bridge_protocol": "1.0.0",
  "registry_schema": "1"
}
```

O comando `version` não inicializa dados. Os comandos `initialize`, `migrate`,
`doctor` e `smoke-test` usam diretórios recebidos por argumentos explícitos.
Todas as respostas públicas são envelopes JSON da ponte.

## Recursos empacotados

O build inclui somente recursos operacionais imutáveis:

- `reviews_editorial`;
- migrações;
- schemas;
- regras editoriais;
- skills;
- scripts operacionais;
- suporte a PDF e DOCX.

O corpus do Drive, bancos, jobs, documentos, tokens, logs e credenciais não são
empacotados. O histórico privado precisa ser importado pelo proprietário.

## Compatibilidade com os scripts das skills

Na primeira execução, o sidecar cria um shim privado `runtime/bin/python.exe`.
Esse arquivo é o próprio sidecar e aceita apenas scripts da allowlist
operacional. Assim, as skills existentes continuam podendo chamar seus
validadores sem instalar Python de sistema nem executar scripts arbitrários.
