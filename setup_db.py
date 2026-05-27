import sqlite3
import pandas as pd
import os

# Cloud-compatible path
DB_PATH = '/mount/src/cpmo_prototype/cpmo.db' if os.path.exists('/mount/src') else 'cpmo.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Load master data if available
    if os.path.exists('MDG_Master.csv'):
        mdg = pd.read_csv('MDG_Master.csv')
        mdg.to_sql('materials', conn, if_exists='replace', index=False)
    
    # Add AI orchestration columns
    try:
        cursor.execute("ALTER TABLE materials ADD COLUMN status TEXT DEFAULT 'PENDING'")
        cursor.execute("ALTER TABLE materials ADD COLUMN ai_remediation TEXT")
    except sqlite3.OperationalError:
        pass 

    # Create Audit table
    cursor.execute('''CREATE TABLE IF NOT EXISTS audit_log 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       material_id TEXT, 
                       action TEXT, 
                       timestamp DATETIME)''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()