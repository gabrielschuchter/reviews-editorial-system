# Operação do sistema editorial

## 1. Preparar as fontes

1. Mantenha os originais fora de `jobs/` ou copie-os para `jobs/<id>/input/` sem alterar os arquivos-fonte.
2. Registre a pasta ou os arquivos com `scripts/create_job.py`.
3. Execute `scripts/normalize_documents.py`.
4. Revise `normalized/missing-materials.md`, `page-map.json`, `table-map.json` e `figure-map.json`.
5. Preencha cada item de `normalized/manual-document-review.json`; um nome de revisor não substitui as confirmações.
6. Só então use `scripts/validate_job.py <job-dir> --confirm-documents "Nome"`.

Não avance se o artigo completo, o desfecho primário, o comparador, a direção do efeito ou as tabelas essenciais não puderem ser confirmados.

## 2. Extrair e verificar

1. Preencha ou gere os arquivos estruturados em `extraction/`.
2. Execute `scripts/extract_evidence.py` para validar o pacote mínimo.
3. Execute `scripts/verify_numbers.py` para comparar valores estruturados e registrar divergências.
4. Execute `scripts/build_claim_ledger.py` antes de qualquer texto público.

Os contratos unitários de estudo, população, intervenção, desfecho, estimativa e demais artefatos podem ser verificados diretamente:

```powershell
python scripts/validate_schema.py caminho\population.json --schema population
```

Use as expressões padronizadas quando necessário:

- `Informação não localizada nos materiais consultados.`
- `Informação ambígua ou insuficientemente descrita no material disponível.`

## 3. Analisar e planejar

1. Registre o desenho em `analysis/study-classification.json`.
2. Produza `analysis/methodological-review.json`, `inference-boundaries.md` e `critical-issues.md`.
3. Registre a busca externa com data; se ela não ocorreu, declare isso literalmente.
4. Use `scripts/edition_router.py` e documente a recomendação ou override.
5. Use `scripts/select_exemplars.py`; não carregue o corpus inteiro.

## 4. Redigir e auditar

Redija apenas com o pacote validado, o plano editorial e os exemplares selecionados. Depois execute, nesta ordem:

1. auditoria factual;
2. auditoria estatística e metodológica;
3. revisão estrutural;
4. revisão de estilo e anti-IA;
5. revisão de coerência;
6. auditoria final.

`scripts/audit_draft.py` bloqueia ledger inválido, claim explicitamente proibida e número sem correspondência exata em claim público verificado. Ele não prova, sozinho, que toda frase factual qualitativa é semanticamente sustentada. A cobertura completa exige claim ledger, mapa de fontes e auditoria adversarial/humana registrada em `audits/factual-audit.json`.

## 5. Exportar e revisar

1. Gere `final/candidate.md` e `final/editorial-report.md`.
2. Gere o DOCX com `scripts/export_docx.py`; para destino Google Docs, use o preset nativo documentado.
3. Inspecione visualmente o DOCX renderizado antes de entregar.
4. Prepare `drive-transfer.json` com `scripts/publish_to_drive.py`, informando o job, o destino e a lista explícita de pastas de produção autorizadas. O script não faz upload.
5. Use o conector do Drive somente na pasta de produção autorizada e nunca sobrescreva o arquivo histórico.
6. Mantenha o status `AGUARDANDO REVISÃO EDITORIAL` até decisão humana.

## 6. Incorporar feedback

Compare candidata e versão revisada com `scripts/compare_versions.py`. Classifique as mudanças com `scripts/incorporate_feedback.py`. Uma regra candidata permanece pendente até ter justificativa, exemplo antes/depois, teste de regressão e aprovação do editor.

O teste de regressão deve apontar para um arquivo existente dentro do repositório e declarar `passed_existing_cases: true`; isso registra evidência, mas não modifica regras automaticamente.

## Registro central

O registro local acompanha automaticamente a criação e o avanço dos jobs. Para migrar jobs anteriores e auditar a trilha completa:

```powershell
python scripts/editorial_registry.py sync-all-jobs jobs
python scripts/editorial_registry.py dashboard
python scripts/editorial_registry.py validate-registry
```

Consulte `docs/EDITORIAL_REGISTRY.md` para versões, eventos, linhagem, memória, classificação, saídas de agentes e arquivo privado do Drive.

## Comandos de verificação

```powershell
python -m unittest discover -s tests -v
python scripts/run_evals.py
python scripts/run_checks.py
python scripts/inventory_corpus.py --help
python scripts/create_job.py --help
```

Os arquivos `.yml` gerados pelo núcleo usam o subconjunto JSON de YAML 1.2. Isso permite leitura determinística apenas com a biblioteca padrão do Python.
