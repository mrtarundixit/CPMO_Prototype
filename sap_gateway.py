import json
from datetime import datetime

def trigger_sap_integration(material_id, new_value):
    """Simulates a secure API call to SAP/MDM."""
    payload = {
        "material_id": material_id,
        "action": "UPDATE",
        "value": new_value,
        "timestamp": datetime.now().isoformat(),
        "status": "QUEUED_FOR_ERP"
    }
    
    # In production, this would be a requests.post() call
    with open("SAP_Outbound_Queue.json", "a") as f:
        f.write(json.dumps(payload) + "\n")
        
    return True