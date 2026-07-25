# Sistema visual

## Posição do MVP

O MVP é textual. Visuais são opcionais e não podem bloquear uma candidata completa. A política-base é:

```yaml
visuals:
  enabled: false
  use_article_figures: conditional
  use_reviews_design_system: conditional
  allow_generated_scientific_images: false
```

Não existe frontend neste repositório e esta documentação não autoriza criar um.

## Status da referência fornecida

O arquivo `documentação design reviews.md` se apresenta como engenharia reversa da página de reports da plataforma. Ele é uma referência candidata, não um design system canônico:

- não foi fornecido como especificação oficial aprovada;
- tokens e componentes parecem ter sido inferidos da interface;
- afirmações sobre framework, fontes e comportamento não foram verificadas contra código-fonte;
- o arquivo termina no meio de um exemplo do cartão da evidência, portanto está incompleto;
- não houve aprovação editorial dos componentes para os novos tipos de edição.

Classifique-o inicialmente como D, “material de discussão”, até validação humana. Não use a versão `1.0.0` declarada pelo documento como prova de canonização.

## Observações candidatas, não normativas

| Aspecto | Candidato inferido no documento |
|---|---|
| Fundo | `#FAF9F5` |
| Texto principal | `#141413` |
| Accent terracota | `#D97757` |
| Superfícies | `#EDE9DF`, `#F0EEE6` |
| Borda | `#E2DED4` |
| Serif | Source Serif 4 |
| Sans | Inter |
| Raio recorrente | 8 px, com caixas pontuais de 12 px |
| Leitura | coluna de aproximadamente 700 px |
| Componentes observados | hero, cartão da evidência, banners de seção, tabelas, takeaways e leituras recomendadas |

Esses valores podem orientar um protótipo somente se o editor aprovar seu uso. Não invente componentes, estados ou variações ausentes.

## Saída DOCX atual

`src/reviews_editorial/export_docx.py` não implementa o visual acima. O preset atual é deliberadamente simples e voltado à compatibilidade com Google Docs:

- página Letter com margens de 1 polegada;
- Arial em corpo, títulos e listas;
- preto/cinza;
- suporte básico a headings, parágrafos, listas, negrito, itálico, código inline e tabelas Markdown;
- auditoria estrutural do pacote DOCX.

O exportador não aplica Source Serif 4, Inter, terracota, cards, banners ou imagens. Também não interpreta todo o Markdown. Portanto, “DOCX gerado” não significa “design Reviews aplicado”. Qualquer aproximação visual futura exige contrato aprovado, implementação separada e inspeção renderizada.

## Figuras do artigo

Uma figura pode entrar no plano apenas quando:

- melhora materialmente a compreensão;
- está legível no arquivo correto;
- tem origem, localizador e legenda registrados;
- não é recortada de modo a alterar a interpretação;
- seu uso e adaptação são compatíveis com direitos e permissões;
- contexto e limitações são preservados.

A normalização atual detecta mídia empacotada em DOCX e marca mapas vazios para figuras de PDF; ela não valida conteúdo, legenda, licença ou legibilidade. Inspeção visual é obrigatória.

## Recriação de gráficos

Só recrie um gráfico quando todos os valores estiverem disponíveis e verificados, com dupla conferência, fonte indicada e identificação explícita de que é uma recriação. Não imite a aparência da figura original a ponto de confundir autoria.

O gráfico deve preservar:

- denominadores, unidades e escalas;
- direção favorável/desfavorável;
- intervalos e incerteza;
- categorias e tempos;
- ausência de dados e notas relevantes.

Não derive pontos de uma imagem quando a resolução não permite leitura confiável.

## Imagens geradas

É proibido gerar imagens anatômicas, mecanismos, resultados ou gráficos científicos que possam ser confundidos com evidência. Uma ilustração editorial não científica só pode ser considerada quando tiver função clara, não sugerir precisão, estiver identificada e seguir um sistema visual aprovado.

## Plano visual obrigatório

Mesmo quando nenhum visual for usado, `final/visual-plan.md` registra a decisão. Para cada item proposto, inclua:

| Campo | Pergunta |
|---|---|
| elemento | O que será mostrado? |
| função | Que dúvida do leitor resolve? |
| origem | Artigo, recriação ou ativo editorial? |
| localização | Onde aparece na fonte e na edição? |
| risco | Pode distorcer magnitude, comparação ou certeza? |
| permissão | Há direito/autoridade para uso? |
| decisão | incluir, adaptar, omitir ou aguardar |

O schema `visual-asset.schema.json` deve ser usado para o registro estruturado correspondente.

## Verificação visual

Antes da entrega:

- renderize e inspecione o DOCX, não apenas seu XML;
- confira tabelas largas, quebras, hierarquia e caracteres especiais;
- valide contraste, legibilidade e significado sem depender apenas de cor;
- confira legenda, fonte e relação entre texto e visual;
- confirme que a versão no Google Docs não degradou o layout;
- mantenha o conteúdo compreensível sem a imagem.

## Caminho para canonização

1. Comparar a documentação reversa com a plataforma atual e, se possível, com ativos oficiais.
2. Separar observado, inferido e recomendado.
3. Inventariar componentes realmente usados nas edições.
4. Resolver direitos de fontes, imagens e ativos.
5. Validar acessibilidade e comportamento de exportação.
6. Obter aprovação do editor.
7. Versionar tokens e templates aprovados.
8. Criar testes renderizados de regressão.

Até esse processo terminar, registre `design_system_version: 1.0.0-candidate-unverified` ou outro estado explicitamente não aprovado.
