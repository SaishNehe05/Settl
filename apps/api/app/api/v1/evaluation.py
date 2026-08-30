from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.evaluation.simulation_engine import run_benchmark_simulation

router = APIRouter(prefix="/evaluation", tags=["Evaluation Benchmark"])

# Cached benchmark results in memory for sub-second retrieval
_CACHED_BENCHMARK = None


@router.get("/summary")
def get_evaluation_summary(dataset_type: str = Query("locked_test", pattern="^(locked_test|dev)$")):
    """
    Returns comparative evaluation metrics comparing Settl Autonomous Agent
    against Naive Rule-Based and No-Action baselines on the 1,000 locked test dataset.
    """
    global _CACHED_BENCHMARK
    if _CACHED_BENCHMARK is None or _CACHED_BENCHMARK.get("dataset_type") != dataset_type:
        _CACHED_BENCHMARK = run_benchmark_simulation(dataset_type)
    return _CACHED_BENCHMARK


class RunEvaluationRequest(BaseModel):
    dataset_type: Optional[str] = "locked_test"


@router.post("/run")
def run_evaluation_benchmark(req: Optional[RunEvaluationRequest] = None):
    """
    Executes a fresh evaluation benchmark run on the synthetic dataset
    and returns refreshed metrics.
    """
    global _CACHED_BENCHMARK
    dataset_type = req.dataset_type if req and req.dataset_type else "locked_test"
    if dataset_type not in ["locked_test", "dev"]:
        raise HTTPException(status_code=400, detail="dataset_type must be 'locked_test' or 'dev'")

    _CACHED_BENCHMARK = run_benchmark_simulation(dataset_type)
    return _CACHED_BENCHMARK


@router.get("/confusion-matrix")
def get_confusion_matrix(dataset_type: str = Query("locked_test", pattern="^(locked_test|dev)$")):
    """
    Returns detailed confusion matrix (TP, FP, TN, FN) for Settl vs Baseline.
    """
    summary = get_evaluation_summary(dataset_type)
    return {
        "dataset_type": dataset_type,
        "confusion_matrix": summary["confusion_matrix"],
        "metrics": {
            "settl_precision": summary["strategies"]["settl_ai_agent"]["precision"],
            "settl_recall": summary["strategies"]["settl_ai_agent"]["recall"],
            "settl_f1": summary["strategies"]["settl_ai_agent"]["f1_score"],
            "naive_precision": summary["strategies"]["naive_rule_based"]["precision"],
            "naive_recall": summary["strategies"]["naive_rule_based"]["recall"],
            "naive_f1": summary["strategies"]["naive_rule_based"]["f1_score"],
        }
    }
