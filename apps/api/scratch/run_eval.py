import sys
import os

# Add apps/api to sys path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.evaluation_service import run_evaluation_batch

print("Starting evaluation batch...")
try:
    run_id = run_evaluation_batch()
    print(f"Success! Run ID: {run_id}")
except Exception as e:
    print(f"Evaluation failed: {e}")
    import traceback
    traceback.print_exc()
