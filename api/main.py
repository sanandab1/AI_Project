from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from loan_ai_system.models.schemas import LoanApplication
from loan_ai_system.orchestration.graph import run_workflow
from loan_ai_system.services.logger_service import StructuredLogger

app = FastAPI(title="Loan Approval System API", version="1.0.0")
logger = StructuredLogger(__name__)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "loan-approval-api"}


@app.post("/loan/process")
def process_loan(app_data: LoanApplication):
    """
    Process a loan application and return decision

    Args:
        app_data: LoanApplication with applicant details

    Returns:
        Decision result with explanation and compliance info
    """
    try:
        logger.info(
            "Processing loan application",
            applicant_id=app_data.applicant_id,
            loan_amount=app_data.loan_amount
        )

        # Run the workflow
        result = run_workflow(app_data)

        # Ensure result is a dict
        if isinstance(result, dict):
            decision_data = result.get("decision", {})
            if isinstance(decision_data, dict):
                decision_class = decision_data.get("classification")
            else:
                decision_class = getattr(decision_data, "classification", "UNKNOWN")
        else:
            decision_class = "UNKNOWN"

        logger.info(
            "Loan application processed successfully",
            applicant_id=app_data.applicant_id,
            decision=decision_class
        )

        return result

    except ValueError as e:
        logger.error(f"Invalid input: {str(e)}", applicant_id=app_data.applicant_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )

    except Exception as e:
        logger.error(
            f"Error processing loan application: {str(e)}",
            applicant_id=app_data.applicant_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing loan application. Please try again later."
        )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", path=request.url.path)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )
