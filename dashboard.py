import streamlit as st
import pandas as pd
import sqlite3
import google.generativeai as genai
from sap_gateway import trigger_sap_integration # Importing our new gateway

# 1. Config
genai.configure(api_key='AIzaSyDm8DpXYbmAUhhtARNCuIhygGO-z2I5aJo')
model = genai.GenerativeModel('models/gemini-2.5-flash')
try:
    model = genai.GenerativeModel('models/gemini-2.5-flash')
except Exception as e:
    st.error(f"Could not load model {'models/gemini-2.5-flash'}. Check your available models.")

# 2. Database Connection
def get_db_connection():
    return sqlite3.connect('cpmo.db')

def log_audit(material_id, action):
    conn = get_db_connection()
    conn.execute("INSERT INTO audit_log (material_id, action, timestamp) VALUES (?, ?, ?)", 
                 (material_id, action, pd.Timestamp.now()))
    conn.commit()
    conn.close()

# 3. Streamlit UI
st.set_page_config(page_title="Enterprise CPD Orchestrator", layout="wide")
st.title("🌐 Enterprise Cognitive Product Master Orchestrator")

tabs = st.tabs(["📊 Operations Dashboard", "✅ Data Steward Review", "📜 Audit Trail"])

with tabs[0]: # Executive Analytics
    df = pd.read_sql('SELECT * FROM materials', get_db_connection())
    st.metric("Total Materials", len(df))
    st.metric("Pending Remediation", len(df[df['status'] == 'PENDING']))
    st.dataframe(df)

with tabs[1]: # Data Steward Review
    pending = pd.read_sql("SELECT * FROM materials WHERE status='PENDING'", get_db_connection())
    for index, row in pending.iterrows():
        with st.expander(f"Review: {row['Material_ID']}"):
            if st.button(f"Analyze {row['Material_ID']}", key=f"ai_{index}"):
                resp = model.generate_content(f"Remediate {row['Material_ID']}")
                st.info(resp.text)
                if st.button("Approve & Execute SAP Update", key=f"exec_{index}"):
                    # Execute Integration
                    trigger_sap_integration(row['Material_ID'], resp.text)
                    # Update DB
                    conn = get_db_connection()
                    conn.execute("UPDATE materials SET status='APPROVED' WHERE Material_ID=?", (row['Material_ID'],))
                    conn.commit()
                    conn.close()
                    # Log Audit
                    log_audit(row['Material_ID'], "APPROVED_AND_SENT_TO_SAP")
                    st.success("Remediation completed and logged!")
                    st.rerun()

with tabs[2]: # Audit Trail
    st.dataframe(pd.read_sql("SELECT * FROM audit_log", get_db_connection()))