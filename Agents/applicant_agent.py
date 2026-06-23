from typing import Dict, Any
from loan_ai_system.services.mcp_client import call_mcp
from loan_ai_system.services.logger_service import StructuredLogger

logger = StructuredLogger(__name__)


def analyze_applicant(data: Any) -> Dict[str, Any]:
    """
    Analyze applicant profile with optional MCP enrichment

    Args:
        data: LoanApplication data

    Returns:
        Profile analysis metrics
    """
    # Convert data to dict if needed
    if hasattr(data, "dict"):
        data_dict = data.dict()
    else:
        data_dict = dict(data) if isinstance(data, dict) else data.__dict__

    applicant_id = data_dict.get("applicant_id")
    income = data_dict.get("income", 0)
    employment_type = data_dict.get("employment_type", "Unknown")

    # Try to enrich with MCP (income verification) - graceful degradation
    verified_income = income
    try:
        mcp_result = call_mcp(
            "verify_income",
            {"applicant_id": applicant_id, "declared_income": income}
        )
        if mcp_result and mcp_result.get("verified_income"):
            verified_income = mcp_result.get("verified_income")
            logger.info("Income verified via MCP", applicant_id=applicant_id, verified_income=verified_income)
    except Exception as e:
        logger.warning(f"MCP income verification failed, using declared income: {str(e)}")

    # Income stability score (0-1)
    income_stability = 1.0 if verified_income > 50000 else (0.7 if verified_income > 30000 else 0.5)

    # Employment risk score (0-1)
    employment_risk_map = {
        "Salaried": 0.2,
        "Self-Employed": 0.6,
        "Freelance": 0.7,
        "Other": 0.8
    }
    employment_risk = employment_risk_map.get(employment_type, 0.5)

    # Profile score
    profile_score = income_stability - employment_risk

    # Completeness check
    completeness = all([
        data_dict.get("age"),
        data_dict.get("income"),
        data_dict.get("credit_score")
    ])

    logger.info(
        "Applicant analysis completed",
        applicant_id=applicant_id,
        income_stability=income_stability,
        employment_risk=employment_risk
    )

    return {
        "income_stability": income_stability,
        "employment_risk": employment_risk,
        "profile_score": profile_score,
        "complete": completeness,
        "employment_type": employment_type
    }