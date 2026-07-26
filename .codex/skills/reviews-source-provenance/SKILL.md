---
name: reviews-source-provenance
description: Validar, normalizar e rastrear fontes do Reviews; construir inventário documental, papéis de fonte, source map, extração rastreável e claim ledger. Use para artigos, diretrizes, suplementos, protocolos, registros, erratas, fontes externas e qualquer discrepância documental.
---

# Provenance e extração do Reviews

Use esta skill antes de qualquer interpretação ou redação. O objetivo não é “entender o artigo”; é criar um pacote factual auditável que outra pessoa consiga conferir sem depender da memória do agente.

## Critérios de entrada

Exija um job, fontes identificáveis e uma pergunta editorial. Se houver somente título, abstract ou notícia, registre o limite de full text antes de continuar. Nunca complete lacunas com conhecimento clínico geral.

Leia, nesta ordem:

1. `AGENTS.md`, `editorial/constitution.md` e `editorial/source-rules.md`;
2. `references/contracts.md`;
3. `docs/FACTUAL-SAFETY.md` e o schema correspondente ao artefato que será criado;
4. regras do desenho após a classificação inicial.

## Procedimento

### 1. Isolar e inventariar

- Criar um job por artigo ou pacote independente com `scripts/create_job.py`.
- Registrar origem, versão, URL/identificador, hash, idioma, formato, status de acesso e papel possível.
- Procurar artigo principal, suplemento, apêndice, protocolo, registro, plano de análise, errata, retratação, versão duplicada e revisão humana relacionada.
- Anotar material esperado, ausente, ilegível ou apenas parcialmente acessível em `normalized/missing-materials.md`.

Não aceitar um PDF pelo nome. Confirmar título, autoria, ano, periódico/instituição e correspondência com a pauta.

### 2. Normalizar e conferir

- Executar `scripts/normalize_documents.py <job>`.
- Conferir o inventário, mapa de páginas, tabelas e figuras produzidos.
- Preencher a revisão humana em `normalized/manual-document-review.json`; confirmar cada item somente após conferência real.
- Executar `scripts/validate_job.py <job> --confirm-documents <revisor>`.

PDF e DOCX são superfícies de leitura e conferência. Nunca redigir a partir deles sem artefatos normalizados e localizadores.

### 3. Classificar fontes por papel

Criar `normalized/source-roles.json` e validar com `scripts/validate_artifact.py source-roles`.

| Papel | Pode sustentar |
| --- | --- |
| `primary-evidence` | dados, resultados e métodos |
| `method-authority` | instrumento metodológico, não o resultado do artigo |
| `human-correction` | decisão editorial explícita do texto revisado |
| `editorial-authority` | regra aprovada do Reviews |
| `exemplar-structure`/`exemplar-style` | forma, nunca fato científico |
| `external-scrutiny` | crítica rotulada e verificada |
| `context-only` | contexto, nunca claim principal |

Respeitar a hierarquia de autoridade. Um exemplar ou press release não pode compensar uma fonte primária ausente.

### 4. Extrair sem interpretar

Inicializar com `scripts/extract_evidence.py --initialize <job>`. Para cada item, registrar população, exposição/intervenção, comparador, tempo, desfecho, escala, denominador, análise, perdas e localização.

Para números, conferir valor, sinal, unidade, grupo, denominador, tempo e se a comparação é entre grupos. Cálculo derivado recebe `derived-calculation`, entradas e fórmula; jamais é atribuído aos autores.

Use literalmente:

- `Informação não localizada nos materiais consultados.`
- `Informação ambígua ou insuficientemente descrita no material disponível.`

### 5. Construir e auditar o claim ledger

Cada claim potencialmente público precisa de texto, tipo, documento, localizador, excerto, hash, status e permissão de uso. Executar `scripts/build_claim_ledger.py` e `scripts/verify_numbers.py`.

Bloquear claims sem fonte, com fonte divergente, efeito incerto ou permissão pública falsa. Registrar conflito entre texto, tabela, figura, suplemento e protocolo como discrepância; não escolher uma versão silenciosamente.

## Saídas e gates

Entregar inventário, source roles, extração, verificação numérica e claim ledger antes de liberar appraisal. A saída é válida quando `scripts/validate_job.py` não encontra erro crítico e cada claim usado em prosa está `verified`.

## Caminho degradado

Sem full text, OCR confiável, suplemento ou registro: continuar apenas com o que a fonte permite, rotular a limitação e impedir claims que dependam do material ausente. Não declarar “não encontrado” sem registrar onde e quando foi procurado.
