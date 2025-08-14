import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session

# --------------------------------------------------------------------------
# Data Loading Functions
# --------------------------------------------------------------------------
# Caching prevents queries from re-running every time a user interacts
# with the app, which saves time and compute credits.

def load_overall_scores(session):
    """Loads the average final score for each agent."""
    query = """
    SELECT
        agent,
        AVG(final_score) AS average_final_score
    FROM
        qa_scoring_view
    GROUP BY
        agent;
    """
    try:
        snowpark_df = session.sql(query)
        return snowpark_df.to_pandas()
    except Exception as e:
        st.error(f"Error loading overall scores: {e}")
        return pd.DataFrame()

def load_category_scores(session):
    """Loads the average score for each agent per category for the heatmap."""
    query = """
    SELECT
        agent,
        category_name AS category,
        AVG(category_adjusted_score) AS average_score
    FROM
        qa_scoring_view
    GROUP BY
        agent,
        category;        
    """
    try:
        snowpark_df = session.sql(query)
        return snowpark_df.to_pandas()
    except Exception as e:
        st.error(f"Error loading category scores: {e}")
        return pd.DataFrame()

def load_all_element_scores(session):
    """Loads all individual element scores for every agent and chat."""
    query = """
    SELECT
        agent,
        element_name,
        element_score
    FROM
        qa_scoring_view;        
    """
    try:
        snowpark_df = session.sql(query)
        return snowpark_df.to_pandas()
    except Exception as e:
        st.error(f"Error loading all element scores: {e}")
        return pd.DataFrame()

# --------------------------------------------------------------------------
# Main Application UI
# --------------------------------------------------------------------------
st.title("📊 Agent Performance Dashboard")
st.markdown("This dashboard displays the average quality assurance score for each customer service agent.")

# Get the active Snowpark session from the notebook environment
session = get_active_session()

# --- Overall Performance Bar Chart ---
st.header("Average Final Score by Agent")
df_overall = load_overall_scores(session)

if not df_overall.empty:
    bar_chart = alt.Chart(df_overall).mark_bar().encode(
        x=alt.X('AGENT', sort=alt.EncodingSortField(field="AVERAGE_FINAL_SCORE", op="sum", order='descending')),
        y=alt.Y('AVERAGE_FINAL_SCORE', title='Average Final Score'),
        tooltip=['AGENT', 'AVERAGE_FINAL_SCORE']
    ).properties(height=500)
    st.altair_chart(bar_chart, use_container_width=True)
else:
    st.warning("No overall score data returned from the query.")

# --- Category Performance Heatmap ---
st.header("Heatmap of Average Score by Category")
df_heatmap = load_category_scores(session)

if not df_heatmap.empty:
    heatmap = alt.Chart(df_heatmap).mark_rect().encode(
        x=alt.X('AGENT:O', title='Agent'),
        y=alt.Y('CATEGORY:O', title='Category', sort='-x'),
        color=alt.Color('AVERAGE_SCORE:Q', scale=alt.Scale(scheme='viridis'), title='Avg. Score'),
        tooltip=[alt.Tooltip('AGENT', title='Agent'), alt.Tooltip('CATEGORY', title='Category'), alt.Tooltip('AVERAGE_SCORE', title='Average Score', format='.2f')]
    ).properties(height=alt.Step(20))
    st.altair_chart(heatmap, use_container_width=True)
else:
    st.warning("No category score data returned from the query.")

# --- Load data for the new charts ---
df_elements = load_all_element_scores(session)

if not df_elements.empty:
    # --- ANALYSIS 1: Overall Skill Gaps (Team-Wide) ---
    st.header("Overall Skill Gaps (Team-Wide)")
    df_skill_gaps = df_elements.groupby('ELEMENT_NAME')['SCORE'].mean().reset_index()

    skill_gap_chart = alt.Chart(df_skill_gaps).mark_bar().encode(
        x=alt.X('SCORE:Q', title='Average Score Across All Agents'),
        y=alt.Y('ELEMENT_NAME:N', title='Skill Element', sort='-x'),
        tooltip=['ELEMENT_NAME', alt.Tooltip('SCORE', title='Average Score', format='.2f')]
    ).properties(height=alt.Step(15))
    st.altair_chart(skill_gap_chart, use_container_width=True)
    with st.expander("View Skill Gap Raw Data"):
        st.dataframe(df_skill_gaps.sort_values(by='SCORE', ascending=False))

else:
    st.warning("No element-level score data returned from the query. Cannot generate additional analyses.")
