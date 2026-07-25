---
name: reviews-feedback-learning
description: Comparar candidata e revisão humana do Reviews, produzir diff semântico e transformar padrões apenas em regras candidatas com teste de regressão. Use ao incorporar correções humanas ou revisar o corpus de aprendizagem.
---

# Feedback learning

Ler `references/promotion-policy.md` e preservar as duas versões humanas.

1. Comparar texto, estrutura, tabela, claim e fonte sem reescrever originais.
2. Classificar a mudança como correção factual, método, estrutura, estilo, preferência ou decisão editorial contextual.
3. Registrar motivo provável, confiança, escopo, risco de supergeneralização, antes/depois e caso de regressão.
4. Criar padrão `candidate`; só promover com aprovação editorial, exemplo verificável e teste verde.
5. Nunca simular fine-tuning, alterar corpus canônico ou transformar frequência em autoridade.
