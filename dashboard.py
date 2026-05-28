import streamlit as st
import pandas as pd
import sqlite3
import setup_db
from sap_gateway import trigger_sap_integration
from datetime import datetime
import google.generativeai as genai
from prompts import MDM_STEWARD_PROMPT
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from google.api_core import exceptions

# 1. Initialize DB and Model
setup_db.init_db()

# REPLACE WITH A NEW, SECURE API KEY
genai.configure(api_key="AIzaSyAdTQnsNY7nvUH8Hh0_KViS5RZhq6rA_8g")
model_name = "gemini-1.5-flash"

try:
    model = genai.GenerativeModel(model_name)
except Exception as e:
    st.error(f"Failed to load model {model_name}: {e}")

# 2. Resilient API Logic with Exponential Back-off
@retry(
    wait=wait_exponential(multiplier=1, min=2, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(exceptions.ResourceExhausted)
)
def call_gemini_with_retry(prompt):
    return model.generate_content(prompt)

def get_ai_suggestion(row_data):
    # Caching: If we already have a suggestion in session, don't call the API
    cache_key = f"suggestion_{row_data['Material_ID']}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    
    try:
        prompt = MDM_STEWARD_PROMPT.format(
            component=row_data['Component'], 
            data_dict=row_data.to_dict()
        )
        response = call_gemini_with_retry(prompt)
        
        # Save to cache
        st.session_state[cache_key] = response.text
        return response.text
        
    except Exception as e:
        return f"ERROR: {str(e)}"

# 3. Helper Functions
def get_db_connection():
    return sqlite3.connect(setup_db.DB_PATH)

def log_audit(material_id, action):
    conn = get_db_connection()
    conn.execute("INSERT INTO audit_log (material_id, action, timestamp) VALUES (?, ?, ?)", 
                 (material_id, action, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# 4. UI Layout
st.title("Enterprise Cognitive Product Master Orchestrator")

# Metrics
conn = get_db_connection()
total_records = pd.read_sql("SELECT COUNT(*) as count FROM materials", conn).iloc[0]['count']
pending_records = pd.read_sql("SELECT COUNT(*) as count FROM materials WHERE status = 'PENDING'", conn).iloc[0]['count']
synced_records = pd.read_sql("SELECT COUNT(*) as count FROM materials WHERE status = 'SYNCED'", conn).iloc[0]['count']
conn.close()

col1, col2, col3 = st.columns(3)
col1.metric("Total Materials", total_records)
col2.metric("Pending Review", pending_records)
col3.metric("Successfully Synced", synced_records)

st.divider()
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
        mat_id = st.selectbox("Select Material", pending_df['Material_ID'].tolist())
        row = pending_df[pending_df['Material_ID'] == mat_id].iloc[0]
        st.dataframe(row.to_frame())
        
        # AI Logic
        if st.button("Get AI Recommendation"):
            with st.spinner("Gemini is consulting..."):
                suggestion = get_ai_suggestion(row)
                st.info(f"AI Suggestion: {suggestion}")

        new_val = st.text_input("Approved Value")
        
        # Action Buttons
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("Approve & Sync"):
                trigger_sap_integration(mat_id, new_val)
                log_audit(mat_id, "APPROVED_AND_SYNCED")
                conn = get_db_connection()
                conn.execute("UPDATE materials SET status = 'SYNCED' WHERE Material_ID = ?", (mat_id,))
                conn.commit()
                conn.close()
                st.success(f"Material {mat_id} synced!")
                st.rerun()
                
        with col_btn2:
            # NEW: Reject Functionality
            if st.button("Reject Material"):
                log_audit(mat_id, "REJECTED")
                conn = get_db_connection()
                conn.execute("UPDATE materials SET status = 'REJECTED' WHERE Material_ID = ?", (mat_id,))
                conn.commit()
                conn.close()
                st.error(f"Material {mat_id} has been rejected.")
                st.rerun()
    else:
        st.write("No pending materials.")

with tabs[2]:
    st.header("Audit Trail")
    conn = get_db_connection()
    audit_df = pd.read_sql('SELECT * FROM audit_log', conn)
    conn.close()
    st.table(audit_df)