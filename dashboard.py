import streamlit as st
import pandas as pd
import sqlite3
import os
import setup_db
import google.generativeai as genai
from sap_gateway import trigger_sap_integration

# 1. Initialize Database
setup_db.init_db()

# 2. Config
API_KEY = "AIzaSyDm8DpXYbmAUhhtARNCuIhygGO-z2I5aJo" # Put your actual key here
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('models/gemini-2.5-flash')

# 3. Connection Helper
def get_db_connection():
    return sqlite3.connect(setup_db.DB_PATH)

# 4. App Layout
st.title("Enterprise Cognitive Product Master Orchestrator")
tabs = st.tabs(["Operations Dashboard", "Data Steward Review", "Audit Trail"])

with tabs[0]:
    st.header("Operations Dashboard")
    df = pd.read_sql('SELECT * FROM materials', get_db_connection())
    st.dataframe(df)
    
    if st.button("Sync to SAP"):
        trigger_sap_integration("ALL_MATERIALS")

with tabs[1]:
    st.header("Data Steward Review")
    st.write("AI-driven suggestions for master data remediation will appear here.")

with tabs[2]:
    st.header("Audit Trail")
    audit_df = pd.read_sql('SELECT * FROM audit_log', get_db_connection())
    st.table(audit_df)