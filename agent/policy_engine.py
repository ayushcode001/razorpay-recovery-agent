"""
Decides the bounded action for a failed payment by combining:
  1. Deterministic taxonomy (is auto-retry even allowed for this error?)
  2. Learned success probability (is it WORTH attempting, given context?)

This is the "every money action explainable, bounded and gated" piece.
Every decision returns a reason string suitable for the audit trail.
"""

import json
import os
from agent.taxonomy import category_for, policy_for_category

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "threshold_config.json")

def get_success_prob_threshold() -> float:
    """Loads tuned threshold if threshold_config.json exists, otherwise defaults to 0.40."""
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, "r") as f:
                cfg = json.load(f)
                return float(cfg.get("optimal_threshold", 0.40))
        except Exception:
            pass
    return 0.40

SUCCESS_PROB_THRESHOLD = get_success_prob_threshold()  # below this, don't burn an attempt -- escalate instead



def decide_action(record: dict, predicted_success_prob: float) -> dict:
    """Returns a decision dict: action, attempted, reason, category."""
    error_code = record["error_code"]
    category = category_for(error_code)
    policy = policy_for_category(category)

    if not policy["auto_retry_allowed"] and category == "escalate":
        return {
            "category": category,
            "action": "escalate_to_human",
            "attempted": False,
            "predicted_success_prob": predicted_success_prob,
            "reason": (
                f"error_code='{error_code}' is in the do-not-auto-retry class "
                f"(risk/compliance/international-block). Policy forbids autonomous "
                f"action here regardless of predicted success -- escalated to human review."
            ),
        }

    if predicted_success_prob < SUCCESS_PROB_THRESHOLD:
        return {
            "category": category,
            "action": "escalate_to_human",
            "attempted": False,
            "predicted_success_prob": predicted_success_prob,
            "reason": (
                f"Predicted success probability {predicted_success_prob:.2f} is below "
                f"threshold {SUCCESS_PROB_THRESHOLD}. Stopping rule triggered: not worth "
                f"burning an attempt (and the retry/notification cost that comes with it). "
                f"Escalated instead of acting blindly."
            ),
        }

    if record.get("retry_count", 0) >= policy["max_retries"] and policy["max_retries"] > 0:
        return {
            "category": category,
            "action": "escalate_to_human",
            "attempted": False,
            "predicted_success_prob": predicted_success_prob,
            "reason": (
                f"Max retries ({policy['max_retries']}) already reached for this "
                f"category. Stopping rule triggered to avoid spamming the customer/bank."
            ),
        }

    return {
        "category": category,
        "action": policy["action"],
        "attempted": True,
        "predicted_success_prob": predicted_success_prob,
        "reason": (
            f"error_code='{error_code}' -> category='{category}'. Predicted success "
            f"probability {predicted_success_prob:.2f} clears threshold "
            f"({SUCCESS_PROB_THRESHOLD}) and retry budget available. Executing "
            f"'{policy['action']}'."
        ),
    }
