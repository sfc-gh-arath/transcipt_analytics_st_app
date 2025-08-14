import streamlit as st
import pandas as pd
import altair as alt
from snowflake.snowpark.context import get_active_session

# --------------------------------------------------------------------------
# Data Loading Functions
# --------------------------------------------------------------------------
def load_element_scores(session):
    """Loads all individual element scores for the detailed scorecard."""
    query = """
    SELECT
        agent,
        element_name,
        element_score as SCORE
    FROM
        qa_scoring_view;        
    """
    try:
        snowpark_df = session.sql(query)
        return snowpark_df.to_pandas()
    except Exception as e:
        st.error(f"Error loading element scores: {e}")
        return pd.DataFrame()

def load_final_scores(session):
    """Loads the final score for each chat to be used in the overview chart."""
    query = """
    SELECT
        agent,
        chat_id,
        qa_score
    FROM
        qa_scoring_summary;
    """
    try:
        snowpark_df = session.sql(query)
        return snowpark_df.to_pandas()
    except Exception as e:
        st.error(f"Error loading final scores: {e}")
        return pd.DataFrame()

# --------------------------------------------------------------------------
# Main Application UI
# --------------------------------------------------------------------------
st.title("🧑‍💻 Individual Agent Scorecard")
st.markdown("Select an agent from the dropdown below to view their performance across all calls and a detailed skill breakdown.")

# Get the active Snowpark session from the notebook environment
session = get_active_session()

# Load the data using both functions
df_elements = load_element_scores(session)
df_final_scores = load_final_scores(session)

if not df_elements.empty and not df_final_scores.empty:
    # Create a list of unique agents for the dropdown
    agent_list = sorted(df_elements['AGENT'].unique())
    selected_agent = st.selectbox("Select an Agent", agent_list)

    # Check if an agent has been selected
    if selected_agent:
        # --- NEW: Chart for all calls by final score ---
        st.header(f"Performance Across All Calls for {selected_agent}")
        agent_calls = df_final_scores[df_final_scores['AGENT'] == selected_agent].copy()

        def get_final_score(qa_score_str):
            try:
                score_dict = eval(qa_score_str)
                return score_dict.get('final', {}).get('final_score', 0)
            except:
                return 0

        agent_calls['FINAL_SCORE'] = agent_calls['QA_SCORE'].apply(get_final_score)

        call_performance_chart = alt.Chart(agent_calls).mark_bar().encode(
            x=alt.X('CHAT_ID:N', title='Chat ID', sort=alt.EncodingSortField(
                field="FINAL_SCORE", op="sum", order='descending'
            )),
            y=alt.Y('FINAL_SCORE:Q', title='Final Score', scale=alt.Scale(domain=[0, 5])),
            tooltip=['CHAT_ID', alt.Tooltip('FINAL_SCORE', format='.2f')]
        ).properties(height=300)
        st.altair_chart(call_performance_chart, use_container_width=True)

        st.markdown("---") # Add a separator

        # --- Existing chart for detailed skill breakdown ---
        st.header(f"Average Skill Performance for {selected_agent}")
        df_agent_scores = df_elements[df_elements['AGENT'] == selected_agent]
        df_agent_summary = df_agent_scores.groupby('ELEMENT_NAME')['SCORE'].mean().reset_index()

        agent_chart = alt.Chart(df_agent_summary).mark_bar().encode(
            x=alt.X('SCORE:Q', title='Average Score', scale=alt.Scale(domain=[0, 5])),
            y=alt.Y('ELEMENT_NAME:N', title='Skill Element', sort='-x'),
            color=alt.Color('SCORE:Q',
                scale=alt.Scale(
                    domain=[0, 3, 4, 5],
                    range=['salmon', 'orange', 'mediumseagreen', 'mediumseagreen']
                ),
                legend=None
            ),
            tooltip=['ELEMENT_NAME', alt.Tooltip('SCORE', title='Average Score', format='.2f')]
        ).properties(height=alt.Step(15))
        st.altair_chart(agent_chart, use_container_width=True)

        with st.expander(f"View Raw Scorecard Data for {selected_agent}"):
            st.dataframe(df_agent_summary.sort_values(by='SCORE', ascending=False))
else:
    st.warning("No score data returned from the query. Cannot generate scorecard.")
