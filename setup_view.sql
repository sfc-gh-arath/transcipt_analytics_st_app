create or replace view SCORING_VIEW
as
WITH llm AS (
  SELECT
      q.chat_id,
      q.agent,
      q.transcript,
      q.sf_case,
      q.kb_articles,
      q.qa_score:"agent_persona_summary"::string AS agent_persona_summary,
      e.value:"element_id"::string               AS element_id,
      e.value:"name"::string                     AS element_name,        -- col1
      e.value:"score"::number                    AS llm_score,           -- col2
      e.value:"rationale"::string                AS element_rationale,
      e.value:"insufficient_evidence"::boolean   AS insufficient_evidence,
      e.value:"evidence"                         AS evidence             -- array/VARIANT
  FROM qa_scoring_summary q,
       LATERAL FLATTEN(input => q.qa_score:"elements") e
)
SELECT
    llm.element_name                             AS element_name,
    llm.element_id                               AS element_id,    
    llm.llm_score                                AS llm_score,
    TRY_TO_NUMBER(h.score)                       AS human_score,
    (llm.llm_score = TRY_TO_NUMBER(h.score))     AS scores_match,
     TRY_TO_NUMBER(h.possible_score)             AS possible_max_score,
    llm.insufficient_evidence                    AS insufficient_evidence,
    llm.element_rationale                        AS rationale,
    llm.evidence                                 AS evidence,
    llm.agent                                    AS agent,
    llm.chat_id                                  AS chat_id,
    llm.agent_persona_summary                    AS agent_persona_summary,
    llm.transcript                               AS transcript,
    llm.kb_articles
FROM llm
LEFT JOIN lulu_qm_scores h
  ON h.interaction_id = llm.sf_case
 AND TO_VARCHAR(h.element_id) = llm.element_id
ORDER BY llm.chat_id, llm.element_id ASC;
