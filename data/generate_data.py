"""
Generates a synthetic-but-schema-accurate dataset of failed Razorpay payments.

Fields mirror the real payment.failed webhook payload:
id, amount, method, bank, card{network,type,last4}, error_code,
error_description, error_source, error_step, created_at

Additionally simulates whether a recovery attempt WOULD succeed, so we have
labeled data to train the success predictor on. This label is what a real
deployment would collect from actual retry outcomes over time -- here it's
simulated with a plausible probability model per category/context so the
generator itself has no info leakage into the model beyond what a real
account would eventually observe.
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

from agent.taxonomy import ERROR_CODE_WEIGHTS, category_for

random.seed(42)

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

# Base success probability if a retry/intervention IS attempted, by category.
# This is the ground truth the ML model has to learn back out from features.
BASE_SUCCESS_PROB = {
    "retry_later": 0.55,
    "change_method": 0.70,   # prompting a new method works most of the time
    "smart_retry": 0.60,
    "escalate": 0.08,        # these mostly shouldn't be retried at all
    "user_error": 0.65,      # re-prompting usually fixes it
}

# Base self-recovery probability WITHOUT any intervention (control arm baseline)
BASE_SELF_RECOVERY_PROB = {
    "smart_retry": 0.30,     # transient -- customer's own retry might just work
    "retry_later": 0.10,     # needs funds to appear; low self-recovery
    "change_method": 0.08,   # needs nudge to switch; low self-recovery
    "escalate": 0.02,        # near-zero; risk/compliance rarely self-resolve
    "user_error": 0.15,      # customer may retry with correct details
}


def _rand_id(prefix):
    return prefix + "_" + "".join(random.choices(string.ascii_letters + string.digits, k=14))


def weighted_error_code():
    codes = list(ERROR_CODE_WEIGHTS.keys())
    weights = list(ERROR_CODE_WEIGHTS.values())
    return random.choices(codes, weights=weights, k=1)[0]


def simulate_outcome(category, amount, retry_count, hour_of_day):
    """Ground-truth simulation of whether an attempted intervention succeeds.
    Real signal + noise, mirroring real-world factors: higher amounts are
    slightly harder to recover, more prior retries hurt, and late-night
    attempts (issuer systems flakier) hurt slightly."""
    p = BASE_SUCCESS_PROB[category]
    if amount > 50000:
        p -= 0.10
    if retry_count >= 2:
        p -= 0.15
    if hour_of_day < 6 or hour_of_day > 23:
        p -= 0.05
    p = max(0.02, min(0.95, p))
    return 1 if random.random() < p else 0


def simulate_self_recovery(category, amount, retry_count, hour_of_day):
    """Ground-truth baseline self-recovery probability without intervention."""
    p0 = BASE_SELF_RECOVERY_PROB[category]
    if amount > 50000:
        p0 -= 0.03
    if retry_count >= 2:
        p0 -= 0.04
    if hour_of_day < 6 or hour_of_day > 23:
        p0 -= 0.02
    p0 = max(0.01, min(0.50, p0))
    return round(p0, 4)


def generate_record(base_time):
    error_code = weighted_error_code()
    category = category_for(error_code)
    method = METHODS_BY_CODE_HINT.get(error_code, random.choices(
        ["card", "upi", "netbanking"], weights=[50, 40, 10], k=1)[0])

    amount = int(random.choice([
        random.randint(199, 2000),
        random.randint(2000, 15000),
        random.randint(15000, 150000),
    ]))

    retry_count = random.choices([0, 1, 2, 3], weights=[55, 25, 12, 8], k=1)[0]
    created_at = base_time - timedelta(minutes=random.randint(0, 60 * 24 * 14))
    hour_of_day = created_at.hour

    recovery_succeeded = simulate_outcome(category, amount, retry_count, hour_of_day)
    p0 = simulate_self_recovery(category, amount, retry_count, hour_of_day)
    
    # 50/50 randomized experiment assignment for T-learner uplift modeling
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
        # ground truth label for training / eval -- would come from real retry
        # outcomes in production, simulated here:
        "recovery_attempted": True,
        "recovery_succeeded": recovery_succeeded,
        "p0_self_recovery": p0,
        "treatment": treatment,
        "observed_outcome": observed_outcome,
        "_category": category,  # kept for eval convenience, not a model input
    }
    return record


def generate_dataset(n=250):
    base_time = datetime.now()
    return [generate_record(base_time) for _ in range(n)]


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 250
    dataset = generate_dataset(n)
    out_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(PROJECT_ROOT, "data", "synthetic_failed_payments.json")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"Generated {n} records -> {out_path}")

    # quick distribution sanity check
    from collections import Counter
    cat_counts = Counter(r["_category"] for r in dataset)
    print("Category distribution:", dict(cat_counts))
    total_amount = sum(r["amount"] for r in dataset)
    print(f"Total amount at risk: Rs.{total_amount:,}")
