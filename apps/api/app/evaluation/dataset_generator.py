import json
import os
import random
from typing import List, Dict, Any, Tuple

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
DEV_DATASET_PATH = os.path.join(DATA_DIR, "evaluation_dev_4000.json")
LOCKED_TEST_DATASET_PATH = os.path.join(DATA_DIR, "evaluation_locked_test_1000.json")

# Failure reasons with their latent real-world recoverability probabilities
FAILURE_PROFILES = [
    {
        "reason": "temporary_bank_failure",
        "category": "BANK_TECHNICAL",
        "weight": 0.35,
        "base_recoverability": 0.88,
        "event_type": "PAYMENT_FAILED",
        "suggested_channel": "WHATSAPP",
    },
    {
        "reason": "gateway_timeout",
        "category": "BANK_TECHNICAL",
        "weight": 0.20,
        "base_recoverability": 0.82,
        "event_type": "PAYMENT_FAILED",
        "suggested_channel": "WHATSAPP",
    },
    {
        "reason": "session_timeout",
        "category": "CUSTOMER_SESSION",
        "weight": 0.20,
        "base_recoverability": 0.76,
        "event_type": "CHECKOUT_ABANDONED",
        "suggested_channel": "WHATSAPP",
    },
    {
        "reason": "otp_expired_or_failed",
        "category": "AUTHENTICATION",
        "weight": 0.12,
        "base_recoverability": 0.65,
        "event_type": "PAYMENT_FAILED",
        "suggested_channel": "SMS",
    },
    {
        "reason": "insufficient_funds",
        "category": "INSUFFICIENT_FUNDS",
        "weight": 0.10,
        "base_recoverability": 0.18,
        "event_type": "PAYMENT_FAILED",
        "suggested_channel": "EMAIL",
    },
    {
        "reason": "card_declined_fraud_suspected",
        "category": "FRAUD_RISK",
        "weight": 0.03,
        "base_recoverability": 0.04,
        "event_type": "PAYMENT_FAILED",
        "suggested_channel": "EMAIL",
    },
]

CUSTOMER_NAMES = [
    "Aarav Sharma", "Vivaan Patel", "Aditya Verma", "Vihaan Iyer", "Arjun Reddy",
    "Sai Krishna", "Reyansh Gupta", "Ayaan Joshi", "Krishna Nair", "Ishaan Malhotra",
    "Ananya Sen", "Diya Mukherjee", "Saanvi Rao", "Aadhya Menon", "Kiara Kapoor",
    "Pari Saxena", "Myra Agarwal", "Riya Choudhury", "Anika Deshmukh", "Navya Bhat",
]


def generate_synthetic_dataset(total_count: int = 5000, seed: int = 42) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Generates 5,000 realistic e-commerce revenue leakage events with ground-truth
    labels and splits into 4,000 Dev and 1,000 Locked Test sets.
    """
    random.seed(seed)
    os.makedirs(DATA_DIR, exist_ok=True)

    # 1. Generate 1,000 customer cohorts
    customers = []
    for i in range(1000):
        c_tier = random.choices(["HIGH", "MEDIUM", "LOW"], weights=[0.25, 0.50, 0.25])[0]
        base_rate = 0.90 if c_tier == "HIGH" else (0.75 if c_tier == "MEDIUM" else 0.50)
        success_rate = max(0.10, min(0.99, random.gauss(base_rate, 0.12)))
        opted_out = random.random() < 0.05  # 5% have opted out

        customers.append({
            "id": f"CUST_SYN_{i:04d}",
            "name": f"{random.choice(CUSTOMER_NAMES)} {i}",
            "email": f"cust_{i:04d}@example.in",
            "phone": f"+9198{random.randint(10000000, 99999999)}",
            "success_rate": round(success_rate, 2),
            "customer_value": c_tier,
            "opted_out": opted_out,
        })

    # 2. Generate 5,000 revenue leakage events
    events = []
    reasons = [p["reason"] for p in FAILURE_PROFILES]
    weights = [p["weight"] for p in FAILURE_PROFILES]
    profile_map = {p["reason"]: p for p in FAILURE_PROFILES}

    for i in range(total_count):
        cust = random.choice(customers)
        reason = random.choices(reasons, weights=weights)[0]
        prof = profile_map[reason]

        # Amounts: log-normal distribution centered around ₹3,500
        raw_amt_inr = int(random.lognormvariate(8.1, 0.75))
        amt_inr = max(499, min(45000, raw_amt_inr))
        amount_paise = amt_inr * 100

        # Determine true latent recoverability
        prob_recover = prof["base_recoverability"] * (0.8 + 0.3 * cust["success_rate"])
        if cust["opted_out"]:
            prob_recover = 0.0  # Cannot recover if customer opted out of communication
        if prof["category"] == "FRAUD_RISK":
            prob_recover = 0.02

        is_recoverable = random.random() < min(0.95, max(0.02, prob_recover))

        # Ground truth optimal action
        if cust["opted_out"]:
            optimal_action = "STOP"
        elif amt_inr > 10000:
            optimal_action = "ESCALATE"
        elif is_recoverable:
            optimal_action = "CREATE_PAYMENT_LINK"
        else:
            optimal_action = "STOP"

        event = {
            "id": f"EVT_SYN_{i:05d}",
            "event_type": prof["event_type"],
            "amount_paise": amount_paise,
            "amount_inr": amt_inr,
            "failure_reason": reason,
            "failure_category": prof["category"],
            "customer": cust,
            "ground_truth": {
                "is_recoverable": is_recoverable,
                "optimal_action": optimal_action,
                "optimal_channel": prof["suggested_channel"],
                "latent_recovery_prob": round(prob_recover, 3),
            }
        }
        events.append(event)

    # 3. Split 4,000 Dev / 1,000 Locked Test
    dev_events = events[:4000]
    locked_test_events = events[4000:]

    with open(DEV_DATASET_PATH, "w", encoding="utf-8") as f:
        json.dump(dev_events, f, indent=2)

    with open(LOCKED_TEST_DATASET_PATH, "w", encoding="utf-8") as f:
        json.dump(locked_test_events, f, indent=2)

    return dev_events, locked_test_events


def load_dataset(dataset_type: str = "locked_test") -> List[Dict[str, Any]]:
    """
    Loads either the 1,000 locked test dataset or the 4,000 development dataset.
    Generates them deterministically if not yet present on disk.
    """
    if not os.path.exists(LOCKED_TEST_DATASET_PATH) or not os.path.exists(DEV_DATASET_PATH):
        generate_synthetic_dataset()

    target_path = LOCKED_TEST_DATASET_PATH if dataset_type == "locked_test" else DEV_DATASET_PATH
    with open(target_path, "r", encoding="utf-8") as f:
        return json.load(f)
