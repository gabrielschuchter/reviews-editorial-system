# Orquestração de agentes

## Modelo operacional

Os “agentes” deste sistema são papéis especializados executados pelo Codex. Eles não são microsserviços, usuários permanentes nem processos em segundo plano. O repositório fornece contratos; a Skill `reviews-writer` deve ordenar o trabalho; os scripts validam invariantes; o editor humano decide o que é canônico e o que pode ser publicado.

O MVP não contém um scheduler programático de agentes. Delegação e consolidação acontecem na execução do Codex. Portanto, um nome de papel não comprova que a etapa foi executada: o artefato esperado e seu gate são a evidência.

## Papéis e fronteiras

| Papel | Responsabilidade | Não pode fazer |
|---|---|---|
| Orquestrador editorial | Criar job, interpretar briefing, escolher fluxo, distribuir tarefas e verificar gates | Ignorar erro crítico ou executar tudo sem separação de responsabilidades |
| Bibliotecário documental | Inventariar, identificar versões, suplementos, protocolos, registros e duplicatas | Interpretar eficácia |
| Normalizador documental | Extrair texto, manter localizadores e mapear tabelas/figuras | Inventar paginação ou considerar figura legível sem inspeção |
| Classificador de desenho | Identificar desenho e variantes | Inferir um desenho não descrito apenas por plausibilidade |
| Extrator de evidências | Extrair população, intervenções, comparadores, desfechos, resultados e segurança | Redigir a edição |
| Verificador estatístico | Conferir números, unidades, denominadores, direção e contraste correto | Apresentar cálculo derivado como valor relatado |
| Revisor metodológico | Avaliar desenho, viés, análise, precisão, aplicabilidade e inferência | Produzir crítica genérica sem consequência interpretativa |
| Pesquisador de escrutínio externo | Buscar registro, protocolo, errata, retratação, cartas e críticas pertinentes | Tratar comentário externo como fato estabelecido |
| Arquiteto da edição | Escolher tipo, seções, hierarquia, resultados e exemplares | Misturar contratos sem registrar a decisão |
| Redator Reviews | Produzir v1 a partir do pacote validado | Navegar livremente no corpus ou adicionar informação não autorizada |
| Editor de estilo Reviews | Comparar com perfil, exemplares e regras | Alterar fatos ou interpretação sem registrar a mudança |
| Editor de português/anti-IA | Melhorar naturalidade, ritmo e conectividade | “Embelezar” sacrificando precisão |
| Auditor factual adversarial | Desafiar suporte e classificação de cada claim | Confiar em plausibilidade |
| Auditor metodológico adversarial | Procurar causalidade indevida, superinterpretação e omissões | Transformar possibilidade em problema demonstrado |
| Editor de coerência | Garantir progressão, conexão e consistência | Reabrir fatos sem devolver o conflito ao papel competente |
| Editor visual | Propor ativos com origem, função e risco | Bloquear a entrega textual por ausência de imagem |
| Finalizador/publicador | Aplicar correções aprovadas, gerar outputs e preparar entrega | Publicar ou marcar aprovação sem autorização humana |

## Ordem e paralelismo

Leituras independentes podem ocorrer em paralelo quando cada agente recebe fontes e outputs exclusivos. Exemplos adequados:

- inventário de arquivos, busca de suplemento e busca de registro;
- extração de seções distintas depois de a correspondência documental estar confirmada;
- conferência estatística e pesquisa externa, se não compartilham arquivos de saída;
- inspeção visual opcional enquanto a análise textual continua.

As etapas abaixo são sequenciais:

```text
validação documental
  -> normalização
  -> classificação do estudo
  -> extração
  -> verificação numérica
  -> claim ledger
  -> análise metodológica e pesquisa externa
  -> seleção do tipo e plano
  -> v1
  -> auditoria factual
  -> auditoria estatística/metodológica
  -> estrutura
  -> estilo/anti-IA
  -> coerência
  -> auditoria final
  -> candidata
  -> revisão humana
```

Redação, consolidação e edição final nunca devem ser paralelizadas sobre o mesmo arquivo. Um único papel deve ser o proprietário de cada versão do draft.

## Contrato de delegação

Toda tarefa delegada deve informar:

- `job_id` e estado atual;
- pergunta precisa;
- fontes autorizadas e suas versões/hashes;
- artefatos de entrada;
- artefato de saída e schema;
- ações proibidas;
- condição de interrupção;
- nível de confiança ou status que o papel pode atribuir.

O resultado deve conter:

- caminho do artefato produzido;
- fontes consultadas e localizadores;
- lacunas e ambiguidades;
- erros críticos;
- o que não foi executado;
- recomendação de próximo gate, sem avançá-lo por conta própria.

## Propriedade de artefatos

Cada artefato possui um produtor primário e um revisor diferente quando o risco justifica:

| Artefato | Produtor | Revisor/gate |
|---|---|---|
| `normalized/*-map.json` | Normalizador | Bibliotecário + confirmação manual |
| `analysis/study-classification.json` | Classificador | Revisor metodológico |
| `extraction/*.json` | Extrator | Verificador estatístico/factual |
| `number-verification.json` | Verificador estatístico | Auditor factual |
| `claim-ledger.json` | Extrator + orquestrador | Auditor factual adversarial |
| `methodological-review.json` | Revisor metodológico | Auditor metodológico adversarial |
| `planning/*` | Arquiteto | Orquestrador |
| `drafts/v1-content.md` | Redator | Cadeia de auditorias |
| `final/candidate.*` | Finalizador | Auditoria final + editor humano |

Agentes paralelos não devem editar o mesmo arquivo. A consolidação deve ocorrer em uma etapa separada e registrar conflitos.

## Gates e interrupções

O orquestrador bloqueia a redação final quando faltar artigo completo, houver tabela essencial ilegível, mistura de estudos, desfecho primário indefinido, comparador incerto, discrepância numérica crítica, direção do efeito incerta, versão de guideline não confirmada, retratação não tratada ou risco de atribuição à fonte errada.

Um bloqueio produz relatório, partes já concluídas, materiais faltantes e caminho seguro de retomada. Ele não autoriza descartar o job nem preencher a lacuna.

## Pesquisa externa

O pesquisador registra consulta, fonte, data e resultado. Se não houver acesso à web, deve escrever que a busca não foi realizada. “Não foram encontradas críticas” só é permitido depois de uma busca real e documentada.

Fontes primárias e oficiais têm prioridade. PubPeer, fóruns e cobertura jornalística podem indicar algo a investigar, mas precisam ser classificados e verificados antes de influenciar uma afirmação pública.

## Processamento em lote

Cada artigo gera um job independente. É permitido compartilhar regras, schemas, corpus aprovado e templates; não é permitido compartilhar extrações, claims, resultados, referências ou auditorias entre jobs.

Checkpoints são os próprios artefatos do job. Uma falha interrompe apenas o job afetado. O sistema não promete processamento em segundo plano.

## Revisão humana

O editor decide:

- promoção de corpus a A/B;
- decisões editoriais amplas;
- aceitação de combinações de tipos;
- transformação de feedback em regra geral;
- aprovação para publicação.

O Codex pode recomendar e preparar; não pode substituir essa autoridade.
