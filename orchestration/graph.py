from typing import Dict, Any
from datetime import datetime
from langgraph.graph import StateGraph, END
from loan_ai_system.orchestration.state import (
    LoanOrchestrationState,
    ProfileMetrics,
    RiskMetrics,
    Decision,
    Explanation,
    ComplianceRecord,
    DecisionFactors
)
from loan_ai_system.agents.applicant_agent import analyze_applicant
from loan_ai_system.agents.risk_agent import risk_analysis
from loan_ai_system.agents.decision_agent import make_decision
from loan_ai_system.agents.compliance_agent import compliance_action
from loan_ai_system.services.explanation_service import generate_decision_explanation
from loan_ai_system.services.logger_service import StructuredLogger
from loan_ai_system.persistence.audit_store import get_audit_store

logger = StructuredLogger(__name__)


def node_analyze_applicant(state: LoanOrchestrationState) -> LoanOrchestrationState:
    """Analyze applicant profile and financial stability"""
    try:
        logger.info("Starting applicant analysis")
        profile_dict = analyze_applicant(state.applicant_data)

        state.profile = ProfileMetrics(
            income_stability=profile_dict.get("income_stability", 0),
            employment_risk=profile_dict.get("employment_risk", 0),
            profile_score=profile_dict.get("profile_score", 0),
            completeness=profile_dict.get("complete", False),
            reasoning="Profile analysis completed"
        )

        state.add_audit_entry(
            "analyze_applicant",
            {"profile": state.profile.dict()},
            "SUCCESS"
        )
        logger.info("Applicant analysis completed", profile_score=state.profile.profile_score)

    except Exception as e:
        logger.error(f"Error in applicant analysis: {str(e)}")
        state.set_error(f"Applicant analysis failed: {str(e)}", "analyze_applicant")

    return state


def node_analyze_risk(state: LoanOrchestrationState) -> LoanOrchestrationState:
    """Analyze financial risk"""
    if state.error_message:
        return state

    try:
        logger.info("Starting risk analysis")
        risk_dict = risk_analysis(state.applicant_data)

        state.risk = RiskMetrics(
            dti=risk_dict.get("dti", 0),
            credit_risk=risk_dict.get("credit_risk", "MEDIUM"),
            loan_risk=risk_dict.get("loan_risk", 0),
            anomaly_detected=risk_dict.get("anomaly", False),
            reasoning="Risk analysis completed"
        )

        state.add_audit_entry(
            "analyze_risk",
            {"risk": state.risk.dict()},
            "SUCCESS"
        )
        logger.info("Risk analysis completed", credit_risk=state.risk.credit_risk, dti=state.risk.dti)

    except Exception as e:
        logger.error(f"Error in risk analysis: {str(e)}")
        state.set_error(f"Risk analysis failed: {str(e)}", "analyze_risk")

    return state


def node_make_decision(state: LoanOrchestrationState) -> LoanOrchestrationState:
    """Make loan decision using LLM with fallback"""
    if state.error_message:
        return state

    try:
        logger.info("Starting decision making")

        # Prepare data for decision
        profile_dict = state.profile.dict() if state.profile else {}
        risk_dict = state.risk.dict() if state.risk else {}

        # Make decision (rule-based)
        decision_dict = make_decision(profile_dict, risk_dict)

        # Create factors if not present
        factors_dict = decision_dict.get("factors", {})
        if not factors_dict or not isinstance(factors_dict, dict):
            factors_dict = {}

        # Ensure all required fields are present
        if "total_score" not in factors_dict:
            factors_dict["total_score"] = decision_dict.get("risk_score", 0)
        if "reasoning" not in factors_dict:
            factors_dict["reasoning"] = decision_dict.get("reasoning", "Decision made by system")

        state.decision = Decision(
            classification=decision_dict.get("classification", "REVIEW"),
            risk_score=decision_dict.get("risk_score", 0),
            confidence=decision_dict.get("confidence", 0.5),
            factors=DecisionFactors(**factors_dict),
            method=decision_dict.get("method", "LLM"),
            timestamp=datetime.utcnow().isoformat()
        )

        state.add_audit_entry(
            "make_decision",
            {
                "decision": state.decision.dict(),
                "method": state.decision.method
            },
            "SUCCESS"
        )

        logger.info(
            "Decision made",
            classification=state.decision.classification,
            confidence=state.decision.confidence,
            method=state.decision.method
        )

    except Exception as e:
        logger.error(f"Error in decision making: {str(e)}")
        state.set_error(f"Decision making failed: {str(e)}", "make_decision")

    return state


def node_generate_explanation(state: LoanOrchestrationState) -> LoanOrchestrationState:
    """Generate rich explanation for the decision"""
    if state.error_message or not state.decision:
        return state

    try:
        logger.info("Generating explanation")

        profile_dict = state.profile.dict() if state.profile else {}
        risk_dict = state.risk.dict() if state.risk else {}
        decision_dict = state.decision.dict()

        explanation_dict = generate_decision_explanation(
            decision_dict,
            profile_dict,
            risk_dict,
            state.applicant_data
        )

        state.explanation = Explanation(
            summary=explanation_dict.get("summary", ""),
            key_factors=explanation_dict.get("key_factors", []),
            risk_summary=explanation_dict.get("risk_summary", ""),
            recommendation=explanation_dict.get("recommendation"),
            timestamp=datetime.utcnow().isoformat()
        )

        state.add_audit_entry(
            "generate_explanation",
            {"explanation": state.explanation.dict()},
            "SUCCESS"
        )

        logger.info("Explanation generated successfully")

    except Exception as e:
        logger.error(f"Error generating explanation: {str(e)}")
        state.set_error(f"Explanation generation failed: {str(e)}", "generate_explanation")

    return state


def node_create_compliance_record(state: LoanOrchestrationState) -> LoanOrchestrationState:
    """Create compliance and audit record"""
    if not state.decision:
        return state

    try:
        logger.info("Creating compliance record")

        compliance_dict = compliance_action(state.decision.dict())

        state.compliance = ComplianceRecord(
            case_id=compliance_dict.get("case_id", f"CASE-{datetime.utcnow().timestamp()}"),
            timestamp=compliance_dict.get("timestamp", datetime.utcnow().isoformat()),
            action=compliance_dict.get("action", "PROCESSED"),
            applicant_notification_sent=True,
            manual_review_required=state.decision.classification == "REVIEW",
            escalation_reason=None if state.decision.classification != "REVIEW" else "Manual review classification"
        )

        state.add_audit_entry(
            "create_compliance_record",
            {"compliance": state.compliance.dict()},
            "SUCCESS"
        )

        logger.info("Compliance record created", case_id=state.compliance.case_id)

    except Exception as e:
        logger.error(f"Error creating compliance record: {str(e)}")
        state.set_error(f"Compliance record creation failed: {str(e)}", "create_compliance_record")

    return state


def node_store_audit_trail(state: LoanOrchestrationState) -> LoanOrchestrationState:
    """Store audit trail in persistent database"""
    try:
        logger.info("Storing audit trail")

        audit_store = get_audit_store()
        application_id = audit_store.create_audit_record(state)

        state.add_audit_entry(
            "store_audit_trail",
            {"application_id": application_id},
            "SUCCESS"
        )

        state.mark_completed()
        logger.info("Audit trail stored successfully", application_id=application_id)

    except Exception as e:
        logger.error(f"Error storing audit trail: {str(e)}")
        state.set_error(f"Audit trail storage failed: {str(e)}", "store_audit_trail")

    return state


def node_manual_review_escalation(state: LoanOrchestrationState) -> LoanOrchestrationState:
    """Handle manual review escalation"""
    logger.info("Application escalated for manual review", case_id=state.compliance.case_id if state.compliance else "N/A")
    return state


def node_error_handler(state: LoanOrchestrationState) -> LoanOrchestrationState:
    """Handle errors gracefully"""
    logger.error(
        f"Workflow error at stage: {state.error_stage}",
        error=state.error_message,
        stage=state.error_stage
    )
    return state


def should_escalate_to_review(state: LoanOrchestrationState) -> str:
    """Conditional edge: check if manual review is needed"""
    if not state.decision:
        return "error"

    if state.decision.classification == "REVIEW":
        return "manual_review"

    return "continue"


# Build the state graph
workflow = StateGraph(LoanOrchestrationState)

# Add nodes
workflow.add_node("analyze_applicant", node_analyze_applicant)
workflow.add_node("analyze_risk", node_analyze_risk)
workflow.add_node("make_decision", node_make_decision)
workflow.add_node("generate_explanation", node_generate_explanation)
workflow.add_node("create_compliance_record", node_create_compliance_record)
workflow.add_node("store_audit_trail", node_store_audit_trail)
workflow.add_node("manual_review_escalation", node_manual_review_escalation)
workflow.add_node("error_handler", node_error_handler)

# Add edges
workflow.set_entry_point("analyze_applicant")

# Linear flow
workflow.add_edge("analyze_applicant", "analyze_risk")
workflow.add_edge("analyze_risk", "make_decision")
workflow.add_edge("make_decision", "generate_explanation")
workflow.add_edge("generate_explanation", "create_compliance_record")

# Conditional edge for manual review
workflow.add_conditional_edges(
    "create_compliance_record",
    should_escalate_to_review,
    {
        "manual_review": "manual_review_escalation",
        "continue": "store_audit_trail",
        "error": "error_handler"
    }
)

workflow.add_edge("manual_review_escalation", "store_audit_trail")
workflow.add_edge("store_audit_trail", END)
workflow.add_edge("error_handler", END)

# Compile the graph
graph = workflow.compile()


def run_workflow(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the complete loan approval workflow

    Args:
        data: Loan application data

    Returns:
        Workflow result with decision, explanation, and compliance info
    """
    # Convert input data to dict if needed
    if hasattr(data, "dict"):
        applicant_dict = data.dict()
    else:
        applicant_dict = dict(data)

    # Create initial state
    initial_state = LoanOrchestrationState(applicant_data=applicant_dict)

    try:
        # Run the graph
        result_state = graph.invoke(initial_state)

        # Return result as dictionary for API response
        if isinstance(result_state, LoanOrchestrationState):
            return result_state.to_dict()
        elif isinstance(result_state, dict):
            return result_state
        else:
            return {"error": "Unexpected result type", "type": str(type(result_state))}
    except Exception as e:
        logger.error(f"Workflow execution failed: {str(e)}")
        return {
            "workflow_status": "ERROR",
            "error_message": str(e),
            "applicant_id": applicant_dict.get("applicant_id")
        }