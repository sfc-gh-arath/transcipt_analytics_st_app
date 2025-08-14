import streamlit as st

Agent_Performance_Dashboard = st.Page("Agent_Performance_Dashboard.py.py", title="Agent_Performance_Dashboard" )
Individual_Agent_Scorecard = st.Page("Individual_Agent_Scorecard.py", title="Individual_Agent_Scorecard" )
Individual_Call_Review_Dashboard = st.Page("Individual_Call_Review_Dashboard.py", title="Individual_Call_Review_Dashboard" )


pg = st.navigation([Agent_Performance_Dashboard, Individual_Agent_Scorecard,Individual_Call_Review_Dashboard])
st.set_page_config(page_title="Call Transcript Analytcis", page_icon=":material/edit:")
pg.run()