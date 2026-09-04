from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import get_db
from app.models.evaluation import EvaluationRun, EvaluationTrace
from app.services.evaluation_service import run_evaluation_batch
from pydantic import BaseModel

router = APIRouter()

class RunResponse(BaseModel):
    status: str
    message: str

@router.post("/run", response_model=RunResponse)
def trigger_evaluation_run(background_tasks: BackgroundTasks):
    """
    Triggers the Batch Measurement and Safety Evaluation System.
    Runs 5,000 events through the real Settl pipeline in the background.
    """
    background_tasks.add_task(run_evaluation_batch)
    return RunResponse(
        status="success", 
        message="Evaluation batch job submitted. Results will be available shortly."
    )

@router.get("/latest")
def get_latest_evaluation(db: Session = Depends(get_db)):
    """
    Retrieves the metrics and traces from the most recent evaluation run.
    """
    run = db.query(EvaluationRun).order_by(desc(EvaluationRun.timestamp)).first()
    if not run:
        raise HTTPException(status_code=404, detail="No evaluation runs found")
        
    traces = db.query(EvaluationTrace).filter(EvaluationTrace.run_id == run.id).limit(100).all() # Return sample for UI
    
    return {
        "id": run.id,
        "dataset_version": run.dataset_version,
        "dataset_size": run.dataset_size,
        "timestamp": run.timestamp,
        "status": run.status,
        "metrics": run.metrics,
        "sample_traces": [
            {
                "id": t.id,
                "event_id": t.event_id,
                "scenario": t.ground_truth_scenario,
                "amount_paise": t.amount_paise,
                "ai_recommendation": t.settl_recommended_action,
                "policy_decision": t.policy_decision,
                "outcome": t.simulated_outcome,
                "policy_violation": t.policy_violation
            }
            for t in traces
        ]
    }
