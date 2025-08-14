create or replace view QA_SCORING_VIEW
as
SELECT
    t.agent,
    t.chat_id,
    PARSE_JSON(t.qa_score):agent_persona_summary::VARCHAR as agent_persona_summary,
    PARSE_JSON(t.qa_score):final.final_score::FLOAT as final_score,
    PARSE_JSON(t.qa_score):final.explanation::VARCHAR as final_explanation,
    c.value:name::VARCHAR as category_name,
    c.value:weight::FLOAT as category_weight,
    c.value:base_score::FLOAT as category_base_score,
    c.value:adjusted_score::FLOAT as category_adjusted_score,
    e.value:name::VARCHAR as element_name,
    e.value:score::NUMBER as element_score,
    e.value:max_score::NUMBER as element_max_score,
    e.value:rationale::VARCHAR as element_rationale,
    e.value:insufficient_evidence::BOOLEAN as insufficient_evidence
FROM DEMO_DB.CRM.qa_scoring_summary t,
LATERAL FLATTEN(input => t.qa_score:categories) c,
LATERAL FLATTEN(input => c.value:elements) e;