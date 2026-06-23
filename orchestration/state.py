from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


class DecisionFactors(BaseModel):
    """Structured decision factors for auditability"""
    credit_risk_contribution: float
    dti_contribution: float
    income_stability_contribution: float
    employment_risk_contribution: float
    anomaly_contribution: float
    total_score: float
    reasoning: str


class RiskMetrics(BaseModel):
    """Complete risk analysis metrics"""
    dti: float
    credit_risk: str
    loan_risk: float
    anomaly_detected: bool
    reasoning: str


class ProfileMetrics(BaseModel):
    """Applicant profile metrics"""
    income_stability: float
    employment_risk: float
    profile_score: float
    completeness: bool
    reasoning: str


class Decision(BaseModel):
    """Loan decision with full reasoning"""
    classification: str  # APPROVED, REJECTED, REVIEW
    risk_score: float
    confidence: float
    factors: DecisionFactors
    method: str  # LLM or RULE_BASED
    timestamp: str


class Explanation(BaseModel):
    """Rich explanation for the decision"""
    summary: str
    key_factors: List[str]
    risk_summary: str
    recommendation: Optional[str]
    timestamp: str


class ComplianceRecord(BaseModel):
    """Compliance tracking record"""
    case_id: str
    timestamp: str
    action: str
    applicant_notification_sent: bool
    manual_review_required: bool
    escalation_reason: Optional[str]


class AuditTrailEntry(BaseModel):
    """Single entry in audit trail"""
    stage: str
    timestamp: str
    data: Dict[str, Any]
    status: str  # SUCCESS or ERROR


class LoanOrchestrationState(BaseModel):
    """Complete state for loan approval workflow"""
    applicant_data: Dict[str, Any]  # Original LoanApplication
    profile: Optional[ProfileMetrics] = None
    risk: Optional[RiskMetrics] = None
    decision: Optional[Decision] = None
    explanation: Optional[Explanation] = None
    compliance: Optional[ComplianceRecord] = None
    audit_trail: List[AuditTrailEntry] = []
    error_message: Optional[str] = None
    error_stage: Optional[str] = None
    workflow_status: str = "STARTED"  # STARTED, IN_PROGRESS, COMPLETED, ERROR

    def add_audit_entry(self, stage: str, data: Dict[str, Any], status: str = "SUCCESS"):
        """Add entry to audit trail"""
        entry = AuditTrailEntry(
            stage=stage,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            status=status
        )
        self.audit_trail.append(entry)

    def set_error(self, error_message: str, stage: str):
        """Set error state"""
        self.error_message = error_message
        self.error_stage = stage
        self.workflow_status = "ERROR"
        self.add_audit_entry(stage, {"error": error_message}, "ERROR")

    def mark_completed(self):
        """Mark workflow as completed"""
        self.workflow_status = "COMPLETED"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "applicant_id": self.applicant_data.get("applicant_id"),
            "decision": self.decision.dict() if self.decision else None,
            "explanation": self.explanation.dict() if self.explanation else None,
            "compliance": self.compliance.dict() if self.compliance else None,
            "workflow_status": self.workflow_status,
            "audit_trail": [e.dict() for e in self.audit_trail],
            "error_message": self.error_message,
        }
