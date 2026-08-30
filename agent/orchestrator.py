"""
Runs the full detect -> predict -> decide -> (simulate/execute) -> log loop
over a batch, then reports the numbers Razorpay explicitly asks for:
money recovered, recovery rate, and an honest exception list.

NOTE on ground truth: `recovery_succeeded` in the synthetic data represents
"would this succeed IF attempted" (see data/generate_data.py). We only
realize that outcome for records the agent actually decides to act on --
escalated records are correctly left as "not attempted", which is the
graceful-failure behavior, not a gap in the pipeline.
"""

import json
import os
import sys

import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.taxonomy import category_for
from agent.policy_engine import decide_action, SUCCESS_PROB_THRESHOLD, UPLIFT_THRESHOLD
from agent.audit import AuditTrail
from agent.success_predictor import train_and_eval, FEATURE_COLUMNS_NUM, FEATURE_COLUMNS_CAT
from agent.uplift_model import TLearnerUpliftModel, train_and_validate_uplift


def run_batch(data_path: str, use_uplift: bool = True):
    with open(data_path) as f:
        records = json.load(f)

    # Train the success predictor on this batch
    pipeline, ml_metrics = train_and_eval(data_path)

    df = pd.DataFrame(records)
    df["category"] = df["error_code"].apply(category_for)
    df["hour_of_day"] = pd.to_datetime(df["created_at"], unit="s").dt.hour
    X = df[FEATURE_COLUMNS_NUM + FEATURE_COLUMNS_CAT]
    probs = pipeline.predict_proba(X)[:, 1]

    uplift_scores = None
    uplift_metrics = None
    if use_uplift and "treatment" in df.columns:
        try:
            t_learner = TLearnerUpliftModel()
            t_learner.fit(df)
            uplift_scores = t_learner.predict_uplift(X)
            uplift_metrics = train_and_validate_uplift(data_path)
        except Exception as e:
            print(f"[Warning] Uplift model training error: {e}")

    audit = AuditTrail()
    exceptions = []  # records the agent could not resolve -- the honest list

    for idx, (record, prob) in enumerate(zip(records, probs)):
        uplift_val = float(uplift_scores[idx]) if uplift_scores is not None else None
        decision = decide_action(record, float(prob), uplift_val)

        outcome = None
        if decision["attempted"]:
            # Realize the ground-truth outcome for this attempt.
            succeeded = bool(record["recovery_succeeded"])
            outcome = {"succeeded": succeeded}
            if not succeeded:
                exceptions.append({
                    "payment_id": record["id"],
                    "amount": record["amount"],
                    "error_code": record["error_code"],
                    "action_taken": decision["action"],
                    "predicted_success_prob": round(prob, 3),
                    "estimated_uplift": round(uplift_val, 3) if uplift_val is not None else None,
                    "why_it_still_failed": "Attempt matched policy but did not recover; "
                                             "see confusion matrix for the model's known error rate.",
                })
        else:
            exceptions.append({
                "payment_id": record["id"],
                "amount": record["amount"],
                "error_code": record["error_code"],
                "action_taken": decision["action"],
                "predicted_success_prob": round(prob, 3),
                "estimated_uplift": round(uplift_val, 3) if uplift_val is not None else None,
                "why_it_still_failed": decision["reason"],
            })

        audit.log(record, decision, outcome)

    audit.save()
    summary = audit.summary()

    # Invariant: Every record must be classified as attempted, escalated, or skipped_low_uplift
    assert (
        summary["attempted"] + summary["escalated_to_human"] + summary["skipped_low_uplift"]
        == summary["total_records"]
    ), (
        f"Invariant violation: {summary['attempted']} (attempted) + "
        f"{summary['escalated_to_human']} (escalated) + {summary['skipped_low_uplift']} (skipped) "
        f"!= {summary['total_records']} (total)"
    )

    return summary, ml_metrics, exceptions, uplift_metrics


if __name__ == "__main__":
    data_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJECT_ROOT, "data", "synthetic_failed_payments.json")
    
    # 1. Run WITH uplift refinement
    summary, ml_metrics, exceptions, uplift_metrics = run_batch(data_path, use_uplift=True)

    # 2. Run WITHOUT uplift refinement to quantify the exact uplift-attributable delta
    summary_no_uplift, _, _, _ = run_batch(data_path, use_uplift=False)

    print("=== BATCH RUN SUMMARY (Tuned Policy + Uplift Refinement) ===")
    for k, v in summary.items():
        if "amount" in k:
            print(f"  {k}: Rs.{v:,}")
        elif "rate" in k:
            print(f"  {k}: {v:.2%}")
        else:
            print(f"  {k}: {v}")

    print("\n=== UPLIFT ATTRIBUTABLE DELTA (With vs Without Uplift Gate) ===")
    diff_attempted = summary_no_uplift["attempted"] - summary["attempted"]
    diff_wasted = summary_no_uplift["amount_wasted_on_failed_attempts"] - summary["amount_wasted_on_failed_attempts"]
    print(f"  Attempts diverted to skipped_low_uplift: {diff_attempted} records")
    print(f"  Wasted spend eliminated: Rs.{diff_wasted:,} ({diff_wasted / summary_no_uplift['amount_wasted_on_failed_attempts']:.2%} reduction)")
    print(f"  Precision on attempted cases: {summary_no_uplift['recovery_rate_of_attempted']:.2%} -> {summary['recovery_rate_of_attempted']:.2%}")

    if uplift_metrics:
        print(f"\n=== UPLIFT MODEL (Causal T-Learner) ===")
        print(f"  Correlation with Ground-Truth Uplift: {uplift_metrics['pearson_correlation']:.4f} (p={uplift_metrics['p_value']:.2e})")
        print(f"  Estimated Mean Uplift: +{uplift_metrics['overall_mean_pred_uplift']:.2%} vs True Mean Uplift: +{uplift_metrics['overall_mean_true_uplift']:.2%}")
        print(f"  Cases Filtered (Likely Self-Recovery): {summary['skipped_low_uplift']} transactions")

    print(f"\n=== EXCEPTIONS (could not resolve): {len(exceptions)} of {summary['total_records']} ===")
    for e in exceptions[:5]:
        uplift_info = f" | uplift={e['estimated_uplift']}" if e.get("estimated_uplift") is not None else ""
        print(f"  [{e['payment_id']}] Rs.{e['amount']} | {e['error_code']} | "
              f"action={e['action_taken']} | p_success={e['predicted_success_prob']}{uplift_info}")
    if len(exceptions) > 5:
        print(f"  ... and {len(exceptions) - 5} more (see audit_logs/audit_trail.json)")

    print(f"\nFull audit trail written to audit_logs/audit_trail.json")

