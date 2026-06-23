import anthropic
import os
import json
import re
from typing import Dict, Any

api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY environment variable not set")

client = anthropic.Anthropic(api_key=api_key)

MODEL = "global.anthropic.claude-sonnet-4-6"


def _extract_json(response_text: str) -> Dict[str, Any]:
    """Extract JSON from LLM response text - handles nested braces"""
    response_text = response_text.strip()

    # Try direct parsing first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass

    # Find first { and match braces
    start = response_text.find('{')
    if start == -1:
        return None

    # Match braces to find complete JSON
    brace_count = 0
    end = -1
    for i in range(start, len(response_text)):
        if response_text[i] == '{':
            brace_count += 1
        elif response_text[i] == '}':
            brace_count -= 1
            if brace_count == 0:
                end = i + 1
                break

    if end > 0:
        try:
            return json.loads(response_text[start:end])
        except json.JSONDecodeError:
            pass

    return None


def get_decision_with_reasoning(profile: Dict, risk: Dict) -> Dict[str, Any]:
    """
    LLM-based decision making with detailed reasoning

    Args:
        profile: Applicant profile metrics
        risk: Risk analysis metrics

    Returns:
        Decision with factors and explanation
    """
    prompt = f"""You are an experienced loan approval expert. Make fair and balanced decisions.

### Applicant Profile:
- Income Stability: {profile.get('income_stability', 'N/A')} (1.0 = excellent, 0.5 = poor)
- Employment Risk: {profile.get('employment_risk', 'N/A')} (0.2 = low, 0.6+ = high)
- Profile Score: {profile.get('profile_score', 'N/A')} (higher is better)
- Application Complete: {profile.get('completeness', 'N/A')}

### Risk Analysis:
- Debt-to-Income Ratio: {risk.get('dti', 'N/A')} (< 0.4 = excellent, 0.4-0.6 = acceptable, > 0.7 = high)
- Credit Risk Level: {risk.get('credit_risk', 'N/A')} (LOW = best, MEDIUM = acceptable, HIGH = risky)
- Loan-to-Income Ratio: {risk.get('loan_risk', 'N/A')} (lower is better)
- Anomaly Detected: {risk.get('anomaly', 'N/A')}

### Decision Guidelines:
APPROVE if:
- Credit risk is LOW OR MEDIUM (not HIGH)
- DTI is less than 0.5
- Income stability is good (> 0.6)
- No major anomalies
- Profile score is positive

REVIEW if:
- Any moderate risk factors OR mixed signals
- DTI between 0.5-0.7
- Credit risk is MEDIUM with other concerns
- Need additional verification

REJECT if:
- Credit risk is HIGH and DTI > 0.6
- DTI > 0.7 with low income stability
- Multiple high-risk factors combined
- Application incomplete

### Output STRICT JSON ONLY (no other text):
{{
  "classification": "APPROVED",
  "confidence": 0.9,
  "risk_score": 0.7,
  "factors": {{
    "credit_risk_contribution": 0.3,
    "dti_contribution": 0.2,
    "income_stability_contribution": 0.2,
    "employment_risk_contribution": 0.1,
    "anomaly_contribution": 0.1,
    "total_score": 0.7,
    "reasoning": "Strong profile meets approval criteria"
  }},
  "key_factors": ["Excellent credit score", "Low DTI", "Stable employment"],
  "reasoning": "Applicant qualifies for approval"
}}

DO NOT include any text before or after the JSON. Respond with ONLY the JSON object."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=500,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}]
    )

    result = _extract_json(response.content[0].text.strip())
    if result:
        return result

    return {
        "classification": "REVIEW",
        "confidence": 0.5,
        "risk_score": 0.5,
        "key_factors": ["Unable to parse LLM response"],
        "reasoning": "Fallback due to parsing issue"
    }


def get_applicant_profile_reasoning(applicant_data: Dict) -> Dict[str, Any]:
    """
    LLM-based applicant profile analysis with reasoning

    Args:
        applicant_data: Raw applicant data

    Returns:
        Profile analysis with reasoning
    """
    prompt = f"""Analyze this loan applicant's profile and provide structured assessment:

Applicant Details:
- Age: {applicant_data.get('age')}
- Employment Type: {applicant_data.get('employment_type')}
- Annual Income: ${applicant_data.get('income')}
- Credit Score: {applicant_data.get('credit_score')}
- Location: {applicant_data.get('location')}

Provide analysis in this exact JSON format:
{{
  "income_stability_assessment": "description",
  "employment_risk_level": "LOW|MEDIUM|HIGH",
  "profile_completeness": true|false,
  "overall_assessment": "brief summary",
  "risk_flags": ["flag1", "flag2"]
}}

Respond ONLY with JSON."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}]
    )

    result = _extract_json(response.content[0].text.strip())
    return result if result else {
        "income_stability_assessment": "Standard assessment",
        "employment_risk_level": "MEDIUM",
        "profile_completeness": True,
        "overall_assessment": "Fallback assessment",
        "risk_flags": []
    }


def get_risk_analysis_reasoning(risk_data: Dict) -> Dict[str, Any]:
    """
    LLM-based risk analysis with detailed reasoning

    Args:
        risk_data: Risk metrics

    Returns:
        Risk analysis with factors
    """
    prompt = f"""Analyze the following risk metrics and provide assessment:

Risk Metrics:
- Debt-to-Income Ratio: {risk_data.get('dti')}
- Credit Risk Level: {risk_data.get('credit_risk')}
- Loan-to-Income Ratio: {risk_data.get('loan_risk')}
- Anomaly Detected: {risk_data.get('anomaly')}

Provide analysis in this JSON format:
{{
  "overall_risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
  "risk_factors": ["factor1", "factor2"],
  "mitigating_factors": ["positive1", "positive2"],
  "key_concerns": ["concern1", "concern2"],
  "recommendation": "brief recommendation"
}}

Respond ONLY with JSON."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        temperature=0.2,
        messages=[{"role": "user", "content": prompt}]
    )

    result = _extract_json(response.content[0].text.strip())
    return result if result else {
        "overall_risk_level": "MEDIUM",
        "risk_factors": [],
        "mitigating_factors": [],
        "key_concerns": [],
        "recommendation": "Fallback assessment"
    }


def get_rich_explanation(decision: Dict, profile: Dict, risk: Dict, applicant_data: Dict) -> str:
    """
    Generate rich natural language explanation for decision

    Args:
        decision: Decision data
        profile: Profile metrics
        risk: Risk metrics
        applicant_data: Original applicant data

    Returns:
        Rich explanation text
    """
    classification = decision.get('classification')
    confidence = decision.get('confidence', 0)

    prompt = f"""Generate a professional, non-technical explanation of this loan decision for the applicant:

Decision: {classification}
Confidence: {confidence:.0%}

Applicant Profile:
- Income: ${applicant_data.get('income')}
- Credit Score: {applicant_data.get('credit_score')}
- Employment: {applicant_data.get('employment_type')}

Risk Assessment:
- DTI: {risk.get('dti', 'N/A')}
- Credit Risk: {risk.get('credit_risk', 'N/A')}
- Loan Risk: {risk.get('loan_risk', 'N/A')}

Key Decision Factors:
{json.dumps(decision.get('factors', {}), indent=2) if decision.get('factors') else 'N/A'}

Generate a brief, professional explanation (3-4 sentences) that a non-technical person can understand. Be positive and constructive.

Respond with ONLY the explanation text, no JSON."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        temperature=0.3,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()


def get_decision(profile, risk):
    """Legacy function for backward compatibility"""
    result = get_decision_with_reasoning(profile, risk)
    return result