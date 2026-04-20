
from pathlib import Path
import sys
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.surreal_client import SurrealClient

QUERIES = {
    "Retrieve the full names of students who have never attempted any CodeWorkout problems.": {
        "input": [],
        "query": """
            SELECT name AS full_name
            FROM student
            WHERE id NOT IN (SELECT VALUE student_id FROM submission);
        """
    },
    "Retrieve the full names of students who have the highest total number of submission attempts.": {
        "input": [],
        "query": """SELECT student_id,type::record('student',student_id).name as full_name,total_attempts
        FROM (SELECT student_id,
        count() AS total_attempts
        FROM submission
        GROUP BY student_id
        ORDER BY total_attempts DESC);"""
    },
    "Given a Problem ID and a Student SIS Login ID, retrieve the chronological sequence of actions along with their statuses from the student's CodeWorkout interactions.": {
        "input": ["student_id", "problem_id"],
        "query": """
            SELECT server_timestamp, event_type, result, compile_message_type, compile_message
            FROM submission
            WHERE ->submitted_by->(SELECT id FROM student WHERE sis_id = '{student_id}')
            AND problem_id = '{problem_id}'
            ORDER BY server_timestamp ASC;
        """
    },
    "Given a Problem ID, retrieve all learning concepts assessed by that problem": {
        "input": ["problem_id"],
        "query": """
            SELECT VALUE concepts
            FROM cw_problem
            WHERE id = cw_problem:`{problem_id}`;
        """
    }
}

def format_query_to_dataframe(query_result):
    if not query_result:
        return "No results found."
    
    df = pd.DataFrame(query_result)
    
    if 'id' in df.columns:
        df['id'] = df['id'].astype(str).str.split(':').str[-1]
    
    return df

def run_selected_query(query_name, input_values):
    query = QUERIES.get(query_name, {}).get('query') if query_name in QUERIES else None
    if query:
        client = SurrealClient()
        for key, value in input_values.items():
            # Replace placeholders in the query with actual input values
            query = query.replace(f"{{{key}}}", value)
        result = client.http_query(query, False)
        if isinstance(result, list):
            result = result[0]

        if isinstance(result, dict) and (result.get('code', 200) != 200 or result.get('status') != 'OK'):
            st.warning(f"Error executing query: {result.get('information', result.get('result', 'Unknown error'))}")
            return pd.DataFrame()  # Return an empty DataFrame for display purposes
        print(f"Raw query result: {result}")
        return format_query_to_dataframe(result['result'])
    else:
        return "Query not found."

input_list = {}

def main():
    st.title("Rule Queries Interface")
    st.set_page_config(layout="centered")
    with st.container():
        st.write("Select a query from the dropdown below to execute it.")
        selected_query = st.selectbox("Select a query to run:", list(QUERIES.keys()))
        with st.container():
            input_fields = QUERIES[selected_query]['input']
            for i, field in enumerate(input_fields):
                input_list[field] = st.text_input(field)

        if st.button("Run Query"):
            result = run_selected_query(selected_query, input_list)
            st.write(f"Results for: {selected_query}")
            with st.container():
                if isinstance(result, str):
                    st.warning(result)
                else:
                    st.dataframe(result)
        else:
            with st.container():
                st.write("Results will be displayed here after running a query.")

if __name__ == "__main__":
    main()