# Contratos de proveniência

## Inventário de documentos

normalized/document-inventory.md deve conter uma linha por entrada com:

| Campo | Regra |
| --- | --- |
| source_id | estável e idêntico ao registrado no job |
| identidade esperada e conferida | título, autor/instituição, ano, tipo e versão |
| localização | origem e cópia de trabalho, sem modificar a origem |
| formato e acesso | PDF, DOCX, HTML, registro etc.; completo, parcial ou ilegível |
| papel proposto | papel inicial, a confirmar em source-roles.json |
| relação com a pauta | principal, suplemento, protocolo, correção, contexto ou excluído |
| hash/versão | use o hash disponível no job ou informe a impossibilidade |
| revisão humana | revisor, data e resultado de legibilidade |
| pendência | material necessário e efeito do seu não acesso |

“Arquivo recebido” não é valor aceitável para identidade conferida.

## Papéis de fonte

normalized/source-roles.json valida contra source-roles.schema.json e usa:

    {
      "job_id": "JOB-2026-001",
      "sources": [
        {
          "source_id": "DOC-ARTIGO",
          "source_role": "primary-evidence",
          "authority_rank": 1,
          "location": "input/artigo.pdf",
          "rationale": "Relatório completo do resultado analisado."
        }
      ]
    }

authority_rank ordena fontes dentro do papel; ele não faz uma fonte de estilo
virar evidência científica.

## Mapa de fontes e claims

extraction/source-map.md deve ter uma seção por claim liberado:

    claim_id: CLM-primary-01
    status: verified
    source_id/document_id: DOC-ARTIGO
    source_role: primary-evidence
    version_or_hash: <valor disponível>
    locator: p. 7, Tabela 2, desfecho primário
    source_excerpt: <trecho curto conferido>
    downstream_use: resultado principal; pode entrar no brief

Se o claim for cálculo derivado, acrescente entradas, fórmula, unidade e a frase
“cálculo do sistema”. Se houver mais de uma fonte, mostre qual sustenta qual
parte da afirmação; não agrupe citações vagas.

## Estados de autorização

| Estado | Uso público |
| --- | --- |
| verified | permitido após correspondência semântica conferida |
| partially-verified | bloqueado; explicar parte não confirmada |
| unsupported | bloqueado |
| ambiguous | bloqueado até desambiguação |
| divergent | bloqueado até registro e decisão editorial |
| extrapolative | bloqueado ou reclassificado como inferência limitada |
| pending | bloqueado |

Cada claim público requer documento, localizador, excerto e proveniência. O
schema também exige calculation_method para derived-calculation.

## Discrepâncias e ausência

Registre em analysis/critical-issues.md:

    elemento: taxa de evento
    fontes: DOC-ARTIGO p. 6 / DOC-SUPL tabela S3
    valores: 12/100 versus 14/100
    consequência: altera a estimativa absoluta reportável
    status: bloqueia o claim numérico até reconciliação
    ação: conferir população, tempo e errata

Use a frase padronizada de ausência ou ambiguidade somente após registrar o
escopo da procura. Falta de relato não permite afirmar falta de condução.

## Verificação executável

Os contratos estruturados existentes são verificados por:

    python scripts/validate_schema.py <job_dir>/normalized/source-roles.json --schema source-roles
    python scripts/verify_numbers.py <job_dir>
    python scripts/build_claim_ledger.py <job_dir>
    python scripts/validate_provenance.py <job_dir>/extraction/claim-ledger.json <job_dir>/normalized/source-roles.json --output <job_dir>/extraction/claim-provenance-report.json

Esses comandos não substituem a leitura do excerto nem a conferência visual das
tabelas.

claim-provenance-report.json valida contra
schemas/claim-provenance-report.schema.json e informa valid, claims_checked,
public_claims_checked, issues e boundary. O relatório só aprova a estrutura da
cadeia: o revisor continua responsável por conferir que o excerto sustenta
semanticamente a frase.
