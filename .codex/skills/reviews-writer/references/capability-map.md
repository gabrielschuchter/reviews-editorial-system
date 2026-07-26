# Mapa de capacidades do Reviews

## Sequência obrigatória

O orquestrador preserva evidência antes de framing, framing antes de prosa,
diagnóstico antes de humanização, auditoria antes de apresentação e feedback
depois de decisão humana. Uma capability não absorve o papel de outra.

| Skill | Consome | Produz | Não faz |
| --- | --- | --- | --- |
| reviews-source-provenance | fontes registradas | inventário, roles, ledger | concluir clinicamente |
| reviews-scientific-appraisal | ledger e extração | limites, viés, certeza | redigir candidata |
| reviews-editorial-brief | evidência avaliada | decisão, seleção, outline | inventar contexto |
| reviews-journalistic-framing | brief e limites | título proporcional, contraponto | ampliar evidência |
| reviews-edition-writing | claims autorizados | draft e tabela | aprovar texto |
| reviews-anti-ai-writing | candidata | relatório de ocorrências | reescrever automaticamente |
| reviews-humanizer-ptbr | findings e ledger | diff mínimo, reauditoria | mudar fatos |
| reviews-audit | candidata e fontes | findings independentes | corrigir silenciosamente |
| reviews-document-presentation | conteúdo auditado | DOCX/render report | esconder condição |
| reviews-feedback-learning | versões e feedback | proposta testável | promover regra automaticamente |

## Regras de roteamento

Use provenance quando fonte, versão, localizador ou permissão de claim não
estiverem comprovados. Use appraisal quando frase depende de causalidade,
certeza, aplicabilidade, recomendação ou relevância clínica. Use brief para
decidir o que entra; use framing para decidir como entra sem fabricar conflito.
Use audit depois de qualquer mudança material, inclusive humanização que toque
claim, título, tabela ou conclusão.

## Critérios de retomada

Retome somente do último artefato válido. Mudança em fonte, hash, população,
comparador, resultado ou limite de inferência invalida artefatos dependentes.
Alteração exclusivamente visual pode começar em apresentação apenas se não
truncar condição, nota, referência ou linha de tabela.

## Handoff mínimo

Cada capability devolve caminho do artefato, versão de entrada, decisões,
incertezas, blockers, claims afetados e próxima capability. O orquestrador não
resolve divergência escolhendo a saída conveniente; registra e devolve ao
responsável apropriado.
