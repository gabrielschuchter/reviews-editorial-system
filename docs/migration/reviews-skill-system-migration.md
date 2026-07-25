# Migração 0.2 → 0.3

| Antes | Problema | Depois | Compatibilidade |
| --- | --- | --- | --- |
| `reviews-writer` monolítico | julgamento e escrita concentrados | roteador para sete skills | nome e gatilhos preservados |
| regras implícitas | difícil auditar | source roles, brief e findings | artefatos aditivos |
| lint factual/anti-IA | sem lint de inferência/tabela | `assurance.py` e evals | scripts anteriores mantidos |
| 13 schemas | contratos faltantes | 17 schemas | schemas anteriores intactos |

Não houve remoção de corpus, documentos humanos, scripts de pipeline ou pontos de entrada. Skills antigas foram substituídas apenas onde novas responsabilidades têm contrato próprio.
