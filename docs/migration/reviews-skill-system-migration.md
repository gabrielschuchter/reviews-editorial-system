# Migração 0.2 → 0.3

| Antes | Problema | Depois | Compatibilidade |
| --- | --- | --- | --- |
| `reviews-writer` monolítico | julgamento e escrita concentrados | roteador para dez skills especializadas | nome e gatilhos preservados |
| regras implícitas | difícil auditar | source roles, brief e findings | artefatos aditivos |
| lint factual/anti-IA | sem lint de inferência/tabela | `assurance.py` e evals | scripts anteriores mantidos |
| 13 schemas | contratos faltantes | 22 schemas | schemas anteriores intactos |

O acréscimo posterior de framing jornalístico, auditoria anti-IA e humanização
confirmada preserva a mesma fachada e torna explícita uma fronteira antes
implícita: diagnosticar padrão artificial não autoriza reescrever texto.

Não houve remoção de corpus, documentos humanos, scripts de pipeline ou pontos de entrada. Skills antigas foram substituídas apenas onde novas responsabilidades têm contrato próprio.
