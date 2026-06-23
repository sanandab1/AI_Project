"""
Service for generating rich, natural language explanations for loan decisions
"""

from typing import Dict, Any, List
from loan_ai_system.services.llm_service import get_rich_explanation, client, MODEL, _extract_json
import json


def generate_decision_explanation(
    decision: Dict[str, Any],
    profile: Dict[str, Any],
    risk: Dict[str, Any],
    applicant_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Generate structured explanation for loan decision

    Args:
        decision: The loan decision
        profile: Applicant profile metrics
        risk: Risk analysis metrics
        applicant_data: Original applicant data

    Returns:
        Structured explanation with summary, factors, and recommendation
    """
    classification = decision.get("classification", "REVIEW")

    # Generate natural language summary
    summary = get_rich_explanation(decision, profile, risk, applicant_data)

    # Extract key factors
    key_factors = extract_key_factors(decision, profile, risk, classification)

    # Generate risk summary
    risk_summary = generate_risk_summary(risk)

    # Generate recommendation based on classification
    recommendation = None
    if classification == "REVIEW":
        recommendation = "This application requires manual review. Our team will contact you within 2-3 business days."
    elif classification == "APPROVED":
        recommendation = "Congratulations! Your application has been approved. Please proceed to the next steps."
    elif classification == "REJECTED":
        recommendation = "Unfortunately, your application cannot be approved at this time. Please contact our support team to understand your options."

    return {
        "summary": summary,
        "key_factors": key_factors,
        "risk_summary": risk_summary,
        "recommendation": recommendation,
        "classification": classification
    }


def extract_key_factors(
    decision: Dict[str, Any],
    profile: Dict[str, Any],
    risk: Dict[str, Any],
    classification: str
) -> List[str]:
    """
    Extract key decision factors in human-readable format

    Args:
        decision: Decision data
        profile: Profile metrics
        risk: Risk metrics
        classification: Decision classification

    Returns:
        List of key factors
    """
    factors = []

    # Credit score factors
    credit_risk = risk.get("credit_risk", "MEDIUM")
    if credit_risk == "LOW":
        factors.append(f"Strong credit score ({risk.get('credit_score', 'N/A')}): Lower default risk")
    elif credit_risk == "HIGH":
        factors.append(f"Lower credit score ({risk.get('credit_score', 'N/A')}): Higher default risk")
    else:
        factors.append(f"Moderate credit score: Standard risk profile")

    # DTI factors
    dti = risk.get("dti", 0)
    if dti < 0.3:
        factors.append(f"Excellent debt-to-income ratio ({dti:.1%}): Strong repayment capacity")
    elif dti < 0.5:
        factors.append(f"Acceptable debt-to-income ratio ({dti:.1%}): Adequate repayment capacity")
    elif dti < 0.7:
        factors.append(f"Higher debt-to-income ratio ({dti:.1%}): Limited repayment capacity")
    else:
        factors.append(f"High debt burden ({dti:.1%}): Significant repayment risk")

    # Income stability
    income_stability = profile.get("income_stability", 0)
    if income_stability > 0.7:
        factors.append("Strong income stability: Reliable earning source")
    elif income_stability > 0.3:
        factors.append("Moderate income stability: Acceptable earning source")
    else:
        factors.append("Lower income stability: Potential earning risk")

    # Employment factors
    employment_risk = profile.get("employment_risk", 0)
    employment_type = profile.get("employment_type", "Unknown")
    if employment_risk < 0.3:
        factors.append(f"Stable employment ({employment_type}): Low employment risk")
    elif employment_risk < 0.5:
        factors.append(f"Standard employment ({employment_type}): Moderate employment risk")
    else:
        factors.append(f"Variable employment ({employment_type}): Higher employment risk")

    # Anomaly factors
    if risk.get("anomaly", False):
        factors.append("Anomaly detected: Loan amount appears unusually high relative to income")

    return factors[:5]  # Return top 5 factors


def generate_risk_summary(risk: Dict[str, Any]) -> str:
    """
    Generate human-readable risk summary

    Args:
        risk: Risk metrics

    Returns:
        Risk summary text
    """
    dti = risk.get("dti", 0)
    credit_risk = risk.get("credit_risk", "MEDIUM")
    loan_risk = risk.get("loan_risk", 0)
    anomaly = risk.get("anomaly", False)

    # Build risk narrative
    parts = []

    if credit_risk == "LOW":
        parts.append("credit score is strong")
    elif credit_risk == "HIGH":
        parts.append("credit score is lower")
    else:
        parts.append("credit score is moderate")

    if dti < 0.5:
        parts.append("and debt levels are manageable")
    elif dti < 0.7:
        parts.append("and debt levels are concerning")
    else:
        parts.append("and debt levels are high")

    if loan_risk < 0.5:
        parts.append("with the requested loan amount being reasonable")
    else:
        parts.append("with the requested loan amount being substantial")

    summary = f"Risk Assessment: Your {', '.join(parts)}."

    if anomaly:
        summary += " Note: The loan amount appears unusually high for your income level."

    return summary


def generate_review_escalation_message(
    profile: Dict[str, Any],
    risk: Dict[str, Any],
    reasons: List[str]
) -> str:
    """
    Generate message for REVIEW classification escalation

    Args:
        profile: Profile metrics
        risk: Risk metrics
        reasons: List of reasons for review

    Returns:
        Escalation message
    """
    prompt = f"""Generate a professional escalation message for manual review of a loan application.

Reasons for Review:
{json.dumps(reasons, indent=2)}

Risk Factors:
- DTI: {risk.get('dti', 'N/A')}
- Credit Risk: {risk.get('credit_risk', 'N/A')}
- Employment Risk: {profile.get('employment_risk', 'N/A')}

Generate a 2-3 sentence professional message that explains why this application needs manual review and what happens next.

Respond with ONLY the message text."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=200,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()
