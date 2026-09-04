import json
import random
import os

def generate_payment_failure(event_id: str) -> dict:
    reasons = [
        ("insufficient_funds", True, "WAIT"),
        ("temporary_bank_failure", True, "CREATE_PAYMENT_LINK"),
        ("gateway_timeout", True, "CREATE_PAYMENT_LINK"),
        ("card_expired", False, "STOP"),
        ("suspected_fraud", False, "STOP"),
        ("high_value_failure", True, "ESCALATE") # We will set amount > 10000
    ]
    reason, recov, ideal = random.choice(reasons)
    
    amt = random.randint(500, 5000) * 100
    if reason == "high_value_failure":
        amt = random.randint(11000, 50000) * 100
        
    return {
        "event_id": event_id,
        "event_type": "PAYMENT_FAILED",
        "scenario": "Payment Failure",
        "amount_paise": amt,
        "failure_reason": reason,
        "customer": {
            "name": f"User_{event_id}",
            "success_rate": round(random.uniform(0.1, 0.99), 2),
            "opted_out": random.random() < 0.05
        },
        "ground_truth_recoverable": False if random.random() < 0.05 else recov, # Add some noise where customer opted out makes it unrecoverable
        "ground_truth_ideal_action": ideal
    }

def generate_checkout_abandonment(event_id: str) -> dict:
    return {
        "event_id": event_id,
        "event_type": "CHECKOUT_ABANDONED",
        "scenario": "Checkout Abandonment",
        "amount_paise": random.randint(500, 10000) * 100,
        "failure_reason": "session_timeout",
        "customer": {
            "name": f"User_{event_id}",
            "success_rate": round(random.uniform(0.1, 0.99), 2),
            "opted_out": random.random() < 0.05
        },
        "ground_truth_recoverable": True,
        "ground_truth_ideal_action": "SEND_REMINDER" # or CREATE_PAYMENT_LINK
    }

def generate_subscription_failure(event_id: str) -> dict:
    reasons = [
        ("subscription_pending", True, "WAIT"),
        ("subscription_halted", True, "CUSTOMER_ACTION_REQUIRED"),
    ]
    reason, recov, ideal = random.choice(reasons)
    return {
        "event_id": event_id,
        "event_type": "SUBSCRIPTION_FAILED",
        "scenario": "Subscription Failure",
        "amount_paise": random.randint(199, 2999) * 100,
        "failure_reason": reason,
        "provider_state": reason.split("_")[1], # pending or halted
        "customer": {
            "name": f"User_{event_id}",
            "success_rate": round(random.uniform(0.1, 0.99), 2),
            "opted_out": random.random() < 0.05
        },
        "ground_truth_recoverable": recov,
        "ground_truth_ideal_action": ideal
    }

def generate_overdue_receivable(event_id: str) -> dict:
    days_overdue = random.choice([1, 4, 10])
    if days_overdue >= 7:
        ideal = "CREATE_COLLECTION_CASE"
    elif days_overdue >= 3:
        ideal = "SEND_FOLLOW_UP"
    else:
        ideal = "SEND_REMINDER"
        
    amt = random.randint(5000, 500000) * 100
    if amt > 10000000:
        ideal = "ESCALATE"
        
    return {
        "event_id": event_id,
        "event_type": "INVOICE_OVERDUE",
        "scenario": "Overdue Receivable",
        "amount_paise": amt,
        "failure_reason": "payment_terms_exceeded",
        "days_overdue": days_overdue,
        "customer": {
            "name": f"B2B_{event_id}",
            "success_rate": round(random.uniform(0.5, 0.99), 2),
            "opted_out": False
        },
        "ground_truth_recoverable": True,
        "ground_truth_ideal_action": ideal
    }

def main():
    random.seed(42) # Deterministic
    events = []
    
    # 2000 Payment Failure
    for i in range(2000):
        events.append(generate_payment_failure(f"SYN_PF_{i}"))
        
    # 1500 Checkout Abandonment
    for i in range(1500):
        events.append(generate_checkout_abandonment(f"SYN_CA_{i}"))
        
    # 1000 Subscription Failure
    for i in range(1000):
        events.append(generate_subscription_failure(f"SYN_SF_{i}"))
        
    # 500 Overdue Receivable
    for i in range(500):
        events.append(generate_overdue_receivable(f"SYN_OR_{i}"))
        
    # Correct ground truth for opt outs and high values to strictly match policy engine
    for e in events:
        # If opted out, policy will block
        if e["customer"]["opted_out"]:
            e["ground_truth_ideal_action"] = "STOP"
            e["ground_truth_recoverable"] = False
        
        # If amount > 10,000 (1000000 paise), policy will escalate
        if e["amount_paise"] > 1000000 and e["scenario"] != "Overdue Receivable":
            e["ground_truth_ideal_action"] = "ESCALATE"
            e["ground_truth_recoverable"] = False
            
    # Write to data directory
    output_path = os.path.join(os.path.dirname(__file__), "../../data")
    os.makedirs(output_path, exist_ok=True)
    file_path = os.path.join(output_path, "eval_dataset.json")
    
    with open(file_path, "w") as f:
        json.dump(events, f, indent=2)
        
    print(f"Generated {len(events)} synthetic events at {file_path}")

if __name__ == "__main__":
    main()
