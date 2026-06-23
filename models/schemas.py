from pydantic import BaseModel
from typing import Optional

# Input schema
class LoanApplication(BaseModel):
    applicant_id: str
    age: int
    income: float
    employment_type: str
    credit_score: int
    loan_amount: float
    tenure: int
    liabilities: float
    location: str

# Output schema
class DecisionOutput(BaseModel):
    classification: str
    risk_score: float
    confidence: float
    explanation: str
