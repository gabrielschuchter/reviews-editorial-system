# Google Drive

## Espaços separados

- **Arquivo-fonte:** pasta `Reviews` (`1eIfDPteYjjijHv-u9JPMkgfvVSY0fv6f`), somente leitura por política editorial.
- **Produção autorizada:** pasta `reviews-editorial-system` (`1q1DoS2nm9JKq-zreLaNk7i5YO1-rqo7s`), vazia nas leituras de 22/07 e 25/07/2026.

O conector dispõe de leitura, criação de pasta, upload, importação DOCX para Google Docs e atualização. A descoberta não confirmou propriedade, visibilidade pública ou ACL detalhada; não inferir essas permissões.

## Leitura

Inventariar metadados e buscar somente itens necessários. Para Google Docs nativos, exportar ou baixar conforme o MIME. Para PDF, imagem, ZIP e Office não nativos, usar download/fetch bruto, não exportação de Google Workspace.

## Escrita

1. Validar candidata e destino.
2. Gerar DOCX e concluir renderização visual.
3. Preparar `drive-transfer.json` com job, candidata dentro de `<job>/final/`, destino e lista explícita de IDs de produção autorizados.
4. Importar como novo Google Doc na pasta de produção; nunca sobrescrever.
5. Se necessário, mover o novo arquivo adicionando a pasta de produção e removendo apenas o pai verificado.
6. Reler metadados e registrar ID, URL e horário realmente retornados.

Não alterar nomes, pais, comentários ou conteúdo do arquivo-fonte. Não sintetizar URLs.
