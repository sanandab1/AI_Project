from typing import Dict, Any


def make_decision_rule_based(profile: Dict, risk: Dict) -> Dict[str, Any]:
    """
    Rule-based decision making with comprehensive condition checking.
    All conditions are evaluated to determine loan approval decision.

    Args:
        profile: Applicant profile metrics
        risk: Risk analysis metrics

    Returns:
        Decision with classification, confidence, and detailed factors
    """
    score = 0
    factors_breakdown = {
        "credit_risk_contribution": 0,
        "dti_contribution": 0,
        "income_stability_contribution": 0,
        "employment_risk_contribution": 0,
        "anomaly_contribution": 0,
        "income_contribution": 0,
        "savings_contribution": 0,
        "employment_length_contribution": 0
    }

    # Credit risk scoring (hardest constraint)
    credit_risk = risk.get("credit_risk", "HIGH")
    if credit_risk == "LOW":
        score += 3
        factors_breakdown["credit_risk_contribution"] = 3
    elif credit_risk == "MEDIUM":
        score += 1
        factors_breakdown["credit_risk_contribution"] = 1
    elif credit_risk == "HIGH":
        score -= 2
        factors_breakdown["credit_risk_contribution"] = -2

    # DTI (Debt-to-Income) ratio scoring
    dti = risk.get("dti", 1.0)
    if dti < 0.3:
        score += 3
        factors_breakdown["dti_contribution"] = 3
    elif dti < 0.4:
        score += 2
        factors_breakdown["dti_contribution"] = 2
    elif dti < 0.7:
        score += 1
        factors_breakdown["dti_contribution"] = 1
    elif dti >= 0.7:
        score -= 1
        factors_breakdown["dti_contribution"] = -1

    # Anomaly detection (fraud/inconsistency check)
    if not risk.get("anomaly", False):
        score += 2
        factors_breakdown["anomaly_contribution"] = 2
    else:
        score -= 2
        factors_breakdown["anomaly_contribution"] = -2

    # Profile/Income stability scoring
    profile_score = profile.get("profile_score", 0)
    if profile_score > 0.7:
        score += 2
        factors_breakdown["income_stability_contribution"] = 2
    elif profile_score > 0.4:
        score += 1
        factors_breakdown["income_stability_contribution"] = 1
    elif profile_score < 0:
        score -= 1
        factors_breakdown["income_stability_contribution"] = -1

    # Employment risk scoring (lower is better)
    employment_risk = profile.get("employment_risk", 1.0)
    if employment_risk < 0.2:
        score += 2
        factors_breakdown["employment_risk_contribution"] = 2
    elif employment_risk < 0.4:
        score += 1
        factors_breakdown["employment_risk_contribution"] = 1
    elif employment_risk > 0.7:
        score -= 1
        factors_breakdown["employment_risk_contribution"] = -1

    # Income level scoring
    income = profile.get("income", 0)
    if income > 100000:
        score += 2
        factors_breakdown["income_contribution"] = 2
    elif income > 50000:
        score += 1
        factors_breakdown["income_contribution"] = 1
    elif income > 0:
        factors_breakdown["income_contribution"] = 0
    else:
        score -= 1
        factors_breakdown["income_contribution"] = -1

    # Savings/Assets scoring
    savings = profile.get("savings", 0)
    if savings > income * 0.5:
        score += 2
        factors_breakdown["savings_contribution"] = 2
    elif savings > income * 0.2:
        score += 1
        factors_breakdown["savings_contribution"] = 1

    # Employment length scoring
    employment_length = profile.get("employment_length_months", 0)
    if employment_length > 36:
        score += 2
        factors_breakdown["employment_length_contribution"] = 2
    elif employment_length > 12:
        score += 1
        factors_breakdown["employment_length_contribution"] = 1
    elif employment_length < 3:
        score -= 1
        factors_breakdown["employment_length_contribution"] = -1

    # Determine classification with comprehensive threshold logic
    if score >= 8:
        decision = "APPROVED"
        confidence_base = 0.95
    elif score >= 5:
        decision = "APPROVED"
        confidence_base = 0.80
    elif score >= 2:
        decision = "REVIEW"
        confidence_base = 0.65
    elif score >= 0:
        decision = "REVIEW"
        confidence_base = 0.50
    else:
        decision = "REJECTED"
        confidence_base = 0.75

    # Confidence calculation based on score magnitude and consistency
    confidence = min(confidence_base * (1 + abs(score) / 20), 1.0)

    return {
        "classification": decision,
        "risk_score": score,
        "confidence": confidence,
        "factors": factors_breakdown,
        "method": "RULE_BASED"
    }


def make_decision(profile: Dict, risk: Dict) -> Dict[str, Any]:
    """
    Make loan decision using rule-based analysis.

    Args:
        profile: Applicant profile metrics
        risk: Risk analysis metrics

    Returns:
        Decision with classification, confidence, and factors
    """
    return make_decision_rule_based(profile, risk)
