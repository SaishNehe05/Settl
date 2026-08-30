import os
from app.evaluation.dataset_generator import (
    generate_synthetic_dataset,
    load_dataset,
    DEV_DATASET_PATH,
    LOCKED_TEST_DATASET_PATH,
)
from app.evaluation.simulation_engine import run_benchmark_simulation


def test_dataset_generation_and_splits():
    dev_events, test_events = generate_synthetic_dataset(total_count=5000, seed=42)

    assert len(dev_events) == 4000
    assert len(test_events) == 1000
    assert os.path.exists(DEV_DATASET_PATH)
    assert os.path.exists(LOCKED_TEST_DATASET_PATH)

    # Verify event structure
    sample = test_events[0]
    assert "id" in sample
    assert "amount_paise" in sample
    assert "failure_reason" in sample
    assert "customer" in sample
    assert "ground_truth" in sample
    assert "is_recoverable" in sample["ground_truth"]
    assert "optimal_channel" in sample["ground_truth"]


def test_simulation_engine_comparative_advantage():
    results = run_benchmark_simulation(dataset_type="locked_test")

    assert results["total_events"] == 1000
    assert "strategies" in results

    settl = results["strategies"]["settl_ai_agent"]
    naive = results["strategies"]["naive_rule_based"]
    no_action = results["strategies"]["no_action"]

    # 1. Settl must demonstrate significantly higher precision than naive spam
    assert settl["precision"] > naive["precision"]
    assert results["lift"]["precision_improvement_pts"] > 0

    # 2. Settl must avoid significant false positive wasted attempts
    assert settl["wasted_attempts_fp"] < naive["wasted_attempts_fp"]
    assert results["lift"]["wasted_outreach_reduced_count"] > 0

    # 3. No action has zero recoveries
    assert no_action["successful_recoveries"] == 0
    assert no_action["net_recovered_inr"] == 0.0

    # 4. Guardrail blocks must be recorded
    assert settl["guardrail_blocks"] > 0


def test_evaluation_api_endpoints(client):
    # Test summary endpoint
    res = client.get("/api/v1/evaluation/summary?dataset_type=locked_test")
    assert res.status_code == 200
    data = res.json()
    assert data["total_events"] == 1000
    assert "settl_ai_agent" in data["strategies"]
    assert "naive_rule_based" in data["strategies"]
    assert "lift" in data

    # Test run endpoint
    run_res = client.post("/api/v1/evaluation/run", json={"dataset_type": "locked_test"})
    assert run_res.status_code == 200
    assert run_res.json()["dataset_type"] == "locked_test"

    # Test confusion matrix endpoint
    cm_res = client.get("/api/v1/evaluation/confusion-matrix")
    assert cm_res.status_code == 200
    cm_data = cm_res.json()
    assert "confusion_matrix" in cm_data
    assert "tp" in cm_data["confusion_matrix"]["settl"]
