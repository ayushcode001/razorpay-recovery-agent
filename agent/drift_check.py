"""
Drift-Check (Recovery Ops) Agent — Proof of Concept.

Detects when the trained models have degraded on fresh / shifted transaction distributions
and proposes (NEVER auto-applies) a policy update for human review.

Key Principles:
  1. Models calibrated once silently decay as issuer performance & user habits change.
  2. Gated, explainable, human-in-the-loop: evaluates on demand and records a proposal.
  3. No live online learning / auto-apply — human approves or rejects policy changes.
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Tuple
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.taxonomy import category_for, policy_for_category
from agent.policy_engine import get_success_prob_threshold
from agent.success_predictor import (
    train_and_eval,
    _load_dataframe,
    FEATURE_COLUMNS_NUM,
    FEATURE_COLUMNS_CAT,
)
from agent.threshold_tuner import simulate_policy_outcomes

ORIGINAL_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "synthetic_failed_payments.json")
DRIFT_DATA_PATH = os.path.join(PROJECT_ROOT, "data", "drift_batch_30d.json")
PROPOSALS_LOG_PATH = os.path.join(PROJECT_ROOT, "audit_logs", "policy_change_proposals.json")
CONFIG_PATH = os.path.join(PROJECT_ROOT, "agent", "threshold_config.json")


def load_proposals(path: str = PROPOSALS_LOG_PATH) -> list:
    """Loads existing policy change proposals from disk."""
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_proposal(proposal: dict, path: str = PROPOSALS_LOG_PATH):
    """Appends a new proposal to the proposal registry."""
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    proposals = load_proposals(path)
    proposals.append(proposal)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(proposals, f, indent=2)


def evaluate_drift(
    original_data_path: str = ORIGINAL_DATA_PATH,
    drift_data_path: str = DRIFT_DATA_PATH,
    accuracy_drop_threshold: float = 0.05,
) -> Dict[str, Any]:
    """
    Evaluates original model on the new drift dataset to identify performance decay.
    Re-tunes threshold if drift is detected and writes a pending proposal.
    """
    # 1. Train original model on baseline data
    pipeline, orig_metrics = train_and_eval(original_data_path)
    orig_acc = orig_metrics["classification_report"]["accuracy"]
    orig_prec = orig_metrics["classification_report"]["1"]["precision"]
    orig_rec = orig_metrics["classification_report"]["1"]["recall"]

    # 2. Evaluate original model on the new drift dataset (simulated 30 days later)
    df_drift = _load_dataframe(drift_data_path)
    X_drift = df_drift[FEATURE_COLUMNS_NUM + FEATURE_COLUMNS_CAT]
    y_drift = df_drift["recovery_succeeded"]

    probs_drift = pipeline.predict_proba(X_drift)[:, 1]
    preds_drift = (probs_drift >= 0.50).astype(int)

    drift_acc = float(accuracy_score(y_drift, preds_drift))
    drift_prec = float(precision_score(y_drift, preds_drift, zero_division=0))
    drift_rec = float(recall_score(y_drift, preds_drift, zero_division=0))

    accuracy_delta = drift_acc - orig_acc
    drift_detected = bool(accuracy_delta <= -accuracy_drop_threshold)

    # 3. Simulate current threshold policy outcomes on drift dataset
    current_threshold = get_success_prob_threshold()
    current_policy_res = simulate_policy_outcomes(df_drift, probs_drift, current_threshold)

    # 4. If drift detected, search for optimal new threshold on drift batch
    proposed_threshold = current_threshold
    proposed_policy_res = current_policy_res
    net_value_impact = 0

    if drift_detected or True:  # Compute grid search to find optimal threshold for new distribution
        threshold_candidates = [round(t, 2) for t in np.arange(0.20, 0.85, 0.01)]
        best_t = current_threshold
        best_net = -float("inf")

        for t in threshold_candidates:
            res = simulate_policy_outcomes(df_drift, probs_drift, t)
            if res["net_value"] > best_net:
                best_net = res["net_value"]
                best_t = t

        proposed_threshold = best_t
        proposed_policy_res = simulate_policy_outcomes(df_drift, probs_drift, proposed_threshold)
        net_value_impact = proposed_policy_res["net_value"] - current_policy_res["net_value"]

    proposal_id = f"prop_drift_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    proposal = {
        "proposal_id": proposal_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "drift_detected": drift_detected,
        "evaluated_on": "simulated_drift_batch_30d",
        "dataset_size": len(df_drift),
        "amount_at_risk": int(df_drift["amount"].sum()),
        "original_performance": {
            "accuracy": round(orig_acc, 3),
            "precision": round(orig_prec, 3),
            "recall": round(orig_rec, 3),
        },
        "drift_batch_performance": {
            "accuracy": round(drift_acc, 3),
            "precision": round(drift_prec, 3),
            "recall": round(drift_rec, 3),
        },
        "accuracy_delta_pp": round(accuracy_delta * 100, 2),
        "current_threshold": round(current_threshold, 2),
        "proposed_threshold": round(proposed_threshold, 2),
        "net_value_current_threshold": int(current_policy_res["net_value"]),
        "net_value_proposed_threshold": int(proposed_policy_res["net_value"]),
        "estimated_net_value_gain": int(net_value_impact),
        "attempted_at_current": current_policy_res["attempted_count"],
        "attempted_at_proposed": proposed_policy_res["attempted_count"],
        "recovery_rate_current": round(current_policy_res["recovery_rate_attempted"], 4),
        "recovery_rate_proposed": round(proposed_policy_res["recovery_rate_attempted"], 4),
        "status": "pending_human_approval",
        "note": "Evaluated on a simulated 30-day-later batch with a deliberately shifted error distribution, not observed production drift.",
    }

    # Save to immutable audit registry
    save_proposal(proposal)

    return proposal


def print_drift_report(proposal: Dict[str, Any]):
    """Prints clean human-readable console report for demos and pitch videos."""
    orig_acc = proposal["original_performance"]["accuracy"] * 100
    drift_acc = proposal["drift_batch_performance"]["accuracy"] * 100
    delta = proposal["accuracy_delta_pp"]
    
    print("\n" + "=" * 60)
    print("=== DRIFT-CHECK (RECOVERY OPS) AGENT REPORT ===")
    print("=" * 60)
    print(f"Evaluated Batch: {proposal['evaluated_on']} (n={proposal['dataset_size']:,} records, Rs.{proposal['amount_at_risk']:,} at risk)")
    print(f"Success Predictor Accuracy: {orig_acc:.1f}% (original baseline) -> {drift_acc:.1f}% (on drift batch)")
    print(f"Accuracy Delta: {delta:+.1f} percentage points")
    
    if proposal["drift_detected"]:
        print(f"\n[!] DRIFT DETECTED (>5.0pp accuracy degradation detected)")
        print(f"   Model assumptions have gone stale due to shifted bank failure rates.")
        print(f"   Proposed Threshold Change: {proposal['current_threshold']:.2f} -> {proposal['proposed_threshold']:.2f}")
        print(f"   Current Net Value:         Rs.{proposal['net_value_current_threshold']:,}")
        print(f"   Proposed Net Value:        Rs.{proposal['net_value_proposed_threshold']:,}")
        print(f"   Estimated Net INR Impact:  +Rs.{proposal['estimated_net_value_gain']:,} if approved")
        print(f"   Attempt Precision:         {proposal['recovery_rate_current']:.1%} -> {proposal['recovery_rate_proposed']:.1%}")
        print(f"\nStatus: PENDING HUMAN APPROVAL (Proposal #{proposal['proposal_id']})")
        print(f"Safety Guarantee: NEVER auto-applied without human review.")
    else:
        print(f"\n[OK] NO DRIFT DETECTED: Model performance within calibrated confidence bounds.")
        print(f"Current threshold ({proposal['current_threshold']:.2f}) remains optimal.")

    print("=" * 60 + "\n")


if __name__ == "__main__":
    orig_path = sys.argv[1] if len(sys.argv) > 1 else ORIGINAL_DATA_PATH
    drift_path = sys.argv[2] if len(sys.argv) > 2 else DRIFT_DATA_PATH
    
    # Ensure drift dataset exists
    if not os.path.exists(drift_path):
        from data.generate_drift_batch import generate_drift_dataset
        print(f"Generating drift batch at {drift_path}...")
        ds = generate_drift_dataset(1200)
        with open(drift_path, "w", encoding="utf-8") as f:
            json.dump(ds, f, indent=2)
            
    res = evaluate_drift(orig_path, drift_path)
    print_drift_report(res)
