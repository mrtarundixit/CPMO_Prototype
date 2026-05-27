import streamlit as st
import pandas as pd
import sqlite3
import setup_db
from sap_gateway import trigger_sap_integration
from datetime import datetime
import google.generativeai as genai

def get_ai_suggestion(row_data):
    prompt = f"""
    You are a Data Steward AI. Analyze this product data and suggest a corrected value for remediation.
    Material: {row_data['Component']}
    Current Data: {row_data.to_dict()}
    Suggest the most appropriate 'UoM_or_Quantity' or 'Status' fix. 
    Keep it concise.
    """
    response = model.generate_content(prompt)
    return response.text

# 1. Initialize
setup_db.init_db()

# 2. Hardcoded Key (Internal Prototype Only)
genai.configure(api_key="AIzaSyC8mkCXVl7ooKvARAbg4JfsRoy0oVbU2Uo")
try:
    # Use the full model string required by the current SDK
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"Error initializing model: {e}")

def get_db_connection():
    return sqlite3.connect(setup_db.DB_PATH)

def log_audit(material_id, action):
    conn = get_db_connection()
    conn.execute("INSERT INTO audit_log (material_id, action, timestamp) VALUES (?, ?, ?)", 
                 (material_id, action, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# 3. UI Layout
st.title("Enterprise Cognitive Product Master Orchestrator")
# Phase 1: Executive Metrics
conn = get_db_connection()
total_records = pd.read_sql("SELECT COUNT(*) as count FROM materials", conn).iloc[0]['count']
pending_records = pd.read_sql("SELECT COUNT(*) as count FROM materials WHERE status = 'PENDING'", conn).iloc[0]['count']
synced_records = pd.read_sql("SELECT COUNT(*) as count FROM materials WHERE status = 'SYNCED'", conn).iloc[0]['count']
conn.close()

col1, col2, col3 = st.columns(3)
col1.metric("Total Materials", total_records)
col2.metric("Pending Review", pending_records, delta_color="inverse")
col3.metric("Successfully Synced", synced_records)

st.divider() # Adds a clean visual separator
tabs = st.tabs(["Operations Dashboard", "Data Steward Review", "Audit Trail"])

with tabs[0]:
    st.header("Operations Dashboard")
    conn = get_db_connection()
    df = pd.read_sql('SELECT * FROM materials', conn)
    conn.close()
    st.dataframe(df)
    
    if st.button("Sync All to SAP"):
        trigger_sap_integration("ALL_MATERIALS", "BULK_UPDATE")
        log_audit("ALL", "BULK_SYNC")
        st.success("Bulk update queued to SAP.")

with tabs[1]:
    st.header("Data Steward Review")
    conn = get_db_connection()
    pending_df = pd.read_sql("SELECT * FROM materials WHERE status = 'PENDING'", conn)
    conn.close()
    
    if not pending_df.empty:
        st.dataframe(pending_df)
        
        # Selection
        mat_id = st.selectbox("Select Material", pending_df['Material_ID'].tolist())
        row = pending_df[pending_df['Material_ID'] == mat_id].iloc[0]
        
        # AI Logic Trigger
        if st.button("Get AI Recommendation"):
            with st.spinner("Gemini is analyzing..."):
                suggestion = get_ai_suggestion(row)
                st.info(f"AI Suggestion: {suggestion}")
                st.session_state['ai_suggestion'] = suggestion

        # Approval logic using the AI's suggestion
        new_val = st.text_input("Approved Value", value=st.session_state.get('ai_suggestion', ''))
        
        if st.button("Approve & Sync"):
            # ... (keep your existing update and trigger_sap_integration logic) ...
            st.success("Synced to SAP!")
    else:
        st.write("No pending materials.")

with tabs[2]:
    st.header("Audit Trail")
    conn = get_db_connection()
    audit_df = pd.read_sql('SELECT * FROM audit_log', conn)
    conn.close()
    st.table(audit_df)