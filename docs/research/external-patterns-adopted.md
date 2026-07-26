# Padrões externos incorporados no Reviews

Este registro explica como os repositórios consultados foram convertidos em comportamento compatível com o Reviews. A unidade de trabalho do Reviews continua sendo uma edição clínica em PT-BR, não um manuscrito IMRAD, uma submissão acadêmica ou um pipeline de meta-análise.

| Origem consultada | Padrão aproveitado | Incorporação no Reviews | Limite de compatibilidade |
| --- | --- | --- | --- |
| Aperivue MedSci Skills: `orchestrate` | roteamento fino, pré-flight, outputs esperados e parar após falha | `reviews-writer` mantém estado, gates e retoma somente artefatos válidos | não pergunta por nós de decisão de pesquisa nem inicia publicação externa |
| Aperivue: `verify-refs` | auditoria somente-leitura e contrato de achado | `reviews-source-provenance` e `reviews-audit` separam correção de verificação | fontes do Reviews incluem diretrizes, artigos, documentos e contexto editorial, não apenas bibliografia de manuscrito |
| Aperivue: `check-reporting` e `self-review` | passagens por dimensão, severidade e verificação numérica | appraisal e audit percorrem método, inferência, números, framing e tabelas | não impõe checklists de relato de estudo a uma peça jornalística |
| paper-review-and-digest | aquisição antes da leitura, leitura por camadas e checagem de afirmações-chave | provenance exige inventário, normalização e claim ledger antes de redigir | não inclui profiling de autor/jornal quando isso não altera a decisão editorial |
| meta-pipe | layout de projeto, artefatos numerados, gates de qualidade e dependências explícitas | o estado do job e os artefatos de cada fase são preservados e validados | não transforma toda edição em revisão sistemática ou exige ferramentas estatísticas |
| paper-writer-skill | outline antes da prosa, revisão adversarial e separação entre draft/QC | brief antecede escrita; audit vem depois do draft | prosa Reviews conserva voz editorial e não usa fluxo IMRAD por padrão |
| med-paper-assistant | contrato operacional, leitura obrigatória de contexto e adaptação de ferramenta | cada skill declara entradas, saídas, limites e caminhos degradados | nenhum runtime ou ferramenta externa se torna dependência central |
| NOAH clinical trial | busca em camadas e fallback progressivo | provenance registra cobertura e fallback quando fonte/versão não está acessível | adaptador de busca fica opcional, sem consulta clínica automática |
| education-agent-skills | protocolo de credibilidade, sinais vermelhos/verdes e evidência explícita | hierarquia de fontes, papel da fonte e pendências de confiabilidade | não usa roteiro pedagógico nem pontuação de credibilidade simplista |
| Fuck My Shit Mountain | boundary de auditoria, cobertura por dimensão e achados estruturados | `audit-report` exige categoria, severidade, evidência, consequência e correção | não usa score agregado para mascarar blockers |
| Anthropic Skills e Trail of Bits | estrutura progressiva, contexto reduzido e workflow com gates | `SKILL.md` contém o fluxo essencial; detalhes estáveis ficam em `references/` | não migra o projeto para outro runtime de skills |
| obra/superpowers | evidência antes de declarar conclusão e prevenção de racionalizações | todas as skills terminam em gate verificável; ausência de evidência bloqueia avanço | validação automatizada não substitui julgamento humano |
| Promptfoo, plugin-eval e Cisco Skill Scanner | comparação de versões, casos de regressão e análise de segurança | evals locais e `scan_skills.py` cobrem invariantes do sistema | não instala plugins nem scanners externos como dependência de produção |
| humanizer / avoid-ai-writing / humanizer-ptbr | catálogo de padrões artificiais, sem tratar detector como verdade | escrita evita fórmulas, repetições e certeza vazia sem reescrever fatos | não promete detectar autoria por IA nem altera o estilo humano canônico |
| Docling, ASReview, RobotReviewer e metafor | especialização opcional para extração, triagem, appraisal e síntese | documentados como possíveis adaptadores futuros | não entram no caminho crítico sem piloto, contrato de dados e avaliação própria |

## Regras de adoção

1. Um padrão externo só entra quando preserva fonte, papel, limite de confiança e ponto de revisão humana.
2. Processo externo que pressupõe artigo acadêmico, submissão, meta-análise ou consulta clínica é adaptado ou descartado; nunca vira comportamento implícito.
3. Nenhuma skill pode enviar, publicar, baixar em lote, modificar fontes ou promover uma regra editorial sem autorização explícita do usuário ou gate humano.
4. Referências externas informam engenharia de workflow; a fonte primária e o corpus humano do Reviews continuam sendo a autoridade editorial.

Os snapshots, licenças e arquivos prioritários consultados estão em `external-source-inventory.md` e `external-license-matrix.md`.
