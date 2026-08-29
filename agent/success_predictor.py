"""
Predicts P(intervention succeeds | context) for a failed payment.

This is the real learned model in the project. error_code is already handed
to us by Razorpay's webhook, so classifying it would be pointless -- what's
NOT known in advance is whether retrying/re-prompting will actually work.
That's the genuinely useful, genuinely hard-to-hand-engineer signal, and the
one with real precision/recall to report.

The predicted probability feeds the policy engine: below a threshold, the
agent stops and escalates instead of burning a retry.
"""

import json
import os
import sys

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.taxonomy import category_for

FEATURE_COLUMNS_NUM = ["amount", "retry_count", "hour_of_day"]
FEATURE_COLUMNS_CAT = ["method", "error_source", "category"]


def _load_dataframe(path):
    with open(path) as f:
        records = json.load(f)
    df = pd.DataFrame(records)
    df["category"] = df["error_code"].apply(category_for)
    df["hour_of_day"] = pd.to_datetime(df["created_at"], unit="s").dt.hour
    return df


def build_pipeline():
    preprocessor = ColumnTransformer([
        ("num", "passthrough", FEATURE_COLUMNS_NUM),
        ("cat", OneHotEncoder(handle_unknown="ignore"), FEATURE_COLUMNS_CAT),
    ])
    model = GradientBoostingClassifier(random_state=42, n_estimators=100, max_depth=3)
    return Pipeline([("prep", preprocessor), ("model", model)])


def train_and_eval(data_path):
    df = _load_dataframe(data_path)
    X = df[FEATURE_COLUMNS_NUM + FEATURE_COLUMNS_CAT]
    y = df["recovery_succeeded"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
    cm = confusion_matrix(y_test, y_pred).tolist()

    return pipeline, {
        "classification_report": report,
        "confusion_matrix": cm,
        "test_size": len(y_test),
        "positive_rate_actual": float(y_test.mean()),
    }


if __name__ == "__main__":
    data_path = sys.argv[1] if len(sys.argv) > 1 else "../data/synthetic_failed_payments.json"
    pipeline, metrics = train_and_eval(data_path)

    print("=== Success Predictor: held-out test metrics ===")
    print(f"Test set size: {metrics['test_size']}")
    print(f"Actual success rate in test set: {metrics['positive_rate_actual']:.2%}")
    print("\nConfusion matrix [[TN, FP], [FN, TP]]:")
    print(np.array(metrics["confusion_matrix"]))
    print("\nPer-class precision/recall/f1:")
    for label, stats in metrics["classification_report"].items():
        if label in ("0", "1"):
            name = "fail (0)" if label == "0" else "succeed (1)"
            print(f"  {name}: precision={stats['precision']:.2f} "
                  f"recall={stats['recall']:.2f} f1={stats['f1-score']:.2f} "
                  f"support={stats['support']}")
    print(f"\nOverall accuracy: {metrics['classification_report']['accuracy']:.2%}")
