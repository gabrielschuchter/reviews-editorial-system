# Relatório de descoberta

Data: 22/07/2026  
Escopo: dois ZIPs locais, documentação visual local, duas pastas do Google Drive e o repositório inicialmente vazio.  
Regra: nenhuma fonte original foi alterada.

## Resumo executivo

O acervo é suficiente para construir a arquitetura e iniciar curadoria, mas ainda não para declarar um estilo canônico ou produzir uma edição real com segurança. O inventário contém 301 registros, incluindo arquivos repetidos entre ZIP e Drive e 24 pastas estruturais. A classificação inicial é propositalmente conservadora: A=0, B=0, C=4, D=244, E=25 e F=28. Todos os níveis são propostas, não aprovações.

Esse parágrafo descreve o snapshot-base de 22/07/2026. Em 25/07/2026 foi inspecionada uma fonte incremental, documentada abaixo, que eleva o total efetivo carregado para 308 e resolve parcialmente a curadoria B/holdout sem alterar retroativamente o inventário histórico.

## Fontes locais

### `drive-download-20260722T201201Z-1-001.zip`

- 2.655.853 bytes; SHA-256 `2DD26CD67A443C09EC101F0CA547830851C818821611259285C1387C40D96587`.
- 57 DOCX: 34 prompts editoriais na raiz e 23 prompts de Instagram.
- Candidatos relevantes: `META-PROMPT — ESTILO DE ESCRITA DO REVIEWS`, `PROMPT AUDITORIA`, modelo e prompts de seções.
- Legado explícito: prompts antigos/teste, memórias de ChatGPT e preferências de Claude.
- Duplicatas: `PROMPT APRENDER MD` e a família `MODO SUPREMO`.
- Não contém o design system visual real; os prompts dependem de documentação externa.

### `drive-download-20260722T201133Z-1-001.zip`

- 83.906.574 bytes; 68 arquivos: 52 DOCX, 14 PNG e 2 JPEG/JPG.
- Áreas: 26 manuscritos na raiz, 25 itens em `Publicados`, 7 em `Entendendo o Risco`, 8 sugestões de temas e 2 versões antigas.
- `Publicados` não garante versão final: há `[Revisando]`, observações em vermelho e comentários.
- 40/52 DOCX avisam que textos vermelhos são observações; 41 têm trechos vermelhos; 6 têm comentários Word; nenhum tem alterações rastreadas.
- Há uma triplicata binária de GLP-1 e famílias versionadas de doença celíaca, Cookbook Cancer, EASO, proteína, colágeno e GLP-1.
- Referência publicada mais limpa identificada: `[publicada] Reviews Colágeno RS com MA Cópia 07_01_26.docx`; isso não a promove automaticamente a exemplar B.

### Documentação visual

`documentação design reviews.md` tem 35.500 bytes e descreve, por engenharia reversa, paleta, tipografia, layout e componentes do EVIDENS Reviews. Registra `#FAF9F5`, `#141413`, `#D97757`, Inter, Source Serif 4, header de 64 px, sidebar de 240 px e artigo de aproximadamente 700 px. O próprio documento contém inferências e sugestões; foi classificado como D, candidato a validação, não fonte técnica canônica.

## Google Drive

### Produção

- Pasta `reviews-editorial-system`: `1q1DoS2nm9JKq-zreLaNk7i5YO1-rqo7s`.
- Estava vazia na descoberta.
- O conector expõe criação de pastas, upload, importação DOCX→Google Docs e leitura de retorno.
- O Drive informou compartilhamento e capacidade de compartilhar, mas não expôs ACL detalhada, propriedade ou visibilidade pública. A escrita não foi testada nesta execução.

### Arquivo-fonte

- Pasta `Reviews`: `1eIfDPteYjjijHv-u9JPMkgfvVSY0fv6f`.
- 175 descendentes: 24 pastas e 151 arquivos.
- Tipos: 127 Google Docs, 1 Markdown, 15 PNG, 2 JPEG, 3 MP4, 2 DOCX e 1 PDF.
- Tamanho conhecido: 4.176.700.609 bytes; 98,4% são três gravações MP4.
- Artefatos centrais: estatuto 0.1a, POP 0.1a, modelos de Resposta Clínica/Geral/Diretrizes, meta-prompt de estilo, prompt de auditoria, mapa de edições, links Canva, transcrições e design system.
- O arquivo mistura `Cópia de`, `[Revisando]`, `[publicado/a]`, `Versões antigas` e `Testes/Antigos`; status e versão não são metadados confiáveis.

### Delta verificado em 25/07/2026 — pasta `Testes`

- Pasta: `1-l8YAR19a9pu63rpysZ8BgqsZ6znzQv1`, criada/modificada depois do snapshot de 22/07.
- Foram localizados sete pacotes editoriais, sete documentos `PUBLICAÇÃO FINAL`, sete `AUDITORIA FINAL`, documentos iniciais/revisados e um relatório mestre.
- A pasta é fonte crucial e prioritária de aprendizado por decisão explícita do editor.
- As sete publicações são próximas do ideal, mas ainda não atingem o ideal; nenhuma pode ser tratada como perfeita ou canônica A.
- Os sete itens foram registrados como B com limitações conhecidas. As edições 01–06 entram na recuperação e a edição 07 SII fica reservada como holdout.
- O pacote de sangramento GI baixo contém registro integral, versão humana final, auditoria e aprendizagem editorial; hipóteses de aprendizagem continuam provisórias e não viram regras universais automaticamente.
- O catálogo incremental está em `corpus/testes-learning-catalog.yml`; o perfil descritivo candidato está em `editorial/style/style-profile-testes-candidate.json`.
- A pasta de produção continuava vazia na leitura de 25/07/2026. Nenhuma escrita foi feita.

## Associações edição–artigo

Não foi possível estabelecer associações auditáveis entre todas as edições e seus artigos-fonte. Os dois ZIPs não contêm o conjunto correspondente de artigos científicos completos, e a maior parte do Drive foi lida apenas por metadados. Nomes temáticos foram preservados, mas não foram convertidos em DOI, citação ou vínculo factual inferido.

## Modelos e exemplos antes/depois

Foram identificados modelos de Resposta Clínica, Diretrizes e um modelo geral, além de famílias de versões. Ainda não há pares antes/depois confirmados pelo editor com justificativa da correção. As famílias versionadas são candidatos à análise, não exemplos de aprendizado aprovados.

## Riscos principais

1. Promover frequência ou publicação aparente a regra atual.
2. Incorporar observações vermelhas e comentários ao texto final.
3. Misturar versões e duplicatas.
4. Usar o design documentado por engenharia reversa como autoridade sem validação.
5. Escrever sem artigo, suplemento, protocolo e registro correspondentes.
6. Confundir acesso compartilhado com permissão pública ou propriedade confirmada.

## Resultado da descoberta

O repositório local foi construído com inventário, contratos, Skill, regras provisórias, scripts e gates. O delta `Testes` foi incorporado como fonte de aprendizagem limitada, não como padrão perfeito. Nenhuma edição real, mudança no Drive, commit ou publicação foi executada.
