import streamlit as st
import pandas as pd
import sqlite3
import os
import setup_db
import google.generativeai as genai
from sap_gateway import trigger_sap_integration

# 1. Initialize DB
setup_db.init_db()

# 2. Config
API_KEY = "YOUR_AIzaSy_KEY_HERE" # Replace with your actual key
genai.configure(api_key=API_KEY)

def get_db_connection():
    return sqlite3.connect(setup_db.DB_PATH)

# 3. App UI
st.title("Enterprise Cognitive Product Master Orchestrator")
tabs = st.tabs(["Operations Dashboard", "Data Steward Review", "Audit Trail"])

with tabs[0]:
    st.header("Operations Dashboard")
    conn = get_db_connection()
    df = pd.read_sql('SELECT * FROM materials', conn)
    conn.close()
    st.dataframe(df)
    if st.button("Sync to SAP"):
        trigger_sap_integration("ALL_MATERIALS")

with tabs[1]:
    st.header("Data Steward Review")
    conn = get_db_connection()
    pending_df = pd.read_sql("SELECT * FROM materials WHERE status = 'PENDING'", conn)
    conn.close()
    
    if not pending_df.empty:
        st.dataframe(pending_df)
        
        # User selection
        mat_id = st.selectbox("Select Material", pending_df['Material_ID'].tolist())
        new_val = st.text_input("Enter Remediation Value")
        
        if st.button("Apply and Sync to SAP"):
            # 1. Update local database
            conn = get_db_connection()
            conn.execute("UPDATE materials SET status = 'SYNCED', ai_remediation = ? WHERE Material_ID = ?", (new_val, mat_id))
            conn.commit()
            conn.close()
            
            # 2. Trigger your new gateway
            trigger_sap_integration(mat_id, new_val)
            st.success(f"Changes for {mat_id} queued for SAP!")
            st.rerun() # Refresh to update the tables
    else:
        st.write("All master data is up to date.")

with tabs[2]:
    st.header("Audit Trail")
    conn = get_db_connection()
    audit_df = pd.read_sql('SELECT * FROM audit_log', conn)
    conn.close()
    st.table(audit_df)