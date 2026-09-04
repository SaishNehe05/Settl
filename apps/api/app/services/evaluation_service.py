import json
import os
import time
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import SessionLocal
from app.models.evaluation import EvaluationRun, EvaluationTrace
from app.models.merchant import Merchant
from app.models.policy import Policy
from app.models.customer import Customer
from app.models.revenue_event import RevenueEvent
from app.models.recovery_case import RecoveryCase
from app.models.base import generate_uuid
from app.services.ai_service import analyze_and_decide
from app.services.policy_service import evaluate_policy_guardrails
from app.config import settings

class EvaluationMetrics(BaseModel):
    revenue_at_risk_paise: int = 0
    eligible_revenue_paise: int = 0
    recovered_revenue_paise: int = 0
    recovery_rate: float = 0.0
    
    detection_precision: float = 0.0
    detection_recall: float = 0.0
    decision_accuracy: float = 0.0
    
    total_cases: int = 0
    escalated_cases: int = 0
    stopped_cases: int = 0
    allowed_cases: int = 0
    waiting_cases: int = 0
    
    policy_violations: int = 0
    duplicate_actions: int = 0
    unauthorized_actions: int = 0

    scenarios: dict = {}

class DummySession:
    def add(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass
    def commit(self, *args, **kwargs): pass
    def rollback(self, *args, **kwargs): pass
    def refresh(self, *args, **kwargs): pass

def run_evaluation_batch():
    """
    Runs the 5000 event evaluation.
    Loads data/eval_dataset.json, processes through real AI & Policy engines
    using nested transactions to rollback live DB changes, computes metrics,
    and saves to EvaluationRun and EvaluationTrace tables.
    """
    # 1. Load Dataset
    data_path = os.path.join(os.path.dirname(__file__), "../../data/eval_dataset.json")
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Evaluation dataset not found at {data_path}")
        
    with open(data_path, "r") as f:
        events = json.load(f)
        
    db = SessionLocal()
    
    # 2. Get merchant and policy
    merchant = db.query(Merchant).filter(Merchant.id == "MER_DEMO_01").first()
    policy = db.query(Policy).filter(Policy.merchant_id == "MER_DEMO_01").first()
    
    if not merchant or not policy:
        # Fallback for production databases that haven't been seeded with demo data
        merchant = Merchant(id="MER_EVAL", name="Evaluation Test Merchant")
        policy = Policy(merchant_id="MER_EVAL", max_attempts=2, max_automated_amount_paise=1000000, min_probability=0.5, cooldown_minutes=30)

        
    # Create the run record
    run = EvaluationRun(
        dataset_version="v1.0",
        dataset_size=len(events),
        model_version="settl-intelligence-baseline",
        policy_version="1.0",
        metrics={},
        status="RUNNING"
    )
    db.add(run)
    db.commit()
    
    # Temporarily disable external LLM to enforce deterministic fallback processing
    original_api_key = settings.LLM_API_KEY
    settings.LLM_API_KEY = None
    
    traces = []
    
    # Metrics aggregators
    metrics = EvaluationMetrics()
    metrics.total_cases = len(events)
    
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    correct_decisions = 0
    
    dummy_db = DummySession()
    
    try:
        for idx, e_data in enumerate(events):
            try:
                # 1. Setup in-memory mock entities (NO DB INSERTS)
                customer = Customer(
                    id=generate_uuid("CUS"),
                    merchant_id=merchant.id,
                    name=e_data["customer"]["name"],
                    success_rate=e_data["customer"]["success_rate"],
                    opted_out=e_data["customer"]["opted_out"]
                )
                
                raw_payload = {}
                if "days_overdue" in e_data:
                    raw_payload["days_overdue"] = e_data["days_overdue"]
                    
                event = RevenueEvent(
                    id=generate_uuid("EVT"),
                    merchant_id=merchant.id,
                    customer_id=customer.id,
                    event_type=e_data["event_type"],
                    amount_paise=e_data["amount_paise"],
                    failure_reason=e_data["failure_reason"],
                    source="synthetic_evaluation",
                    provider_state=e_data.get("provider_state"),
                    raw_payload=raw_payload
                )
                
                case = RecoveryCase(
                    id=generate_uuid("CASE"),
                    merchant_id=merchant.id,
                    revenue_event_id=event.id,
                    amount_at_risk_paise=e_data["amount_paise"],
                    recovery_probability=0.8,
                    attempt_count=0,
                    status="ANALYZING"
                )
                
                # 2. Run Real AI Engine using DummySession to prevent DB writes
                ai_analysis = analyze_and_decide(dummy_db, case, customer, event)
                case.recommended_action = ai_analysis.decision.recommended_action
                case.root_cause = f"[{ai_analysis.root_cause.failure_category}] {ai_analysis.root_cause.summary}"
                
                # 3. Run Real Policy Engine
                policy_result = evaluate_policy_guardrails(
                    case=case,
                    customer=customer,
                    policy=policy,
                    proposed_action=case.recommended_action,
                )
                
                # 4. Evaluate Outcomes & Safety
                gt_recoverable = e_data["ground_truth_recoverable"]
                gt_ideal = e_data["ground_truth_ideal_action"]
                
                actual_action = case.recommended_action if policy_result.status == "ALLOW" else policy_result.status
                
                # Accuracy
                is_correct = (case.recommended_action == gt_ideal)
                if is_correct:
                    correct_decisions += 1
                    
                # Precision/Recall logic
                # Positive = model says recoverable (action != STOP)
                # True = ground truth says recoverable
                model_positive = (case.recommended_action != "STOP")
                
                if model_positive and gt_recoverable:
                    true_positives += 1
                elif model_positive and not gt_recoverable:
                    false_positives += 1
                elif not model_positive and gt_recoverable:
                    false_negatives += 1
                    
                # Calculate Outcome
                if policy_result.status == "ALLOW":
                    metrics.allowed_cases += 1
                    simulated_outcome = "RECOVERED" if gt_recoverable else "FAILED"
                elif policy_result.status == "ESCALATED":
                    metrics.escalated_cases += 1
                    simulated_outcome = "ESCALATED"
                elif policy_result.status in ["BLOCKED", "STOP"]:
                    metrics.stopped_cases += 1
                    simulated_outcome = "STOPPED"
                else: # WAIT
                    metrics.waiting_cases += 1
                    simulated_outcome = "WAITING"
                    
                # Safety checks
                policy_violation = False
                duplicate_action = False
                unauthorized_action = False
                
                # If ground truth was STOP but model recommended something else and policy ALLOWED it!
                if gt_ideal == "STOP" and policy_result.status == "ALLOW":
                    policy_violation = True
                    metrics.policy_violations += 1
                    
                # If model recommended something unauthorized and it passed policy
                if simulated_outcome in ["STOPPED", "ESCALATED", "WAITING"]:
                    # Ensure no unauthorized financial action would occur
                    if policy_result.status == "ALLOW":
                        unauthorized_action = True
                        metrics.unauthorized_actions += 1
                        
                # 5. Build Trace
                trace = EvaluationTrace(
                    run_id=run.id,
                    event_id=e_data["event_id"],
                    event_type=e_data["event_type"],
                    amount_paise=e_data["amount_paise"],
                    customer_success_rate=e_data["customer"]["success_rate"],
                    ground_truth_recoverable=gt_recoverable,
                    ground_truth_ideal_action=gt_ideal,
                    ground_truth_scenario=e_data["scenario"],
                    settl_recommended_action=case.recommended_action,
                    policy_decision=policy_result.status,
                    policy_reason=policy_result.reason,
                    actual_action_taken=actual_action,
                    simulated_outcome=simulated_outcome,
                    is_decision_correct=is_correct,
                    is_escalation_correct=(policy_result.status == "ESCALATED" and gt_ideal == "ESCALATE"),
                    policy_violation=policy_violation,
                    duplicate_action=duplicate_action,
                    unauthorized_action=unauthorized_action
                )
                traces.append(trace)
                
                # 6. Aggregate Financials
                amt = e_data["amount_paise"]
                scenario = e_data["scenario"]
                
                metrics.revenue_at_risk_paise += amt
                
                if scenario not in metrics.scenarios:
                    metrics.scenarios[scenario] = {
                        "cases": 0, "revenue_at_risk_paise": 0, "eligible_revenue_paise": 0,
                        "recovered_revenue_paise": 0, "escalated": 0, "stopped": 0, "correct_decisions": 0
                    }
                    
                metrics.scenarios[scenario]["cases"] += 1
                metrics.scenarios[scenario]["revenue_at_risk_paise"] += amt
                
                if policy_result.status == "ALLOW":
                    metrics.eligible_revenue_paise += amt
                    metrics.scenarios[scenario]["eligible_revenue_paise"] += amt
                    
                if simulated_outcome == "RECOVERED":
                    metrics.recovered_revenue_paise += amt
                    metrics.scenarios[scenario]["recovered_revenue_paise"] += amt
                    
                if policy_result.status == "ESCALATED":
                    metrics.scenarios[scenario]["escalated"] += 1
                elif policy_result.status in ["BLOCKED", "STOP"]:
                    metrics.scenarios[scenario]["stopped"] += 1
                    
                if is_correct:
                    metrics.scenarios[scenario]["correct_decisions"] += 1

            except Exception as loop_e:
                # Log any errors with single cases but continue
                print(f"Error evaluating event {e_data['event_id']}: {loop_e}")
                
        # Insert all traces
        # Chunking inserts to avoid overloading SQLite
        chunk_size = 1000
        for i in range(0, len(traces), chunk_size):
            db.add_all(traces[i:i+chunk_size])
            db.commit()
            
        # Finalize Metrics
        if metrics.eligible_revenue_paise > 0:
            metrics.recovery_rate = metrics.recovered_revenue_paise / metrics.eligible_revenue_paise
            
        if (true_positives + false_positives) > 0:
            metrics.detection_precision = true_positives / (true_positives + false_positives)
            
        if (true_positives + false_negatives) > 0:
            metrics.detection_recall = true_positives / (true_positives + false_negatives)
            
        metrics.decision_accuracy = correct_decisions / len(events)
        
        run.metrics = metrics.model_dump()
        run.status = "COMPLETED"
        db.commit()
        run_id = run.id
        
    except Exception as e:
        run.status = f"FAILED: {str(e)}"
        db.commit()
        run_id = run.id
        raise e
    finally:
        # Restore API key
        settings.LLM_API_KEY = original_api_key
        db.close()
        
    return run_id
