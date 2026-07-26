# Exemplos e autochecagem de proveniência

## Exemplos concretos

### Exemplo 1: Ensaio com suplemento localizado

Entrada: artigo completo, suplemento e registro do ensaio. O resultado
primário está no texto e a análise de sensibilidade no suplemento.

Saída correta: artigo e suplemento entram como primary-evidence; o registro
entra para pré-especificação. O claim do resultado aponta para a tabela do
artigo; o claim da sensibilidade aponta para a tabela suplementar. O source map
não atribui a análise suplementar ao texto principal.

### Exemplo 2: DOCX de diretriz sem paginação estável

Entrada: uma diretriz em DOCX com recomendação e tabela em parágrafo
identificável, mas sem paginação confiável.

Saída correta: o localizador usa seção, título da tabela e trecho verificável;
não inventa número de página. A versão e a entidade publicadora são conferidas
antes de a diretriz receber papel de primary-evidence para sua recomendação.

### Exemplo 3: Cálculo absoluto derivado

Entrada: tabela relata 10/100 versus 15/100 e não fornece diferença absoluta.

Saída correta: dois claims result preservam os números originais; um terceiro
claim derived-calculation registra fórmula 15% - 10% = 5 pontos percentuais,
unidade, localizadores e rótulo de cálculo do sistema. Nenhum texto atribui
“5 pontos percentuais” aos autores.

## Casos adversariais

### Caso adversarial A: Press release no lugar do artigo

Entrada: título da notícia e um press release anunciam benefício, mas não há
artigo completo.

Resposta: o press release pode ser context-only. Registre artigo completo como
ausente; não libere resultado, mecanismo ou mudança de prática.

### Caso adversarial B: Texto e tabela discordam

Entrada: o texto diz 12 eventos e a tabela diz 14, sem evidência de que se
referem a populações ou tempos diferentes.

Resposta: registre discrepância e marque ambos os claims como divergent; a
edição não recebe o número até reconciliação ou delimitação explícita.

### Caso adversarial C: Comentário de rede social acusa fraude

Entrada: comentário externo sem documento oficial ou resposta dos autores.

Resposta: registre como external-scrutiny, alegação não confirmada e bloqueie
qualquer frase que a apresente como fato. Não use a acusação como motivo para
rebaixar automaticamente a evidência.

## Critérios de autoavaliação

Para cada caso, confirme: identidade da fonte; papel adequado; localizador
reproduzível; estado de autorização correto; ausência/discrepância registrada;
e nenhum claim público dependente de informação bloqueada. Os mesmos cenários
estão formalizados em ../evals/cases.json.
