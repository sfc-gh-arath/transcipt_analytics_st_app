import streamlit as st
import pandas as pd
from snowflake.snowpark.context import get_active_session

# --------------------------------------------------------------------------
# Data Loading Function
# --------------------------------------------------------------------------s
def load_call_data(session):
    """Loads all necessary call data, including agent, chat_id, transcript, and the full QA score object."""
    query = """
    SELECT
        agent,
        chat_id,
        TRANSCRIPT,
        qa_score
    FROM
        qa_scoring_summary;
    """
    try:
        snowpark_df = session.sql(query)
        # The qa_score column is loaded as a string, so we'll parse it later
        return snowpark_df.to_pandas()
    except Exception as e:
        st.error(f"Error loading call data: {e}")
        return pd.DataFrame()

# --------------------------------------------------------------------------
# Main Application UI
# --------------------------------------------------------------------------
st.title("📞 Individual Call Review Dashboard")
st.markdown("Select an agent and a specific Chat ID to view the detailed QA analysis, transcript, and scorecard.")

# Get the active Snowpark session
session = get_active_session()

# Load all call data
df_calls = load_call_data(session)

if not df_calls.empty:
    # --- Dropdowns for Agent and Call Selection ---
    agent_list = sorted(df_calls['AGENT'].unique())
    selected_agent = st.selectbox("Step 1: Select an Agent", agent_list)

    if selected_agent:
        # Filter calls for the selected agent
        agent_calls = df_calls[df_calls['AGENT'] == selected_agent]
        call_list = sorted(agent_calls['CHAT_ID'].unique())
        selected_call = st.selectbox("Step 2: Select a Chat ID to Review", call_list)

        if selected_call:
            # Get the data for the selected call
            call_data = agent_calls[agent_calls['CHAT_ID'] == selected_call].iloc[0]
            
            # The qa_score is loaded as a string, so we need to parse it into a dictionary
            # We use `eval()` here, which is safe in this context because the data is coming
            # from our trusted Snowflake database.
            try:
                qa_score_dict = eval(call_data['QA_SCORE'])
            except:
                st.error("Could not parse the QA score data for this call.")
                st.stop()


            st.header(f"Analysis for Chat ID: {selected_call}")

            # --- Display Call Summary ---
            st.subheader("Call Summary")
            st.write(qa_score_dict.get('agent_persona_summary', 'No summary available.'))
            final_score = qa_score_dict.get('final', {}).get('final_score', 0)
            st.metric(label="Final Score", value=f"{final_score:.2f}")


            # --- Display Transcript ---
            with st.expander("View Full Call Transcript"):
                st.text(call_data['TRANSCRIPT'])


            # --- Display Detailed Scorecard ---
            st.subheader("Detailed Scorecard")
            scorecard = qa_score_dict.get('categories', [])

            if scorecard:
                for category in scorecard:
                    category_name = category.get('name', 'Unnamed Category')
                    elements = category.get('elements', [])
                    
                    # Calculate the average score for the category
                    if elements:
                        category_score = sum(el.get('score', 0) for el in elements) / len(elements)
                    else:
                        category_score = 0
                    
                    # Display category header with its average score
                    st.markdown(f"**{category_name}** (Average Score: {category_score:.2f})")
                    
                    # Create a DataFrame for the elements in this category
                    df_elements = pd.DataFrame(elements)
                    st.dataframe(df_elements[['name', 'score', 'justification']], use_container_width=True)
            else:
                st.warning("No scorecard data found for this call.")

else:
    st.warning("No call data returned from the query. Cannot generate dashboard.")
