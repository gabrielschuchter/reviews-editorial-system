# Curadoria do corpus

## Princípio

O corpus serve para recuperar exemplos e regras pertinentes; ele não treina o modelo nem torna um padrão frequente automaticamente correto. Todo material entra como evidência editorial a ser classificada, e não como norma.

Nenhum item é promovido automaticamente a canônico (A) ou referência B. Essas duas classificações exigem decisão explícita do editor. O nível B nunca significa “perfeito”: limitações conhecidas devem acompanhar o registro e a aprovação humana final permanece obrigatória.

## Fontes conhecidas nesta descoberta

| Fonte | Conteúdo observado | Limite de interpretação |
|---|---|---|
| Drive de arquivo-fonte `1eIfDPteYjjijHv-u9JPMkgfvVSY0fv6f` | Biblioteca histórica do Reviews | Tratar como somente leitura; inventário não equivale a curadoria |
| Drive de produção `1q1DoS2nm9JKq-zreLaNk7i5YO1-rqo7s` | Pasta vazia no momento da descoberta | Não contém corpus nem comprova permissões detalhadas de escrita/visibilidade |
| `drive-download-20260722T201201Z-1-001.zip` | 57 DOCX: 34 na raiz e 23 em prompts para imagens do Instagram | Predominantemente prompts, memórias e materiais de processo; autoridade precisa ser decidida item a item |
| `drive-download-20260722T201133Z-1-001.zip` | 68 arquivos: 52 DOCX, 14 PNG, 1 JPG e 1 JPEG | Inclui áreas nomeadas `Publicados`, `Versões antigas`, `Sugestões de Temas` e `Entendendo o Risco`; nomes são sinais, não prova de status |
| `documentação design reviews.md` | Engenharia reversa do visual da plataforma | Candidata de discussão, não design system canônico; documento incompleto |
| Drive `Testes` `1-l8YAR19a9pu63rpysZ8BgqsZ6znzQv1` | Sete pacotes revisados com publicações, auditorias e materiais antes/depois | Fonte crucial de aprendizagem; versões finais próximas do ideal, mas não perfeitas nem canônicas |

Os ZIPs são snapshots locais fornecidos separadamente. Não se deve presumir, sem metadados adicionais, qual snapshot corresponde integralmente a qual estado atual do Drive. Também não foram identificados artigos-fonte suficientes para associar com segurança cada edição ao estudo correspondente.

## Níveis obrigatórios

| Nível | Significado | Pode orientar diretamente a escrita? |
|---|---|---|
| A | Canônico atual | Sim, dentro do escopo aprovado |
| B | Referência próxima do ideal, com limitações conhecidas | Sim, como exemplo pertinente; nunca como padrão perfeito |
| C | Publicado, mas histórico | Apenas para contexto e trajetória |
| D | Material de discussão | Não, salvo uso explicitamente aprovado no job |
| E | Legado ou desatualizado | Não como regra atual |
| F | Excluído ou duplicado | Não |

Pastas estruturais não são conteúdo editorial. Duplicatas exatas são mantidas no inventário para rastreabilidade, classificadas como F e apontadas para o registro principal.

## Inventário reproduzível

`scripts/inventory_corpus.py` aceita ZIPs, arquivos locais e snapshots JSON do Drive. O inventário registra, quando disponível:

- caminho, nome, formato, tamanho, datas, ID e URL;
- hash binário e hash do texto normalizado;
- escopo real da inspeção;
- nível proposto, justificativa e alertas;
- sinais de comentários, alterações rastreadas ou texto vermelho em DOCX;
- associação com artigo e status editorial, mesmo quando permanecem não resolvidos.

Para ZIPs, os arquivos são lidos sem serem extraídos para o corpus. DOCX recebe extração de texto e sinais de revisão; outros formatos recebem metadados e hash binário. Um snapshot do Drive pode fornecer metadados e, em itens selecionados, texto previamente obtido pelo conector.

Exemplo:

```powershell
python scripts/inventory_corpus.py `
  --zip "D:\drive-download-20260722T201201Z-1-001.zip" `
  --zip "D:\drive-download-20260722T201133Z-1-001.zip" `
  --file "D:\documentação design reviews.md"
```

Os outputs-base são `SOURCE_INVENTORY.csv` e `corpus/manifest.yml`. Catálogos incrementais posteriores podem ser anexados por `curated_catalogs` sem reescrever o snapshot antigo. O manifesto atual carrega `testes-learning-catalog.yml`: 301 registros-base + 7 registros curados = 308 efetivos.

## Heurísticas são propostas, não decisões

O classificador conservador usa nomes e localizações para levantar hipóteses. Por exemplo:

- `Versões antigas`, prompts antigos, memórias de ferramenta e testes sugerem E;
- marcadores explícitos como `[publicado]` sugerem C;
- estar apenas dentro de `Publicados` sugere D, porque a pasta observada contém estados mistos;
- imagens e documentos de design começam em D;
- itens sem sinal confiável começam em D.

Essas regras evitam promoção indevida. Elas não substituem inspeção do conteúdo, confirmação do editor ou verificação de que a versão é realmente final.

## Fluxo de curadoria

1. Gerar o inventário sem modificar as fontes.
2. Resolver duplicatas binárias e textuais.
3. Confirmar o tipo de cada item: edição, artigo, guideline, prompt, comentário, ativo visual ou material administrativo.
4. Associar edição e artigo somente com evidência suficiente.
5. Propor nível A–F e registrar justificativa.
6. Separar materiais com sinais de revisão para inspeção antes/depois.
7. Reservar um holdout antes de construir o perfil de estilo.
8. Obter aprovação editorial para qualquer A ou B.
9. Aplicar overrides com `scripts/classify_corpus.py` e manter o log da mudança.

Uma promoção a A ou B exige `approved_by_editor` e justificativa. B também exige `quality_status` e uma lista `known_limitations`. O núcleo recusa a promoção sem esses campos.

Para um item do snapshot-base, use `--manifest`. Para alterar explicitamente um registro incremental, use `--catalog corpus/testes-learning-catalog.yml`; o comando não deve achatar o catálogo dentro do manifesto nem duplicar registros.

## Antes/depois, negativos e holdout

Versões candidatas e corrigidas devem gerar registros por mudança com seção, trecho original, trecho editado, motivo, classificação e indicação de generalização. Texto vermelho, comentários e alterações rastreadas são apenas sinais de que pode existir feedback; não são, por si, uma regra aprovada.

O holdout não participa da seleção de exemplos durante a redação. Ele serve para testar generalização, risco de cópia, fidelidade estrutural e estabilidade entre temas.

Exemplos negativos devem registrar por que não são aceitáveis. Sem essa explicação, o sistema pode imitar a forma proibida sem compreender o problema editorial.

## Perfil de estilo e exemplares

`build_style_profile.py` calcula métricas descritivas de parágrafos, frases, títulos, densidade numérica e conectores. O perfil atual `style-profile-testes-candidate.json` usa somente as seis referências de treinamento e exclui o holdout. Ele permanece candidato; métricas não viram limites rígidos.

`select_exemplars.py` recupera no máximo um conjunto pequeno de registros A/B compatíveis com tipo de edição, desenho e seção. Ele não carrega o corpus inteiro e retorna um aviso quando não há exemplar aprovado.

## Estado atual e lacunas

- não há material A canônico aprovado;
- há sete referências B da pasta `Testes`, todas explicitamente próximas do ideal com limitações;
- seis podem ser recuperadas e uma está reservada como holdout;
- a área `Publicados` contém nomes e cópias conflitantes que exigem confirmação;
- há duplicatas aparentes e versões com nomes como `Cópia`, `[Revisando]` e `Versões antigas`;
- a associação entre edição e artigo está amplamente não resolvida;
- os arquivos de prompts podem documentar práticas históricas, mas não são regras atuais sem aprovação;
- a documentação visual é uma engenharia reversa candidata e não deve entrar no nível A por default.

A próxima etapa de curadoria é validar o comportamento em um piloto real, revisar as limitações observadas e decidir se algum material merece nível A. O sistema não deve “corrigir” as referências B para uma perfeição presumida nem aprender silenciosamente com todo arquivo chamado final.
