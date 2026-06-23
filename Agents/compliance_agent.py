from datetime import datetime

def compliance_action(decision):
    return {
        "case_id": f"CASE-{datetime.now().timestamp()}",
        "timestamp": str(datetime.now()),
        "action": "NOTIFIED",
        "summary": f"Loan {decision['classification']}"
    }
