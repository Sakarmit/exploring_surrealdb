
from pathlib import Path
import sys
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.surreal_client import SurrealClient

QUERIES = {
    "Query Students": "SELECT * FROM student;",
    "Query Assignments": "SELECT * FROM assignment;",
    "Query Topics": "SELECT * FROM topic;",
}

def format_query_to_dataframe(query_result):
    if not query_result:
        return "No results found."
    
    df = pd.DataFrame(query_result)
    
    if 'id' in df.columns:
        df['id'] = df['id'].astype(str).str.split(':').str[-1]
    
    return df

def run_selected_query(query_name):
    query = QUERIES.get(query_name)
    if query:
        client = SurrealClient()
        try:
            result = client.http_query(query)
            return format_query_to_dataframe(result[0]['result'])
        except Exception as e:
            return f"Error occurred while executing query: {e}"
    else:
        return "Query not found."

def main():
    st.title("Rule Queries Interface")
    with st.container():
        st.write("Select a query from the dropdown below to execute it.")
        selected_query = st.selectbox("Select a query to run:", list(QUERIES.keys()))
        if st.button("Run Query"):
            result = run_selected_query(selected_query)
            st.write(f"Results for: {selected_query}")
            with st.container():
                st.dataframe(result)
        else:
            with st.container():
                st.write("Results will be displayed here after running a query.")

if __name__ == "__main__":
    main()