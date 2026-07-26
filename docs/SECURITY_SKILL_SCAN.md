# Inspeção de segurança das skills

## Escopo e método

Foi revisado o Cisco Skill Scanner como referência de cobertura, mas não foi
executado um binário externo nem conteúdo de terceiros. O repositório implementa
uma inspeção determinística local equivalente em
`reviews_editorial.assurance.scan_skill_tree`, acionada por:

```powershell
python scripts/scan_skills.py
```

Ela percorre recursivamente `SKILL.md`, referências, manifestos de eval e
scripts empacotados das skills. Bloqueia padrões de injeção de instruções,
exfiltração de segredos, pipe inseguro para interpretador, execução remota de
código, leitura de arquivos de credenciais e remoção destrutiva sem escopo.

## Resultado da execução de fechamento

Em 25 de julho de 2026, a execução retornou `passed: true`, `0` achados e `75`
arquivos inspecionados. A mesma execução aciona a validação profunda das 11
skills obrigatórias; ela retornou `valid: true` e nenhuma skill ausente.

## Limites

Resultado limpo não é certificação de segurança. O scanner não executa scripts,
não avalia dependências transitivas nem substitui revisão humana antes de adotar
uma fonte externa. A adoção de conteúdo externo permanece limitada ao que está
descrito em [SOURCE_ADOPTION_MAP.md](SOURCE_ADOPTION_MAP.md).
