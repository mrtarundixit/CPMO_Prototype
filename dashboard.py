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
genai.configure(api_key="AIzaSyDm8DpXYbmAUhhtARNCuIhygGO-z2I5aJo")
model = genai.GenerativeModel('gemini-2.5-flash')

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
        mat_id = st.selectbox("Select Material", pending_df['Material_ID'].tolist())
        new_val = st.text_input("Enter Approved Value")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Approve & Sync"):
                if new_val:
                    conn = get_db_connection()
                    conn.execute("UPDATE materials SET status = 'SYNCED', ai_remediation = ? WHERE Material_ID = ?", (new_val, mat_id))
                    conn.commit()
                    conn.close()
                    trigger_sap_integration(mat_id, new_val)
                    log_audit(mat_id, "APPROVED_AND_SYNCED")
                    st.success(f"Material {mat_id} updated.")
                    st.rerun()
        with c2:
            if st.button("Reject"):
                log_audit(mat_id, "REJECTED")
                st.error("Change rejected.")
                st.rerun()
    else:
        st.write("No pending materials.")

with tabs[2]:
    st.header("Audit Trail")
    conn = get_db_connection()
    audit_df = pd.read_sql('SELECT * FROM audit_log', conn)
    conn.close()
    st.table(audit_df)