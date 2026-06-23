import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import os


class AuditStore:
    """SQLite-based persistent audit trail storage"""

    def __init__(self, db_path: str = "loan_decisions.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        """Create database schema if not exists"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS loan_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT UNIQUE NOT NULL,
                applicant_id TEXT NOT NULL,
                case_id TEXT UNIQUE,
                timestamp TEXT NOT NULL,

                -- Input data
                input_data TEXT NOT NULL,

                -- Intermediate results
                profile_data TEXT,
                risk_data TEXT,

                -- Final decision
                decision_data TEXT NOT NULL,
                explanation_data TEXT,
                compliance_data TEXT,

                -- Audit metadata
                decision_method TEXT,
                full_audit_trail TEXT,

                -- Status tracking
                workflow_status TEXT,
                error_message TEXT,

                -- Timestamps
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decision_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id TEXT NOT NULL,
                application_id TEXT NOT NULL,
                decision TEXT NOT NULL,
                confidence REAL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY(application_id) REFERENCES loan_decisions(application_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_applicant_id
            ON loan_decisions(applicant_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_case_id
            ON loan_decisions(case_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON loan_decisions(timestamp)
        """)

        conn.commit()
        conn.close()

    def create_audit_record(self, state: Any) -> str:
        """
        Store complete audit record for a loan decision

        Args:
            state: LoanOrchestrationState object

        Returns:
            application_id of the stored record
        """
        applicant_id = state.applicant_data.get("applicant_id")
        application_id = f"{applicant_id}_{datetime.utcnow().timestamp()}"
        case_id = state.compliance.case_id if state.compliance else None

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO loan_decisions (
                    application_id, applicant_id, case_id, timestamp,
                    input_data, profile_data, risk_data, decision_data,
                    explanation_data, compliance_data, decision_method,
                    full_audit_trail, workflow_status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                application_id,
                applicant_id,
                case_id,
                datetime.utcnow().isoformat(),
                json.dumps(state.applicant_data),
                json.dumps(state.profile.dict()) if state.profile else None,
                json.dumps(state.risk.dict()) if state.risk else None,
                json.dumps(state.decision.dict()) if state.decision else None,
                json.dumps(state.explanation.dict()) if state.explanation else None,
                json.dumps(state.compliance.dict()) if state.compliance else None,
                state.decision.method if state.decision else None,
                json.dumps([e.dict() for e in state.audit_trail]),
                state.workflow_status,
                state.error_message,
            ))

            # Also record in decision history for easy querying
            if state.decision:
                cursor.execute("""
                    INSERT INTO decision_history (
                        applicant_id, application_id, decision, confidence, timestamp
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    applicant_id,
                    application_id,
                    state.decision.classification,
                    state.decision.confidence,
                    datetime.utcnow().isoformat(),
                ))

            conn.commit()
            return application_id

        except sqlite3.IntegrityError as e:
            raise ValueError(f"Audit record creation failed: {str(e)}")
        finally:
            conn.close()

    def get_audit_history(self, applicant_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all decisions for an applicant

        Args:
            applicant_id: The applicant's ID

        Returns:
            List of decision records
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM decision_history
                WHERE applicant_id = ?
                ORDER BY timestamp DESC
            """, (applicant_id,))

            rows = cursor.fetchall()
            return [dict(row) for row in rows]

        finally:
            conn.close()

    def get_decision_trail(self, case_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve complete decision trail for a case

        Args:
            case_id: The case ID to look up

        Returns:
            Complete audit record with all intermediate results
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM loan_decisions
                WHERE case_id = ?
            """, (case_id,))

            row = cursor.fetchone()
            if not row:
                return None

            record = dict(row)
            # Parse JSON fields
            record["input_data"] = json.loads(record["input_data"])
            record["profile_data"] = json.loads(record["profile_data"]) if record["profile_data"] else None
            record["risk_data"] = json.loads(record["risk_data"]) if record["risk_data"] else None
            record["decision_data"] = json.loads(record["decision_data"]) if record["decision_data"] else None
            record["explanation_data"] = json.loads(record["explanation_data"]) if record["explanation_data"] else None
            record["compliance_data"] = json.loads(record["compliance_data"]) if record["compliance_data"] else None
            record["full_audit_trail"] = json.loads(record["full_audit_trail"])

            return record

        finally:
            conn.close()

    def get_application_record(self, application_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve audit record by application ID

        Args:
            application_id: The application ID

        Returns:
            Complete audit record
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT * FROM loan_decisions
                WHERE application_id = ?
            """, (application_id,))

            row = cursor.fetchone()
            if not row:
                return None

            record = dict(row)
            # Parse JSON fields
            record["input_data"] = json.loads(record["input_data"])
            record["profile_data"] = json.loads(record["profile_data"]) if record["profile_data"] else None
            record["risk_data"] = json.loads(record["risk_data"]) if record["risk_data"] else None
            record["decision_data"] = json.loads(record["decision_data"]) if record["decision_data"] else None
            record["explanation_data"] = json.loads(record["explanation_data"]) if record["explanation_data"] else None
            record["compliance_data"] = json.loads(record["compliance_data"]) if record["compliance_data"] else None
            record["full_audit_trail"] = json.loads(record["full_audit_trail"])

            return record

        finally:
            conn.close()

    def get_statistics(self) -> Dict[str, Any]:
        """Get audit statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) as total FROM loan_decisions")
            total = cursor.fetchone()[0]

            cursor.execute("""
                SELECT decision, COUNT(*) as count
                FROM decision_history
                GROUP BY decision
            """)
            decision_breakdown = {row[0]: row[1] for row in cursor.fetchall()}

            cursor.execute("""
                SELECT AVG(confidence) as avg_confidence
                FROM decision_history
            """)
            avg_confidence = cursor.fetchone()[0] or 0

            return {
                "total_decisions": total,
                "decision_breakdown": decision_breakdown,
                "average_confidence": avg_confidence,
            }

        finally:
            conn.close()


# Singleton instance
_audit_store = None


def get_audit_store() -> AuditStore:
    """Get or create singleton audit store"""
    global _audit_store
    if _audit_store is None:
        db_path = os.getenv("AUDIT_DB_PATH", "loan_decisions.db")
        _audit_store = AuditStore(db_path)
    return _audit_store
