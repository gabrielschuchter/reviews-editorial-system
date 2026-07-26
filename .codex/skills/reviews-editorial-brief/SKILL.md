---
name: reviews-editorial-brief
description: Definir ângulo, contexto, informação decisiva, título, lead e estrutura de uma edição do Reviews antes da redação. Use após a evidência estar extraída e avaliada, antes de redigir, reorganizar ou escolher o framing de uma candidata.
---

# Brief editorial do Reviews

O brief converte um pacote científico válido em uma decisão editorial rastreável. Ele organiza a leitura; não amplia a evidência.

## Pré-requisitos

Exigir claim ledger validado, limites de inferência, tipo de edição e seleção inicial de resultados. Ler `editorial/audience.md`, o contrato em `editorial/edition-types/`, `editorial/style/titles-and-subtitles.md` e `references/brief-contract.md`.

## Construir o brief

Criar `planning/editorial-brief.yaml` com todos os campos exigidos e validar via `scripts/validate_artifact.py editorial-brief`.

### Pergunta e decisão

Definir quem lê, qual decisão clínica ou intelectual está em jogo e qual pergunta pode ser respondida pelas fontes. Se não houver decisão, declarar a função conceitual da edição em vez de inventar aplicabilidade prática.

### Ângulo e novidade

Responder: por que isso importa agora, o que mudou, qual tensão real existe e qual takeaway é mais forte sem ocultar a incerteza principal. “Novo” não significa “mudança de paradigma”.

### Seleção e omissão

Listar o que precisa entrar, o que não pode ser afirmado, quais números exigem denominador/tempo/unidade, qual contraprova precisa aparecer e quais omissões distorceriam a leitura. Priorizar desfechos primários, decisão, segurança e sensibilidades decisivas.

### Framing responsável

Registrar conflitos, incentivos, press releases, fonte da crítica externa e diferenças entre fonte original e narrativa secundária quando forem materialmente relevantes. Não criar controvérsia artificial nem falsa equivalência.

### Título, lead e fecho

O título descreve; não resolve a tese. O lead abre com a informação de maior valor para o leitor. O nut graf explica escopo e tensão. O fecho cumpre uma função: implicação, incerteza, monitoramento ou pergunta aberta — não uma repetição genérica.

## Saída

Entregar brief validado, outline por função de seção, hierarquia de resultados e critérios explícitos de inclusão/exclusão. Encaminhar somente claims autorizados para `reviews-edition-writing`.

## Bloqueios

Não iniciar prosa se o brief depender de contexto sem fonte, de headline que exceda a evidência ou de conflito não rastreado. Não usar exemplar como suporte factual.
