"""
Razorpay failure-code taxonomy.

This mapping is DETERMINISTIC domain knowledge, not a model -- Razorpay's
payment.failed webhook already tells you the error_code, so there is no
classification problem here. The genuine ML problem lives one layer up:
given the category + transaction context, will a chosen intervention
actually succeed? See success_predictor.py for that.
"""

# category -> default action + whether auto-retry is even allowed
CATEGORY_POLICY = {
    "retry_later": {
        "action": "retry_after_cooldown",
        "auto_retry_allowed": True,
        "default_cooldown_hours": 24,
        "max_retries": 2,
    },
    "change_method": {
        "action": "prompt_new_payment_method",
        "auto_retry_allowed": False,   # retrying the same instrument is pointless
        "default_cooldown_hours": 0,
        "max_retries": 0,
    },
    "smart_retry": {
        "action": "retry_with_backoff",
        "auto_retry_allowed": True,
        "default_cooldown_hours": 0,   # backoff is in minutes, handled by caller
        "max_retries": 3,
    },
    "escalate": {
        "action": "escalate_to_human",
        "auto_retry_allowed": False,   # never auto-retry these, by design
        "default_cooldown_hours": 0,
        "max_retries": 0,
    },
    "user_error": {
        "action": "reprompt_customer",
        "auto_retry_allowed": False,   # don't silently retry a wrong CVV/OTP
        "default_cooldown_hours": 0,
        "max_retries": 1,
    },
}

# error_code -> category, using Razorpay's real vocabulary
ERROR_CODE_TAXONOMY = {
    # retry-later
    "insufficient_funds": "retry_later",
    "transaction_daily_limit_exceeded": "retry_later",
    "otp_attempts_exceeded": "retry_later",
    "pin_attempts_exceeded": "retry_later",
    # change-method
    "card_expired": "change_method",
    "debit_instrument_blocked": "change_method",
    "bank_account_invalid": "change_method",
    # smart-retry / transient
    "bank_technical_error": "smart_retry",
    "server_error": "smart_retry",
    "payment_timed_out": "smart_retry",
    "upi_app_technical_error": "smart_retry",
    "verification_failed": "smart_retry",
    # do-not-auto-retry / escalate
    "payment_risk_check_failed": "escalate",
    "international_transaction_not_allowed": "escalate",
    "compliance_violation": "escalate",
    # user-error
    "incorrect_cvv": "user_error",
    "incorrect_otp": "user_error",
    "invalid_vpa": "user_error",
}

# Realistic-ish incidence weights for the synthetic generator.
# insufficient_funds and timeouts are common; compliance issues are rare.
ERROR_CODE_WEIGHTS = {
    "insufficient_funds": 22,
    "transaction_daily_limit_exceeded": 4,
    "otp_attempts_exceeded": 5,
    "pin_attempts_exceeded": 3,
    "card_expired": 8,
    "debit_instrument_blocked": 3,
    "bank_account_invalid": 3,
    "bank_technical_error": 12,
    "server_error": 6,
    "payment_timed_out": 14,
    "upi_app_technical_error": 9,
    "verification_failed": 4,
    "payment_risk_check_failed": 2,
    "international_transaction_not_allowed": 1,
    "compliance_violation": 1,
    "incorrect_cvv": 5,
    "incorrect_otp": 5,
    "invalid_vpa": 3,
}


def category_for(error_code: str) -> str:
    return ERROR_CODE_TAXONOMY.get(error_code, "escalate")  # unknown codes are safest escalated


def policy_for_category(category: str) -> dict:
    return CATEGORY_POLICY[category]
