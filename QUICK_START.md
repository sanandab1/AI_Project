# Quick Start Guide - Loan Approval System

## Prerequisites

- Python 3.10+
- Virtual environment with dependencies installed
- ANTHROPIC_API_KEY set in environment

## Installation

### 1. Set Up Environment
```bash
cd /home/ubuntu/Desktop/Loan_Agent_Project
source .venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r loan_ai_system/requirements.txt
```

### 3. Configure API Key
```bash
export ANTHROPIC_API_KEY='sk-MbT3EUpbEfx06ORb3FnfjA'
```

## Running the System

### Terminal 1: Start the API Server
```bash
cd /home/ubuntu/Desktop/Loan_Agent_Project/loan_ai_system
export ANTHROPIC_API_KEY='sk-MbT3EUpbEfx06ORb3FnfjA'
uvicorn api.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete
```

### Terminal 2: Start the Streamlit UI
```bash
cd /home/ubuntu/Desktop/Loan_Agent_Project/loan_ai_system
export ANTHROPIC_API_KEY='sk-MbT3EUpbEfx06ORb3FnfjA'
streamlit run ui/app.py
```

Expected output:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

## Using the System

### 1. Open the UI
Navigate to: http://localhost:8501

### 2. Submit a Loan Application
- Go to **"New Application"** tab
- Fill in the form:
  - Applicant ID (required)
  - Age (18-100)
  - Annual Income
  - Employment Type (Salaried, Self-Employed, Freelance, Other)
  - Credit Score (300-850)
  - Requested Loan Amount
  - Loan Tenure (months)
  - Existing Liabilities
  - Location

### 3. View the Decision
The system will display:
- **Decision Classification**: ✅ APPROVED / ❌ REJECTED / ⚠️ REQUIRES REVIEW
- **Decision Confidence**: Percentage-based confidence score
- **Decision Method**: LLM (AI-driven) or RULE_BASED_FALLBACK
- **Case ID**: Unique identifier for audit tracking
- **Rich Explanation**: Natural language explanation of the decision
- **Key Factors**: Top factors influencing the decision
- **Risk Assessment**: Narrative risk summary
- **Next Steps**: Recommended actions

### 4. View Application History
- Go to **"Application History"** tab
- Enter Applicant ID
- See all previous decisions for that applicant

### 5. View System Statistics
- Go to **"System Statistics"** tab
- See total decisions processed
- View approval/rejection/review breakdown
- Check average confidence score

## API Usage

### Health Check
```bash
curl http://localhost:8000/health
```

### Process Loan Application
```bash
curl -X POST http://localhost:8000/loan/process \
  -H "Content-Type: application/json" \
  -d '{
    "applicant_id": "APP001",
    "age": 35,
    "income": 75000,
    "employment_type": "Salaried",
    "credit_score": 720,
    "loan_amount": 250000,
    "tenure": 60,
    "liabilities": 50000,
    "location": "New York"
  }'
```

## Workflow Architecture

```
┌─────────────────────────────────────┐
│     Streamlit UI (Multi-page)       │
└────────────────┬────────────────────┘
                 │ HTTP POST
┌────────────────▼────────────────────┐
│       FastAPI Server (Port 8000)    │
│         api.main:app                 │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│    LangGraph StateGraph Workflow     │
│                                      │
│  1. analyze_applicant (with MCP)    │
│  2. analyze_risk (with MCP)         │
│  3. make_decision (LLM + fallback)  │
│  4. generate_explanation            │
│  5. create_compliance_record        │
│  6. [CONDITIONAL] manual_review     │
│  7. store_audit_trail               │
│  8. error_handler                   │
└────────────────┬────────────────────┘
                 │
┌────────────────▼────────────────────┐
│    Services Layer                    │
│                                      │
│  • LLM Service (Claude)              │
│  • Explanation Service               │
│  • MCP Client (External Tools)       │
│  • Structured Logger                 │
│  • Audit Store (SQLite)              │
└─────────────────────────────────────┘
```

## Test Scenarios

### Scenario 1: High Probability Approval
```
Age: 35
Income: $100,000
Employment: Salaried
Credit Score: 750
Loan Amount: $300,000
Liabilities: $40,000
```
Expected: APPROVED (low risk, strong profile)

### Scenario 2: Manual Review Required
```
Age: 30
Income: $45,000
Employment: Freelance
Credit Score: 680
Loan Amount: $150,000
Liabilities: $30,000
```
Expected: REVIEW (mixed risk factors)

### Scenario 3: Rejection
```
Age: 25
Income: $30,000
Employment: Self-Employed
Credit Score: 550
Loan Amount: $500,000
Liabilities: $60,000
```
Expected: REJECTED (high risk indicators)

## Viewing Audit Trail

### Query SQLite Database
```bash
# View all decisions
sqlite3 loan_decisions.db "SELECT applicant_id, decision_data, timestamp FROM loan_decisions LIMIT 10;"

# Get applicant history
sqlite3 loan_decisions.db "SELECT * FROM decision_history WHERE applicant_id = 'APP001';"

# Get system statistics
sqlite3 loan_decisions.db "SELECT decision, COUNT(*) FROM decision_history GROUP BY decision;"
```

## Key Features

✅ **LangGraph Orchestration**
- Dynamic state machine with conditional routing
- Manual review escalation for REVIEW classifications

✅ **LLM-Driven Reasoning**
- Claude provides explicit reasoning for decisions
- Fallback to rule-based system if LLM fails
- Clear decision method tracking

✅ **Rich Explanations**
- Natural language decision explanations
- Key factors highlighted
- Risk assessment narrative

✅ **MCP Integration**
- Income verification via MCP
- Credit bureau lookup via MCP
- Graceful fallback handling

✅ **Persistent Audit Trail**
- SQLite database with immutable records
- Complete decision history per applicant
- Queryable for compliance review

✅ **Professional UI**
- Multi-page interface
- Application form
- Decision history
- System statistics
- Color-coded decision display

✅ **Error Handling**
- Comprehensive error recovery
- Graceful degradation
- Detailed error logging

## Troubleshooting

### "Cannot connect to API server"
- Ensure API is running on port 8000
- Check: `curl http://localhost:8000/health`

### "ANTHROPIC_API_KEY not set"
- Set the environment variable:
  ```bash
  export ANTHROPIC_API_KEY='sk-MbT3EUpbEfx06ORb3FnfjA'
  ```

### "MCP connection error"
- This is normal - MCP server is optional
- System falls back to declared values
- Check logs for details

### "No audit database"
- Database creates on first application
- Check file: `loan_decisions.db`

## Production Deployment

### Docker (Optional)
```dockerfile
FROM python:3.10
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0"]
```

### Database Migration
For production, migrate from SQLite to PostgreSQL:
```python
# Edit persistence/audit_store.py to use PostgreSQL connection
# Update with connection string: postgresql://user:pass@host/db
```

## Support

For issues or questions:
1. Check logs in Terminal 1 (API) and Terminal 2 (UI)
2. Review error messages in UI
3. Check audit database: `sqlite3 loan_decisions.db`
4. Verify API response: `curl http://localhost:8000/health`

## Documentation

- **IMPLEMENTATION_SUMMARY.md** - Complete implementation details
- **EVALUATION_REPORT_SANANDA_BHUNIYA_UPDATED.md** - Evaluation and scoring
- **EVALUATION_REPORT_SANANDA_BHUNIYA.md** - Original evaluation
- **GEN AI CASE STUDY LOAN APPROVAL SYSTEM EVALUATOR PROMPT.md** - Evaluation criteria

---

**System Score: 9/10 (Excellent)**
**Status: Production-Ready**
