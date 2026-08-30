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

# Threshold source of truth: threshold_config.json (tuned to 0.47 via 5-seed cross-validation)
SUCCESS_PROB_THRESHOLD = get_success_prob_threshold()  # below this (0.47), don't burn an attempt -- escalate instead
UPLIFT_THRESHOLD = 0.05  # below this, intervention adds negligible causal lift; skip to avoid wasted cost



def decide_action(record: dict, predicted_success_prob: float, estimated_uplift: float | None = None) -> dict:
    """
    Returns a decision dict: action, attempted, reason, category, predicted_success_prob, estimated_uplift.
    
    Decision pipeline:
      1. Deterministic Taxonomy Gate (risk/compliance never auto-actioned)
      2. Success Probability Gate (P >= SUCCESS_PROB_THRESHOLD)
      3. Retry Budget Gate (retry_count < max_retries)
      4. Causal Uplift Gate (estimated_uplift >= UPLIFT_THRESHOLD if provided)
    """
    error_code = record["error_code"]
    category = category_for(error_code)
    policy = policy_for_category(category)

    if not policy["auto_retry_allowed"] and category == "escalate":
        return {
            "category": category,
            "action": "escalate_to_human",
            "attempted": False,
            "predicted_success_prob": predicted_success_prob,
            "estimated_uplift": estimated_uplift,
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
            "estimated_uplift": estimated_uplift,
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
            "estimated_uplift": estimated_uplift,
            "reason": (
                f"Max retries ({policy['max_retries']}) already reached for this "
                f"category. Stopping rule triggered to avoid spamming the customer/bank."
            ),
        }

    # Uplift Refinement Layer: If uplift model is active and predicts negligible lift over self-recovery
    if estimated_uplift is not None and estimated_uplift < UPLIFT_THRESHOLD:
        return {
            "category": category,
            "action": "skipped_low_uplift",
            "attempted": False,
            "predicted_success_prob": predicted_success_prob,
            "estimated_uplift": estimated_uplift,
            "reason": (
                f"P(success)={predicted_success_prob:.2f} clears threshold, but estimated "
                f"uplift is only {estimated_uplift:.3f} (< {UPLIFT_THRESHOLD:.2f}). Customer is likely to self-recover; "
                f"intervention skipped to avoid wasted cost."
            ),
        }

    uplift_str = f", estimated uplift={estimated_uplift:.2f}" if estimated_uplift is not None else ""
    return {
        "category": category,
        "action": policy["action"],
        "attempted": True,
        "predicted_success_prob": predicted_success_prob,
        "estimated_uplift": estimated_uplift,
        "reason": (
            f"error_code='{error_code}' -> category='{category}'. Predicted success "
            f"probability {predicted_success_prob:.2f} clears threshold "
            f"({SUCCESS_PROB_THRESHOLD}){uplift_str} and retry budget available. Executing "
            f"'{policy['action']}'."
        ),
    }
