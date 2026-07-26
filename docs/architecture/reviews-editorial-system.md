# Reviews Editorial System 0.3

O Reviews é um sistema local, Codex-native, para transformar fontes científicas em candidatas rastreáveis. A fonte científica delimita o que pode ser dito; a camada editorial decide como organizar e comunicar sem ultrapassar esses limites. Não há frontend, API, banco remoto ou publicação automática.

```mermaid
flowchart LR
  S[Fontes imutáveis] --> P[Provenance e claim ledger]
  P --> M[Avaliação científica]
  M --> B[Brief editorial]
  B --> F[Framing jornalístico]
  F --> W[Redação por tipo]
  W --> X[Auditoria anti-IA]
  X --> HZ[Humanização mínima confirmada]
  HZ --> A[Auditorias independentes]
  A --> D[DOCX e renderização]
  D --> H[Revisão humana]
```

`reviews-writer` é a fachada compatível e roteia dez capacidades especializadas:
proveniência, appraisal científico, brief, framing jornalístico, redação,
auditoria de padrões artificiais, humanização mínima confirmada, auditoria
independente, apresentação documental e aprendizado de feedback. Nenhuma delas
promove uma candidata sem decisão humana explícita. A auditoria anti-IA não
atribui autoria, e a humanização só atua sobre ocorrências confirmadas com diff
e reauditoria de claims.
