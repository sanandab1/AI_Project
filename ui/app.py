import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, Any
import sqlite3

# Page configuration
st.set_page_config(
    page_title="AI Loan Approval System",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
<style>
    .decision-approved {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .decision-rejected {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
    .decision-review {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 AI Loan Approval System")
st.markdown("Advanced agentic AI system for intelligent loan decision-making")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Select Page",
        ["New Application", "Application History", "System Statistics"]
    )

API_URL = "http://localhost:8000"


def format_decision_display(decision_class: str, confidence: float) -> tuple:
    """Format decision with color and icon"""
    if decision_class == "APPROVED":
        return "✅ APPROVED", "#28a745", "decision-approved"
    elif decision_class == "REJECTED":
        return "❌ REJECTED", "#dc3545", "decision-rejected"
    else:
        return "⚠️ REQUIRES REVIEW", "#ffc107", "decision-review"


def submit_loan_application(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Submit loan application to API"""
    try:
        response = requests.post(f"{API_URL}/loan/process", json=payload, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("⚠️ Cannot connect to API server. Please ensure the API is running on port 8000.")
        return None
    except requests.exceptions.Timeout:
        st.error("⚠️ API request timed out. Please try again.")
        return None
    except Exception as e:
        st.error(f"⚠️ Error processing application: {str(e)}")
        return None


def display_decision_result(result: Dict[str, Any]):
    """Display detailed decision result"""
    if not result or result.get("workflow_status") == "ERROR":
        st.error(f"❌ Workflow Error: {result.get('error_message', 'Unknown error')}")
        return

    decision = result.get("decision", {})
    explanation = result.get("explanation", {})
    compliance = result.get("compliance", {})

    # Decision banner
    if decision:
        decision_text, color, css_class = format_decision_display(
            decision.get("classification", "REVIEW"),
            decision.get("confidence", 0)
        )

        if css_class == "decision-approved":
            st.success(f"### {decision_text}")
        elif css_class == "decision-rejected":
            st.error(f"### {decision_text}")
        else:
            st.warning(f"### {decision_text}")

    # Metrics row
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Decision Confidence",
            f"{decision.get('confidence', 0):.0%}",
            "LLM-based decision"
        )

    with col2:
        st.metric(
            "Decision Method",
            decision.get("method", "UNKNOWN"),
            "With fallback capability"
        )

    with col3:
        st.metric(
            "Case ID",
            compliance.get("case_id", "N/A")[:20] + "..." if compliance.get("case_id") else "N/A",
            "For audit tracking"
        )

    # Explanation section
    if explanation:
        st.subheader("📋 Decision Explanation")
        st.write(explanation.get("summary", "No summary available"))

        # Key factors
        st.subheader("🎯 Key Factors")
        for factor in explanation.get("key_factors", []):
            st.info(f"• {factor}")

        # Risk summary
        if explanation.get("risk_summary"):
            st.subheader("⚠️ Risk Assessment")
            st.write(explanation.get("risk_summary"))

        # Recommendation
        if explanation.get("recommendation"):
            st.subheader("💡 Next Steps")
            st.success(explanation.get("recommendation"))

    # Audit trail
    audit_trail = result.get("audit_trail", [])
    if audit_trail:
        st.subheader("📊 Audit Trail")
        with st.expander("View Complete Audit Trail"):
            for i, entry in enumerate(audit_trail):
                st.write(f"**Stage {i+1}: {entry.get('stage')}**")
                st.write(f"Status: {entry.get('status')}")
                st.write(f"Timestamp: {entry.get('timestamp')}")
                if entry.get("data"):
                    st.json(entry.get("data"))
                st.divider()


def get_applicant_history(applicant_id: str) -> list:
    """Retrieve applicant decision history from audit database"""
    try:
        conn = sqlite3.connect("loan_decisions.db")
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT application_id, decision, confidence, timestamp
            FROM decision_history
            WHERE applicant_id = ?
            ORDER BY timestamp DESC
        """, (applicant_id,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]
    except Exception as e:
        st.warning(f"Could not retrieve history: {str(e)}")
        return []


def get_system_statistics() -> Dict[str, Any]:
    """Get system statistics from audit database"""
    try:
        conn = sqlite3.connect("loan_decisions.db")
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) as total FROM loan_decisions")
        total = cursor.fetchone()[0]

        cursor.execute("""
            SELECT decision, COUNT(*) as count
            FROM decision_history
            GROUP BY decision
        """)
        breakdown = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT AVG(confidence) as avg_confidence FROM decision_history")
        avg_confidence = cursor.fetchone()[0] or 0

        conn.close()

        return {
            "total_decisions": total,
            "decision_breakdown": breakdown,
            "average_confidence": avg_confidence
        }
    except Exception as e:
        st.warning(f"Could not retrieve statistics: {str(e)}")
        return {}


# Page: New Application
if page == "New Application":
    st.header("📝 New Loan Application")

    col1, col2 = st.columns(2)

    with st.form("loan_form", clear_on_submit=True):
        st.subheader("Applicant Information")

        with col1:
            applicant_id = st.text_input("Applicant ID *", placeholder="APP001")
            age = st.number_input("Age *", min_value=18, max_value=100, value=30)
            income = st.number_input("Annual Income ($) *", min_value=0, value=50000)
            employment_type = st.selectbox(
                "Employment Type *",
                ["Salaried", "Self-Employed", "Freelance", "Other"]
            )

        with col2:
            credit_score = st.number_input("Credit Score *", min_value=300, max_value=850, value=700)
            loan_amount = st.number_input("Requested Loan Amount ($) *", min_value=0, value=100000)
            tenure = st.number_input("Loan Tenure (months) *", min_value=1, max_value=360, value=24)
            liabilities = st.number_input("Existing Liabilities ($) *", min_value=0, value=0)

        st.subheader("Location")
        location = st.text_input("Location", value="India")

        submit = st.form_submit_button("🚀 Process Application", use_container_width=True)

    if submit:
        if not applicant_id:
            st.error("❌ Applicant ID is required")
        else:
            # Prepare payload
            payload = {
                "applicant_id": applicant_id,
                "age": age,
                "income": income,
                "employment_type": employment_type,
                "credit_score": credit_score,
                "loan_amount": loan_amount,
                "tenure": tenure,
                "liabilities": liabilities,
                "location": location
            }

            st.info("⏳ Processing your application...")

            # Submit application
            result = submit_loan_application(payload)

            if result:
                st.success("✅ Application processed successfully!")
                display_decision_result(result)

# Page: Application History
elif page == "Application History":
    st.header("📚 Application History")

    applicant_id = st.text_input("Enter Applicant ID to view history")

    if applicant_id:
        history = get_applicant_history(applicant_id)

        if history:
            st.success(f"Found {len(history)} application(s) for applicant {applicant_id}")

            for i, record in enumerate(history):
                with st.expander(
                    f"Application {i+1} - {record['decision']} - {record['timestamp'][:10]}"
                ):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Decision:** {record['decision']}")
                        st.write(f"**Confidence:** {record['confidence']:.0%}")

                    with col2:
                        st.write(f"**Timestamp:** {record['timestamp']}")
                        st.write(f"**Application ID:** {record['application_id']}")
        else:
            st.info("No applications found for this applicant ID")

# Page: System Statistics
elif page == "System Statistics":
    st.header("📊 System Statistics")

    stats = get_system_statistics()

    if stats:
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Decisions", stats.get("total_decisions", 0))

        with col2:
            st.metric("Average Confidence", f"{stats.get('average_confidence', 0):.0%}")

        with col3:
            st.metric("System Status", "✅ Operational")

        st.subheader("Decision Breakdown")

        breakdown = stats.get("decision_breakdown", {})
        if breakdown:
            col1, col2, col3 = st.columns(3)

            for i, (decision, count) in enumerate(breakdown.items()):
                if i == 0:
                    st.metric(f"✅ {decision}", count)
                elif i == 1:
                    st.metric(f"⚠️ {decision}", count)
                elif i == 2:
                    st.metric(f"❌ {decision}", count)
                else:
                    st.metric(f"{decision}", count)

        st.info("💡 Statistics are updated in real-time as applications are processed.")
    else:
        st.warning("No data available yet. Process some applications to see statistics.")