# Solução de problemas

## Diagnóstico rápido

| Sintoma | Causa provável | Ação segura |
|---|---|---|
| `python` não encontrado ou versão abaixo de 3.11 | Interpretador ausente/incorreto | Use `py -3.11` ou o runtime Python compatível disponível e repita o comando |
| `ModuleNotFoundError: reviews_editorial` ao chamar um módulo diretamente | `src/` não está no path | Execute o script em `scripts/`, que carrega `_bootstrap.py`, ou instale o projeto em modo editável |
| PDF pede extra opcional | `pypdf` ausente | Instale `.[documents]`; não troque por extração improvisada |
| Exportação DOCX pede extra opcional | `python-docx` ausente | Instale `.[documents]` e repita |
| Página PDF sem texto | Scan/imagem, proteção ou extração falhou | Bloqueie o uso daquela página e faça OCR/inspeção visual documentada fora do normalizador atual |
| DOCX não mostra páginas | Paginação depende de renderização | Use parágrafos/localizadores ou renderize antes de citar página |
| Tabelas/figuras de PDF ficam vazias | O normalizador não reconhece esses elementos | Inspecione o PDF visualmente e registre a extração com fonte e dupla conferência |
| `document-validation.json` continua pendente | Confirmação manual não ocorreu | Revise a checklist e use `--confirm-documents <revisor>` somente depois da inspeção |
| `Gate bloqueado: outputs obrigatórios ausentes` | Estado-alvo está adiante dos artefatos | Gere e valide os arquivos listados em `missing_outputs`; não crie arquivos vazios para contornar o gate |
| “avanço deve ocorrer para o estado imediatamente seguinte” | Tentativa de pular estado | Avance um estado por vez e registre o ator |
| Extração permanece inválida | Arquivos foram inicializados com `not-extracted` | Preencha com dados reais, localizadores e marque `extraction_status: validated` após revisão |
| `number-records.json` não encontrado | Conferência numérica ainda não foi preparada | Crie registros estruturados a partir da extração; não derive do draft |
| Claim ledger inválido | Campos, fonte, excerto ou localizador ausentes | Corrija o claim; não altere `allowed_in_public_draft` para esconder a lacuna |
| Número do draft aparece como “unmapped” | Token não está em claim público ou é falso positivo | Vincule o número correto ao claim; para ano/título, documente o falso positivo e mantenha revisão manual |
| Claim parafraseado passa sem suporte | Auditoria automática é literal | Execute auditoria factual adversarial; a passagem automática não é prova semântica |
| Roteador retorna código 2 | Tipo solicitado é incompatível e exige editor | Registre a incompatibilidade e peça decisão; não force a recomendação |
| Nenhum exemplar selecionado | Não há item A/B aprovado compatível | Continue apenas com regras aprovadas e registre a lacuna; não use C/D como B silenciosamente |
| Perfil de estilo parece estranho | Corpus inadequado ou pequeno | Confirme que somente A/B aprovados entraram e trate as métricas como descritivas |
| Linter anti-IA gera muitos avisos | Heurística encontrou frases comuns | Revise função, repetição e naturalidade; não faça substituição cega de palavras |
| DOCX falha na auditoria | Estrutura ou estilo do pacote não atende ao preset | Corrija o exportador/Markdown e gere novamente; não entregue o arquivo quebrado |
| DOCX abre, mas layout está ruim | Auditoria estrutural não cobre renderização | Abra/renderize, revise tabelas e quebras e repita a exportação |
| `publish_to_drive.py` “não publicou” | Comportamento esperado | Use o manifesto com o conector depois de verificar permissões; o script nunca faz upload |
| Destino coincide com arquivo-fonte | Proteção contra escrita histórica | Corrija para o ID da produção; nunca remova a proteção |
| Ferramenta de escrita existe, mas upload é incerto | Permissão/visibilidade detalhada não verificada | Faça leitura de metadados e teste controlado autorizado ou entregue localmente |
| `run_checks.py` falha por arquivo obrigatório | Esqueleto incompleto | Crie/preencha o artefato real correspondente; não desative a verificação |
| `run_checks.py` acusa `TODO` na Skill | Skill ainda é scaffold | Conclua a Skill conforme os contratos antes de declarar o MVP operacional |
| Schema passa no JSON, mas o conteúdo é incoerente | Schema verifica forma, não verdade | Reexecute revisão factual/metodológica |

## Normalização bloqueada

Preserve o arquivo original e o erro. Não tente “consertar” o original. Verifique:

1. se o formato corresponde à extensão;
2. se o arquivo está completo e abre em leitor independente;
3. se é o documento correto;
4. se o extra opcional está instalado;
5. se páginas, tabelas e figuras críticas são legíveis;
6. se há outra versão oficial ou suplemento.

Registre falhas em `normalized/document-validation.json` e `missing-materials.md`. Um segundo arquivo obtido depois deve ser adicionado como nova fonte com hash, não sobrescrever o primeiro.

## Gate bloqueado por erro crítico

Procure em:

- `job.yml.gates.critical_errors`;
- `normalized/document-validation.json`;
- arquivos JSON em `audits/`;
- `analysis/critical-issues.md`.

Resolva a causa e atualize o artefato responsável com histórico. Como a máquina lê criticidade de JSON e do job, um problema descrito apenas em Markdown pode não bloquear automaticamente; replique o bloqueio no campo estruturado apropriado.

Não edite o estado manualmente para avançar. Use `validate_job.py` e preserve `history`.

## Divergência numérica

1. Confirme documento, versão e população de análise.
2. Compare texto, tabela, figura e suplemento.
3. Confira unidade, escala, sinal e denominador.
4. Separe valor relatado de cálculo derivado.
5. Registre ambas as fontes conflitantes.
6. Marque `divergent` ou `ambiguous`.
7. Bloqueie a redação se a divergência altera direção, magnitude ou conclusão.

Não escolha o valor mais plausível nem faça média entre valores conflitantes.

## Pesquisa externa indisponível

Preencha o log com data, escopo pretendido e declaração de que a busca não foi realizada. Não escreva “não foram encontradas críticas”. O job pode preservar o trabalho anterior, mas não deve fingir que o estado `external_research_complete` tem conteúdo real.

## Recuperação de um job

Jobs são checkpoints por arquivos. Para retomar:

1. leia `job.yml` e o último item de `history`;
2. rode `validate_job.py` sem `--advance`;
3. corrija apenas os outputs ausentes ou inválidos do próximo gate;
4. reexecute as auditorias afetadas por qualquer mudança anterior;
5. avance um estado;
6. nunca reutilize artefatos de outro job.

Se uma fonte mudou, registre-a como nova versão e reexecute todas as etapas dependentes; o hash anterior não deve ser substituído silenciosamente.

## Drive

Se o conector não permitir escrita, entregue `.md`, `.docx` e `drive-transfer.json` localmente. Se a escrita ocorrer, releia o item e registre ID/URL retornados. Falha de upload não autoriza escrever no arquivo-fonte nem sintetizar um link.

Se não estiver claro quem pode ver o arquivo criado, interrompa antes do upload. A pasta de produção estava vazia na descoberta e suas propriedades detalhadas ainda precisam ser confirmadas.

## Quando pedir decisão humana

Escalone ao editor quando houver:

- material candidato a A/B;
- tipo solicitado incompatível;
- combinação de tipos;
- título ou estrutura ainda pendente;
- conflito de fontes sem resolução documental;
- regra candidata derivada de feedback;
- uso de ativo com direito/permissão incerto;
- aprovação para publicação.

Escalonar não significa abandonar o job. Entregue o diagnóstico, o que já foi validado e a menor decisão necessária para continuar.
