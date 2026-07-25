---
name: reviews-source-provenance
description: Validar, normalizar e rastrear fontes do Reviews; construir papéis de fonte, mapas de documentos e claim ledgers. Use para artigos, diretrizes, suplementos, registros, correções, fontes externas e discrepâncias documentais.
---

# Source provenance

Ler `editorial/source-rules.md`, `docs/FACTUAL-SAFETY.md` e `references/contracts.md` antes de alterar artefatos.

1. Inventariar fonte, versão, hash, legibilidade, suplementos, protocolo, registro, errata e duplicatas.
2. Normalizar antes de extrair; PDF e DOCX são superfícies de conferência, não memória factual.
3. Classificar cada fonte por papel e autoridade em `normalized/source-roles.json`; usar `scripts/validate_artifact.py source-roles`.
4. Extrair somente dados localizáveis. Construir claims com excerto, localizador, hash, status e permissão pública.
5. Registrar discrepâncias, ausência de full text e busca não executada. Não resolver conflito silenciosamente.

Bloquear a passagem quando houver fonte trocada, hash divergente, documento essencial ilegível ou direção de efeito incerta.
