# Exemplos e autochecagem de avaliação científica

## Exemplos concretos

### Exemplo 1: Ensaio com desfecho clínico e perdas desbalanceadas

O ensaio relata menos hospitalizações no grupo intervenção, mas 18% dos
participantes desse grupo não têm desfecho final, contra 5% no comparador.

Resposta: criar issue ligado ao claim de hospitalização; descrever perdas,
motivos disponíveis e possível superestimação de benefício como potencial ou
provável conforme dados. O bottom line pode mencionar a estimativa, mas reduz
a segurança; não declara ineficácia nem fraude.

### Exemplo 2: Coorte com associação ajustada

Uma coorte associa exposição alimentar a menor mortalidade após ajuste por
idade e tabagismo, sem medir gravidade basal.

Resposta: classificar como associação; registrar confundimento residual
plausível com mecanismo específico e manter linguagem não causal. O intervalo
estreito não elimina a necessidade dessa fronteira.

### Exemplo 3: Diretriz com recomendação condicional

Uma diretriz recomenda uma intervenção de forma condicional para população
restrita e declara certeza baixa.

Resposta: separar estudo, certeza e recomendação; preservar população,
condicionalidade e exceções. O brief pode discutir a decisão, mas não a chama
de regra geral nem de evidência de alta certeza.

## Casos adversariais

### Caso adversarial A: p maior que 0,05 vira “não funciona”

Um intervalo inclui benefício importante e dano, com p maior que 0,05.

Resposta: registrar imprecisão; não declarar ausência de efeito nem
equivalência.

### Caso adversarial B: Subgrupo com um p significativo

O efeito é significativo em mulheres, não em homens, mas não há teste de
interação.

Resposta: não afirmar heterogeneidade por sexo; classificar como exploração
ou informação insuficiente, conforme pré-especificação e multiplicidade.

### Caso adversarial C: Redução de biomarcador vira benefício clínico

Um estudo reduz um biomarcador em oito semanas sem medir sintomas ou eventos.

Resposta: nomear o marcador e bloquear a conclusão sobre benefício ao paciente.
O resultado pode entrar como dado, não como solução clínica.

## Critérios de autoavaliação

Cada caso passa se a análise identifica unidade de resultado, localizador,
categoria do claim, limite de inferência, consequência específica e modalidade
permitida. Os cenários formais correspondentes estão em ../evals/cases.json.
