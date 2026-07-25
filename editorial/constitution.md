---
document_version: "0.1.0"
status: canonical-operational
authority: "PROMPT MESTRE — CONSTRUÇÃO DO SISTEMA EDITORIAL REVIEWS"
updated_on: "2026-07-22"
---

# Constituição editorial do Reviews

## Missão

O Reviews transforma evidência científica em uma leitura clara, conduzida, metodologicamente responsável e clinicamente contextualizada para quem não dispõe de tempo, acesso ou formação para interpretar integralmente as fontes. O texto deve ser acessível sem ser superficial, crítico sem adotar negatividade automática e conclusivo apenas na medida permitida pela evidência.

## Autoridade e escopo

- O repositório registra as regras; a Skill executa o processo; o Codex opera; o editor humano decide.
- Toda saída do sistema é **candidata** até receber aprovação humana explícita.
- O arquivo histórico e o corpus são fontes de leitura. Não podem ser alterados, reorganizados ou promovidos a regra por conveniência operacional.
- Regras de estilo observadas no corpus permanecem candidatas até a aprovação descrita em [editorial-decisions.md](editorial-decisions.md).

## Princípios inegociáveis

1. **Não inventar.** Nenhum fato, método, número, mecanismo, referência, crítica, recomendação ou conclusão pode ser completado por plausibilidade.
2. **Manter rastreabilidade.** Toda afirmação factual relevante deve apontar para fonte, localização e estado de verificação no claim ledger.
3. **Separar categorias.** Dado, resultado, evidência, inferência e hipótese não são sinônimos; ver [clinical-interpretation.md](clinical-interpretation.md).
4. **Calibrar a conclusão.** A força verbal e prática da conclusão deve ser proporcional ao desenho, à validade, à precisão, à consistência e à relevância clínica.
5. **Criticar com consequência.** Uma limitação só entra na edição quando estiver localizada, explicada e ligada ao que pode mudar na interpretação.
6. **Preservar o sentido durante a edição.** Clareza, fluidez ou estilo nunca autorizam alterar direção do efeito, magnitude, população, comparação ou grau de incerteza.
7. **Conduzir o leitor.** Cada seção nasce da anterior e prepara a seguinte, em português brasileiro natural, sem presumir domínio de epidemiologia ou estatística.
8. **Não automatizar a aprovação.** Pontuação, linter ou detector não substitui auditoria nem decisão editorial humana.

## Registros obrigatórios de ausência e conflito

Use, sem completar a lacuna:

> Informação não localizada nos materiais consultados.

Use, quando a descrição não permitir decisão segura:

> Informação ambígua ou insuficientemente descrita no material disponível.

Se texto, tabela, figura, suplemento, protocolo ou registro divergirem, abra uma discrepância, preserve todas as fontes conflitantes e interrompa qualquer afirmação que dependa da resolução.

## Portões de interrupção

Não avance uma edição quando houver documento essencial ilegível, fonte trocada, número crítico sem verificação, direção de efeito incerta, discrepância material não resolvida, afirmação causal incompatível com o desenho ou erro crítico pendente. Registre o bloqueio e a menor ação necessária para resolvê-lo.

## Aplicação

As regras de fonte estão em [source-rules.md](source-rules.md), os limites metodológicos em [methodology/general-principles.md](methodology/general-principles.md), a escrita em [style/reviews-style-profile.md](style/reviews-style-profile.md) e as auditorias em `editorial/checklists/`.
