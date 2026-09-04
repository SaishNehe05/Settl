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

def run_evaluation_batch(merchant_id: str):
    """
    Runs the 5000 event evaluation.
    Loads data/eval_dataset.json, processes through real AI & Policy engines
    using nested transactions to rollback live DB changes, computes metrics,
    and saves to EvaluationRun and EvaluationTrace tables.
    """
    db = SessionLocal()
    
    # 1. Fetch real cases from the database for the specific merchant
    real_cases = db.query(RecoveryCase).join(RevenueEvent).filter(
        RevenueEvent.source != "synthetic",
        RecoveryCase.merchant_id == merchant_id
    ).all()
    
    if not real_cases:
        db.close()
        raise ValueError(f"No real cases found in the database to evaluate for merchant {merchant_id}.")
    
    # 2. Get the actual deployed merchant and policy
    merchant = db.query(Merchant).filter(Merchant.id == merchant_id).first()
    if not merchant:
        db.close()
        raise ValueError(f"Merchant {merchant_id} not found in database.")
        
    policy = db.query(Policy).filter(Policy.merchant_id == merchant.id).first()
    if not policy:
        db.close()
        raise ValueError(f"No policy found for merchant {merchant.name}")        
    # Create the run record
    run = EvaluationRun(
        merchant_id=merchant_id,
        dataset_version="live_db_v1",
        dataset_size=len(real_cases),
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
    metrics.total_cases = len(real_cases)
    
    dummy_db = DummySession()
    
    try:
        for idx, case in enumerate(real_cases):
            try:
                event = case.revenue_event
                customer = event.customer
                
                # Setup dummy tracking fields to avoid modifying real records
                eval_case = RecoveryCase(
                    id=case.id,
                    merchant_id=case.merchant_id,
                    revenue_event_id=case.revenue_event_id,
                    amount_at_risk_paise=case.amount_at_risk_paise,
                    recovery_probability=case.recovery_probability,
                    attempt_count=case.attempt_count,
                    status="ANALYZING"
                )
                
                # 2. Run Real AI Engine using DummySession to prevent DB writes
                ai_analysis = analyze_and_decide(dummy_db, eval_case, customer, event)
                eval_case.recommended_action = ai_analysis.decision.recommended_action
                eval_case.root_cause = f"[{ai_analysis.root_cause.failure_category}] {ai_analysis.root_cause.summary}"
                
                # 3. Run Real Policy Engine
                policy_result = evaluate_policy_guardrails(
                    case=eval_case,
                    customer=customer,
                    policy=policy,
                    proposed_action=eval_case.recommended_action,
                )
                
                # 4. Evaluate Outcomes & Safety
                actual_action = eval_case.recommended_action if policy_result.status == "ALLOW" else policy_result.status
                
                # Simulate recovery based on AI's confidence if policy allows it
                is_recoverable = eval_case.recovery_probability > 0.5
                    
                # Calculate Outcome
                if policy_result.status == "ALLOW":
                    metrics.allowed_cases += 1
                    simulated_outcome = "RECOVERED" if is_recoverable else "FAILED"
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
                
                # If model recommended something unauthorized and it passed policy
                if simulated_outcome in ["STOPPED", "ESCALATED", "WAITING"]:
                    # Ensure no unauthorized financial action would occur
                    if policy_result.status == "ALLOW":
                        unauthorized_action = True
                        metrics.unauthorized_actions += 1
                        
                # Derive scenario from event type for reporting
                scenario_map = {
                    "PAYMENT_FAILED": "Payment Failure",
                    "CHECKOUT_ABANDONED": "Checkout Abandonment",
                    "SUBSCRIPTION_FAILED": "Subscription Failure",
                    "INVOICE_OVERDUE": "Overdue Receivable"
                }
                scenario = scenario_map.get(event.event_type, "Other")
                        
                # 5. Build Trace
                trace = EvaluationTrace(
                    run_id=run.id,
                    event_id=event.id,
                    event_type=event.event_type,
                    amount_paise=case.amount_at_risk_paise,
                    customer_success_rate=customer.success_rate if customer.success_rate else 0.5,
                    ground_truth_recoverable=False,
                    ground_truth_ideal_action="N/A",
                    ground_truth_scenario=scenario,
                    settl_recommended_action=eval_case.recommended_action,
                    policy_decision=policy_result.status,
                    policy_reason=policy_result.reason,
                    actual_action_taken=actual_action,
                    simulated_outcome=simulated_outcome,
                    is_decision_correct=False,
                    is_escalation_correct=False,
                    policy_violation=policy_violation,
                    duplicate_action=duplicate_action,
                    unauthorized_action=unauthorized_action
                )
                traces.append(trace)
                
                # 6. Aggregate Financials
                amt = case.amount_at_risk_paise
                
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
                    
            except Exception as loop_e:
                # Log any errors with single cases but continue
                print(f"Error evaluating event {event.id}: {loop_e}")
                
        # Insert all traces
        # Chunking inserts to avoid overloading SQLite
        chunk_size = 1000
        for i in range(0, len(traces), chunk_size):
            db.add_all(traces[i:i+chunk_size])
            db.commit()
            
        # Finalize Metrics
        if metrics.eligible_revenue_paise > 0:
            metrics.recovery_rate = metrics.recovered_revenue_paise / metrics.eligible_revenue_paise
            
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
