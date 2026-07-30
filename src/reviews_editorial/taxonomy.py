"""Taxonomia editorial inicial, hierárquica e extensível do registro central."""

from __future__ import annotations

from typing import Final


DOCUMENT_TYPES: Final[tuple[tuple[str, str, str | None, str], ...]] = (
    ("type.source", "Fonte", None, "Material usado como evidência ou contexto."),
    ("type.primary_source", "Fonte primária", "type.source", "Fonte original da evidência."),
    ("type.scientific_article", "Artigo científico", "type.primary_source", "Artigo científico."),
    ("type.clinical_guideline", "Diretriz clínica", "type.primary_source", "Diretriz ou guideline clínico."),
    ("type.systematic_review", "Revisão sistemática", "type.primary_source", "Revisão sistemática."),
    ("type.meta_analysis", "Metanálise", "type.systematic_review", "Metanálise."),
    ("type.randomized_trial", "Ensaio clínico", "type.scientific_article", "Ensaio clínico."),
    ("type.observational_study", "Estudo observacional", "type.scientific_article", "Estudo observacional."),
    ("type.protocol", "Protocolo", "type.primary_source", "Protocolo de estudo ou editorial."),
    ("type.study_registry", "Registro de estudo", "type.primary_source", "Registro de estudo."),
    ("type.supplement", "Material suplementar", "type.source", "Anexo ou suplemento de uma fonte."),
    ("type.secondary_source", "Fonte secundária", "type.source", "Fonte contextual ou secundária."),
    ("type.structured_extraction", "Extração estruturada", None, "Extração de evidências."),
    ("type.extraction_sheet", "Planilha de extração", "type.structured_extraction", "Planilha estruturada."),
    ("type.methodological_analysis", "Análise metodológica", None, "Análise de métodos e confiabilidade."),
    ("type.critical_analysis", "Análise crítica", "type.methodological_analysis", "Interpretação crítica."),
    ("type.clinical_answer", "Resposta clínica", None, "Resposta editorial a uma pergunta clínica."),
    ("type.editorial_draft", "Rascunho editorial", None, "Texto editorial ainda não aprovado."),
    ("type.methodological_review", "Revisão metodológica", None, "Revisão de conteúdo metodológico."),
    ("type.editorial_review", "Revisão editorial", None, "Revisão de linguagem, estrutura e edição."),
    ("type.review_comment", "Comentário de revisão", None, "Comentário vinculado a uma revisão."),
    ("type.change_request", "Solicitação de alteração", None, "Alteração solicitada."),
    ("type.audit", "Auditoria", None, "Auditoria factual, numérica, metodológica ou editorial."),
    ("type.publication_version", "Versão para publicação", None, "Versão preparada para publicação."),
    ("type.published_material", "Material final publicado", None, "Material efetivamente publicado."),
    ("type.post_publication_correction", "Correção pós-publicação", None, "Correção de publicação."),
    ("type.template", "Modelo", None, "Modelo reutilizável."),
    ("type.prompt", "Prompt", None, "Instrução de agente ou geração."),
    ("type.transcript", "Transcrição", None, "Transcrição de reunião ou entrevista."),
    ("type.recording", "Gravação", None, "Áudio ou vídeo integral."),
    ("type.visual_asset", "Ativo visual", None, "Imagem ou ativo gráfico."),
    ("type.design_document", "Documento de design", None, "Regras ou documentação visual."),
    ("type.editorial_map", "Mapa editorial", None, "Organização de edições ou território editorial."),
    ("type.topic_suggestion", "Sugestão de tema", None, "Pauta ou sugestão ainda não produzida."),
    ("type.supporting_material", "Material de apoio", None, "Material auxiliar."),
    ("type.administrative", "Documento administrativo", None, "Documento operacional ou administrativo."),
    ("type.editorial_learning_record", "Registro de aprendizado editorial", None, "Comparação ou memória de uma edição."),
    ("type.unknown", "Desconhecido", None, "Tipo ainda não confirmado."),
)

EDITORIAL_FUNCTIONS: Final[tuple[tuple[str, str, str | None, str], ...]] = (
    ("function.source", "Fonte", None, "Material consultado."),
    ("function.main_source", "Fonte principal", "function.source", "Fonte central da edição."),
    ("function.supporting_source", "Fonte de apoio", "function.source", "Fonte complementar."),
    ("function.extraction", "Extração", None, "Estrutura evidências ou dados."),
    ("function.analysis", "Análise", None, "Interpreta criticamente a evidência."),
    ("function.draft", "Rascunho", None, "Texto em elaboração."),
    ("function.review", "Revisão", None, "Revisa uma versão anterior."),
    ("function.audit", "Auditoria", None, "Verifica a integridade de uma versão."),
    ("function.final", "Final", None, "Resultado editorial final ainda não necessariamente publicado."),
    ("function.published", "Publicado", None, "Resultado efetivamente publicado."),
    ("function.derived", "Derivado", None, "Produto derivado de outro documento."),
    ("function.template", "Modelo", None, "Base reutilizável."),
    ("function.prompt", "Prompt", None, "Instrução operacional."),
    ("function.learning", "Aprendizado", None, "Registra mudança, erro, decisão ou lição."),
    ("function.organization", "Organização editorial", None, "Organiza o acervo ou fluxo."),
    ("function.unclassified", "Não classificado", None, "Função ainda não confirmada."),
)

STAGES: Final[tuple[tuple[str, str, str | None, str], ...]] = (
    ("stage.not_started", "Não iniciado", None, "Ainda não entrou em produção."),
    ("stage.material_received", "Material recebido", None, "Material recebido e preservado."),
    ("stage.triage", "Em triagem", None, "Em triagem editorial."),
    ("stage.awaiting_classification", "Aguardando classificação", None, "Classificação humana pendente."),
    ("stage.drafting", "Em elaboração", None, "Em elaboração."),
    ("stage.awaiting_review", "Aguardando revisão", None, "Aguardando revisor."),
    ("stage.methodological_review", "Em revisão metodológica", None, "Sob revisão metodológica."),
    ("stage.editorial_review", "Em revisão editorial", None, "Sob revisão editorial."),
    ("stage.changes_requested", "Alterações solicitadas", None, "Possui alterações solicitadas."),
    ("stage.corrections", "Correções em andamento", None, "Correções em execução."),
    ("stage.awaiting_rereview", "Aguardando nova revisão", None, "Aguardando nova rodada."),
    ("stage.awaiting_audit", "Aguardando auditoria", None, "Aguardando auditoria."),
    ("stage.audit", "Em auditoria", None, "Sob auditoria."),
    ("stage.approved", "Aprovado", None, "Aprovado por humano autorizado."),
    ("stage.ready_to_publish", "Pronto para publicação", None, "Aprovado e preparado para publicação."),
    ("stage.published", "Publicado", None, "Publicado."),
    ("stage.post_publication_correction", "Correção pós-publicação", None, "Correção após publicação."),
    ("stage.superseded", "Substituído", None, "Substituído por versão posterior."),
    ("stage.archived", "Arquivado", None, "Arquivado."),
    ("stage.abandoned", "Abandonado", None, "Produção abandonada."),
    ("stage.rejected", "Rejeitado", None, "Rejeitado."),
)

STATUSES: Final[tuple[tuple[str, str, str | None, str], ...]] = (
    ("status.unverified", "Não verificado", None, "Conteúdo ou classificação não confirmados."),
    ("status.source_verified", "Fonte verificada", None, "Fonte conferida."),
    ("status.preliminary", "Preliminar", None, "Versão preliminar."),
    ("status.awaiting_review", "Aguardando revisão", None, "Revisão pendente."),
    ("status.changes_requested", "Alterações solicitadas", None, "Ainda não incorpora todas as correções."),
    ("status.approved", "Aprovado", None, "Aprovado por humano autorizado."),
    ("status.ready_to_publish", "Pronto para publicação", None, "Aprovado para publicação."),
    ("status.published", "Publicado", None, "Corresponde a uma publicação registrada."),
    ("status.superseded", "Substituído", None, "Não é a versão corrente."),
    ("status.archived", "Arquivado", None, "Preservado apenas no histórico."),
    ("status.rejected", "Rejeitado", None, "Não utilizar como exemplo positivo."),
    ("status.known_error", "Erro conhecido", None, "Possui erro conhecido."),
    ("status.do_not_use", "Não usar como referência", None, "Uso normativo bloqueado."),
    ("status.classification_pending", "Classificação pendente", None, "Aguardando confirmação humana."),
)

MEMORY_CATEGORIES: Final[tuple[tuple[str, str, str | None, str], ...]] = (
    ("memory.good_example", "Bom exemplo", None, "Exemplo positivo confirmado."),
    ("memory.bad_example", "Mau exemplo", None, "Contraexemplo explicitamente identificado."),
    ("memory.known_error", "Erro conhecido", None, "Erro preservado para prevenção."),
    ("memory.exception", "Exceção", None, "Exceção a uma regra."),
    ("memory.general_rule", "Regra geral", None, "Regra aprovada."),
    ("memory.style_preference", "Preferência de estilo", None, "Preferência editorial aprovada."),
    ("memory.methodological_principle", "Princípio metodológico", None, "Princípio metodológico aprovado."),
    ("memory.interpretation_alert", "Alerta de interpretação", None, "Alerta para evitar inferência indevida."),
    ("memory.historical_artifact", "Artefato histórico", None, "Documento ou versão preservada sem força normativa."),
)


TAXONOMY_VOCABULARIES: Final[dict[str, tuple[tuple[str, str, str | None, str], ...]]] = {
    "document_type": DOCUMENT_TYPES,
    "editorial_function": EDITORIAL_FUNCTIONS,
    "stage": STAGES,
    "status": STATUSES,
    "memory_category": MEMORY_CATEGORIES,
}


def iter_taxonomy_terms():
    for vocabulary, terms in TAXONOMY_VOCABULARIES.items():
        for term_id, label, parent_id, description in terms:
            yield {
                "term_id": term_id,
                "vocabulary": vocabulary,
                "label": label,
                "parent_id": parent_id,
                "description": description,
            }
