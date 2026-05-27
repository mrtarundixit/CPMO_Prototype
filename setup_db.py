import sqlite3
import pandas as pd
import os
import setup_db # assuming this script creates your database

if not os.path.exists('cpmo.db'):
    setup_db.create_tables() # Ensure this function exists in your setup_db.py

# 1. Load data
mdg = pd.read_csv('MDG_Master.csv')

# 2. Setup Database Connection
conn = sqlite3.connect('cpmo.db')
cursor = conn.cursor()

# 3. Create 'materials' table
mdg.to_sql('materials', conn, if_exists='replace', index=False)

# 4. Add columns for AI Orchestration status
try:
    cursor.execute("ALTER TABLE materials ADD COLUMN status TEXT DEFAULT 'PENDING'")
    cursor.execute("ALTER TABLE materials ADD COLUMN ai_remediation TEXT")
except sqlite3.OperationalError:
    print("Columns already exist, skipping...")

# 5. Create 'audit_log' table (This is the phase 4 requirement)
cursor.execute('''CREATE TABLE IF NOT EXISTS audit_log 
                  (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                   material_id TEXT, 
                   action TEXT, 
                   timestamp DATETIME)''')

conn.commit()
conn.close()
print("Database initialized with Audit Trail and Materials table.")