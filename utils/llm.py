def generate_explanation(decision, risk):
    return f"""
    Decision: {decision['classification']}
    Risk Score: {decision['risk_score']}

    Key Factors:
    - Credit Risk: {risk['credit_risk']}
    - Debt to Income: {risk['dti']}
    - Loan Risk: {risk['loan_risk']}

    This decision is based on financial stability and risk exposure.
    """