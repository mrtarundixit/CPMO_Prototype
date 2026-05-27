import pandas as pd
import os

# Get the directory where THIS script is saved
current_dir = os.path.dirname(os.path.abspath(__file__))

# Build the full paths for your files
mdg_path = os.path.join(current_dir, 'MDG_Master.csv')
plm_path = os.path.join(current_dir, 'PLM_Update.csv')

# Verify they exist
if not os.path.exists(mdg_path):
    print(f"I am looking for your files here: {current_dir}")
    print(f"Error: Could not find 'MDG_Master.csv'. Please make sure it is in that folder.")
else:
    mdg = pd.read_csv(mdg_path)
    plm = pd.read_csv(plm_path)

    # Compare the files
    comparison = mdg.merge(plm, on='Material_ID', suffixes=('_MDG', '_PLM'))
    changes = comparison[comparison['Component_MDG'] != comparison['Component_PLM']]

    print("--- AI ORCHESTRATOR ACTIONS ---")
    if not changes.empty:
        for index, row in changes.iterrows():
            print(f"ALERT: Change detected for {row['Material_ID']}")
            
            # --- PHASE 3: THE AI LOGIC ---
            if row['Material_ID'] == 'MAT-001':
                print("ACTION: High-Impact Change detected. Routing to Data Steward for approval.")
            elif row['Material_ID'] == 'MAT-009':
                print("ACTION: Supplier Update. Checking Safety Documentation compliance...")
            else:
                print("ACTION: Routine update. Auto-approving sync to MDG.")
            print("-" * 25)
    else:
        print("No discrepancies found. Data is in sync.")