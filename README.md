# Reviews Editorial System

Sistema editorial Codex-native para transformar documentos científicos em edições candidatas do Reviews com rastreabilidade, gates e revisão humana obrigatória.

O repositório é o cérebro normativo; a Skill `reviews-writer` orquestra o processo; o Drive é biblioteca e destino autorizado; o Google Docs é a superfície de revisão. Não há frontend, autenticação, banco remoto ou publicação automática.

## Estado desta entrega

- descoberta e inventário reproduzível das fontes fornecidas;
- arquitetura editorial e contratos versionados;
- criação e validação de jobs isolados;
- normalização básica de Markdown, texto, DOCX e PDF;
- roteamento de tipo de edição;
- claim ledger e gates de auditoria;
- seleção de exemplares, comparação de versões e feedback sem promoção automática;
- exportação opcional de candidata para DOCX;
- integração com Drive documentada e deliberadamente mediada pelo Codex;
- testes de regressão e verificador agregado.
- arquitetura modular 0.3 com sete capacidades especializadas e `reviews-writer` como fachada compatível;
- contratos para source roles, brief editorial, findings e padrões de aprendizado;
- linter determinístico de saltos inferenciais, validador de recomendações tabulares e scanner local de skills.

O sistema não escreve uma edição real até que o pacote documental mínimo, a extração e o claim ledger estejam válidos.

## Início rápido

```powershell
python -m unittest discover -s tests -v
python scripts/run_checks.py
python scripts/run_evals.py
python scripts/scan_skills.py
python scripts/create_job.py --source "C:\caminho\artigo.pdf" --topic "Tema"
```

Leia [README-OPERACIONAL.md](README-OPERACIONAL.md) antes do primeiro piloto e confirme as decisões em [EDITORIAL_DECISIONS_PENDING.md](EDITORIAL_DECISIONS_PENDING.md).

## Garantias centrais

- zero número público sem fonte;
- originais imutáveis;
- crítica proporcional ao que foi documentado;
- conclusão proporcional à evidência;
- status final inicial `AGUARDANDO REVISÃO EDITORIAL`;
- somente o editor humano pode autorizar publicação.
