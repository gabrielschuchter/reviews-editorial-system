# Handoff para retomada

Atualizado em 25/07/2026. Não houve commit, push, upload ou qualquer escrita no Google Drive.

## Onde continuar

`C:\Users\gabsc\Documents\Codex\2026-07-22\https-drive-google-com-drive-folders\outputs\reviews-editorial-system`

## Estado real

O núcleo local `0.2.0` está implementado e verificável, mas ainda não houve um piloto editorial científico completo pelos vinte estados. Não confundir checks verdes com validação de qualidade de uma edição real.

- inventário-base: 301 registros;
- catálogo incremental `Testes`: 7 referências B próximas do ideal, todas com limitações conhecidas;
- total efetivo carregado: 308 registros;
- corpus A canônico: 0;
- treinamento/recuperação: 6 referências;
- holdout: `07-sii-acg-2021`, excluído da recuperação;
- perfil de estilo: candidato e descritivo, nunca limite automático;
- pasta de produção verificada vazia em 25/07/2026;
- upload/readback no Drive: não executado;
- piloto real e inspeção visual do DOCX: não executados.

Os “finais” da pasta `Testes` são uma fonte crucial de aprendizado, mas não são exemplos perfeitos nem especificação encerrada.

## Verificação inicial

```powershell
$py = 'C:\Users\gabsc\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
Set-Location 'C:\Users\gabsc\Documents\Codex\2026-07-22\https-drive-google-com-drive-folders\outputs\reviews-editorial-system'
& $py -m unittest discover -s tests -v
& $py scripts\run_evals.py
& $py scripts\run_checks.py
```

Último resultado confirmado em 25/07/2026:

- 21/21 testes unitários e de integração local passaram;
- 5/5 evals determinísticos passaram;
- `run_checks.py` passou com 13 schemas, 308 registros efetivos, 7 referências B e 1 holdout.

Substitua esses números pelo resultado da nova execução ao retomar.

## Fontes e decisões preservadas

- ZIPs originais em `D:\drive-download-20260722T201201Z-1-001.zip` e `D:\drive-download-20260722T201133Z-1-001.zip`;
- documentação visual em `D:\documentação design reviews.md`;
- Drive-fonte somente leitura: `1eIfDPteYjjijHv-u9JPMkgfvVSY0fv6f`;
- pasta `Testes`: `1-l8YAR19a9pu63rpysZ8BgqsZ6znzQv1`;
- produção autorizada pretendida: `1q1DoS2nm9JKq-zreLaNk7i5YO1-rqo7s`;
- catálogo curado: `corpus/testes-learning-catalog.yml`;
- perfil candidato: `editorial/style/style-profile-testes-candidate.json`.

`SOURCE_INVENTORY.csv` e os 301 registros embutidos em `corpus/manifest.yml` refletem o snapshot-base de 22/07. O carregador acrescenta o catálogo `Testes`, criado depois desse snapshot, sem fingir que ele fazia parte da captura antiga.

## Próxima execução recomendada

1. Escolher um dos seis pacotes de treinamento com artigo completo e materiais associados; não usar o holdout 07.
2. Criar o job real com `scripts/create_job.py`.
3. Normalizar as fontes e preencher todos os itens de `normalized/manual-document-review.json`.
4. Confirmar a validação documental com um revisor identificado.
5. Executar extração, números, claim ledger e auditorias, mantendo claims qualitativas sob revisão adversarial/humana.
6. Produzir e inspecionar visualmente o DOCX.
7. Somente depois preparar a transferência à pasta de produção autorizada e realizar upload/readback com autorização explícita.

Exemplo:

```powershell
& $py scripts\create_job.py --source 'C:\caminho\artigo-completo.pdf' --topic 'Tema do piloto' --editor 'Nome'
& $py scripts\normalize_documents.py 'jobs\JOB-2026-001'
```

Antes da confirmação, editar `jobs\JOB-2026-001\normalized\manual-document-review.json` e marcar cada `confirmed` como `true` apenas após a checagem real:

```powershell
& $py scripts\validate_job.py 'jobs\JOB-2026-001' --confirm-documents 'Nome do revisor'
```

## Lacunas que continuam reais

1. Nenhum corpus A foi aprovado.
2. A associação integral de todas as edições históricas aos artigos não foi concluída.
3. A auditoria automática não prova suporte semântico de prosa factual qualitativa; claim ledger, mapa de fontes e revisão adversarial continuam obrigatórios.
4. Não há runner de lote; cada edição deve permanecer em job independente.
5. Ainda faltam o piloto científico completo, a inspeção renderizada do DOCX e o teste controlado de upload/readback.

Essas lacunas não impedem continuar o desenvolvimento local, mas impedem declarar o sistema editorial integralmente validado em produção.
