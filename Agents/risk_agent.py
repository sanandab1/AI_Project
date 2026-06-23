from typing import Dict, Any
from loan_ai_system.services.mcp_client import call_mcp
from loan_ai_system.services.logger_service import StructuredLogger

logger = StructuredLogger(__name__)


def risk_analysis(data: Any) -> Dict[str, Any]:
    """
    Analyze financial risk with optional MCP enrichment

    Args:
        data: LoanApplication data

    Returns:
        Risk metrics including DTI, credit risk, and anomaly detection
    """
    # Convert data to dict if needed
    if hasattr(data, "dict"):
        data_dict = data.dict()
    else:
        data_dict = dict(data) if isinstance(data, dict) else data.__dict__

    applicant_id = data_dict.get("applicant_id")
    liabilities = data_dict.get("liabilities", 0)
    income = data_dict.get("income", 1)  # Prevent division by zero
    credit_score = data_dict.get("credit_score", 600)
    loan_amount = data_dict.get("loan_amount", 0)

    # Prevent division by zero
    if income == 0:
        income = 1

    # Debt-to-Income ratio
    dti = liabilities / income

    # Try to enrich credit score with MCP (bureau lookup) - graceful degradation
    verified_credit_score = credit_score
    try:
        mcp_result = call_mcp(
            "get_credit_bureau_data",
            {"applicant_id": applicant_id, "credit_score": credit_score}
        )
        if mcp_result and mcp_result.get("verified_credit_score"):
            verified_credit_score = mcp_result.get("verified_credit_score")
            logger.info(
                "Credit score verified via MCP",
                applicant_id=applicant_id,
                verified_score=verified_credit_score
            )
    except Exception as e:
        logger.warning(f"MCP credit verification failed, using declared score: {str(e)}")

    # Credit risk classification
    if verified_credit_score > 750:
        credit_risk = "LOW"
    elif verified_credit_score > 650:
        credit_risk = "MEDIUM"
    else:
        credit_risk = "HIGH"

    # Loan risk (loan-to-income ratio)
    loan_risk = loan_amount / income

    # Anomaly detection (unusually high loan relative to income)
    anomaly = loan_amount > (income * 10)

    logger.info(
        "Risk analysis completed",
        applicant_id=applicant_id,
        dti=dti,
        credit_risk=credit_risk,
        loan_risk=loan_risk,
        anomaly_detected=anomaly
    )

    return {
        "dti": dti,
        "credit_risk": credit_risk,
        "loan_risk": loan_risk,
        "anomaly": anomaly,
        "credit_score": verified_credit_score
    }