"""
Generates a synthetic shifted dataset representing a "30 days later" drift scenario.

CONSTRUCTED DRIFT SCENARIO FOR DEMONSTRATION:
Simulates a real-world macroeconomic and bank infrastructure shift:
  1. Emerging Issuer Degradation: bank_technical_error and payment_timed_out surge.
  2. Consumer App Shift: Popular UPI app update alters retry UI, lowering organic self-recovery.
  3. Gateway Success Degradation: Transient failure recovery rate drops.

This dataset is used by agent/drift_check.py to evaluate whether the original
calibrated models have gone stale, and to propose a policy update.
"""

import json
import os
import random
import string
import sys
from datetime import datetime, timedelta

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.taxonomy import category_for

# Seed for reproducible drift scenario
random.seed(99)

BANKS = ["HDFC", "ICICI", "SBI", "Axis", "Kotak", "Yes Bank", "IDFC First"]
CARD_NETWORKS = ["Visa", "Mastercard", "RuPay", "Amex"]
METHODS_BY_CODE_HINT = {
    "invalid_vpa": "upi",
    "upi_app_technical_error": "upi",
    "bank_account_invalid": "netbanking",
}

ERROR_DESCRIPTIONS = {
    "insufficient_funds": "Payment failed due to insufficient funds in the customer's account.",
    "transaction_daily_limit_exceeded": "Daily transaction limit exceeded for this instrument.",
    "otp_attempts_exceeded": "Maximum OTP attempts exceeded.",
    "pin_attempts_exceeded": "Maximum PIN attempts exceeded.",
    "card_expired": "The card has expired.",
    "debit_instrument_blocked": "The debit instrument is blocked by the issuer.",
    "bank_account_invalid": "The bank account details are invalid.",
    "bank_technical_error": "Payment failed due to a technical error at the bank's end.",
    "server_error": "Payment failed due to an internal server error.",
    "payment_timed_out": "The payment timed out.",
    "upi_app_technical_error": "The UPI app encountered a technical error.",
    "verification_failed": "Verification of the payment could not be completed.",
    "payment_risk_check_failed": "Payment failed the risk check.",
    "international_transaction_not_allowed": "International transactions are not enabled for this instrument.",
    "compliance_violation": "Transaction blocked due to a compliance violation.",
    "incorrect_cvv": "The CVV entered is incorrect.",
    "incorrect_otp": "The OTP entered is incorrect.",
    "invalid_vpa": "The VPA entered is invalid.",
}

# Shifted error weights: High bank_technical_error & payment_timed_out surge
SHIFTED_ERROR_CODE_WEIGHTS = {
    "insufficient_funds": 14,
    "transaction_daily_limit_exceeded": 3,
    "otp_attempts_exceeded": 4,
    "pin_attempts_exceeded": 2,
    "card_expired": 5,
    "debit_instrument_blocked": 2,
    "bank_account_invalid": 2,
    "bank_technical_error": 32,      # Surge from 12 -> 32 (Issuer outage/flakiness)
    "server_error": 8,
    "payment_timed_out": 22,         # Surge from 14 -> 22
    "upi_app_technical_error": 12,
    "verification_failed": 3,
    "payment_risk_check_failed": 2,
    "international_transaction_not_allowed": 1,
    "compliance_violation": 1,
    "incorrect_cvv": 3,
    "incorrect_otp": 3,
    "invalid_vpa": 2,
}

# Shifted intervention success probability: transient smart_retries are harder due to bank congestion
SHIFTED_SUCCESS_PROB = {
    "retry_later": 0.48,     # dropped from 0.55
    "change_method": 0.68,   # slightly stable
    "smart_retry": 0.40,     # dropped from 0.60 (severe bank gateway congestion)
    "escalate": 0.05,        # low
    "user_error": 0.60,      # dropped from 0.65
}

# Shifted self-recovery probability (UPI app UI change reduced user self-retries)
SHIFTED_SELF_RECOVERY_PROB = {
    "smart_retry": 0.14,     # dropped from 0.30 (users abandon rather than retrying manually)
    "retry_later": 0.06,
    "change_method": 0.05,
    "escalate": 0.01,
    "user_error": 0.10,
}


def _rand_id(prefix):
    return prefix + "_" + "".join(random.choices(string.ascii_letters + string.digits, k=14))


def weighted_shifted_error_code():
    codes = list(SHIFTED_ERROR_CODE_WEIGHTS.keys())
    weights = list(SHIFTED_ERROR_CODE_WEIGHTS.values())
    return random.choices(codes, weights=weights, k=1)[0]


def simulate_shifted_outcome(category, amount, retry_count, hour_of_day):
    p = SHIFTED_SUCCESS_PROB[category]
    if amount > 50000:
        p -= 0.12
    if retry_count >= 2:
        p -= 0.18
    if hour_of_day < 6 or hour_of_day > 23:
        p -= 0.08
    p = max(0.02, min(0.95, p))
    return 1 if random.random() < p else 0


def simulate_shifted_self_recovery(category, amount, retry_count, hour_of_day):
    p0 = SHIFTED_SELF_RECOVERY_PROB[category]
    if amount > 50000:
        p0 -= 0.04
    if retry_count >= 2:
        p0 -= 0.05
    if hour_of_day < 6 or hour_of_day > 23:
        p0 -= 0.03
    p0 = max(0.01, min(0.50, p0))
    return round(p0, 4)


def generate_drift_record(base_time):
    error_code = weighted_shifted_error_code()
    category = category_for(error_code)
    method = METHODS_BY_CODE_HINT.get(error_code, random.choices(
        ["card", "upi", "netbanking"], weights=[45, 45, 10], k=1)[0])

    amount = int(random.choice([
        random.randint(199, 2500),
        random.randint(2500, 20000),
        random.randint(20000, 160000),
    ]))

    retry_count = random.choices([0, 1, 2, 3], weights=[50, 28, 14, 8], k=1)[0]
    created_at = base_time + timedelta(days=30) - timedelta(minutes=random.randint(0, 60 * 24 * 14))
    hour_of_day = created_at.hour

    recovery_succeeded = simulate_shifted_outcome(category, amount, retry_count, hour_of_day)
    p0 = simulate_shifted_self_recovery(category, amount, retry_count, hour_of_day)
    
    treatment = 1 if random.random() < 0.5 else 0
    if treatment == 1:
        observed_outcome = recovery_succeeded
    else:
        observed_outcome = 1 if random.random() < p0 else 0

    record = {
        "id": _rand_id("pay"),
        "amount": amount,
        "currency": "INR",
        "method": method,
        "bank": random.choice(BANKS) if method in ("netbanking", "card") else None,
        "card": {
            "network": random.choice(CARD_NETWORKS),
            "type": random.choice(["credit", "debit"]),
            "last4": f"{random.randint(1000,9999)}",
        } if method == "card" else None,
        "vpa": f"user{random.randint(1000,9999)}@{random.choice(['okhdfcbank','oksbi','okicici','ybl'])}"
               if method == "upi" else None,
        "error_code": error_code,
        "error_description": ERROR_DESCRIPTIONS[error_code],
        "error_source": random.choice(["issuer", "gateway", "razorpay", "customer"]),
        "error_step": random.choice(["payment_authentication", "payment_authorization", "payment_processing"]),
        "error_reason": error_code,
        "created_at": int(created_at.timestamp()),
        "retry_count": retry_count,
        "recovery_attempted": True,
        "recovery_succeeded": recovery_succeeded,
        "p0_self_recovery": p0,
        "treatment": treatment,
        "observed_outcome": observed_outcome,
        "_category": category,
        "_scenario": "simulated_drift_batch_30d",
    }
    return record


def generate_drift_dataset(n=1200):
    base_time = datetime.now()
    return [generate_drift_record(base_time) for _ in range(n)]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 1200
    dataset = generate_drift_dataset(n)
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PROJECT_ROOT, "data", "drift_batch_30d.json")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)
    print(f"Generated {n} drift records -> {out_path}")

    from collections import Counter
    cat_counts = Counter(r["_category"] for r in dataset)
    print("Category distribution:", dict(cat_counts))
    total_amount = sum(r["amount"] for r in dataset)
    print(f"Total amount at risk: Rs.{total_amount:,}")
