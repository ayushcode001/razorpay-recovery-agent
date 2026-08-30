"""
T-Learner Uplift Model for Autonomous Payment Recovery.

Answers the genuine causal question:
"Did OUR intervention cause the recovery, or would it have happened anyway?"

Implements a two-model T-Learner (Causal ML):
  μ₁(x) = P(recovery | treatment=1, features x)   -- trained on treated subset
  μ₀(x) = P(recovery | treatment=0, features x)   -- trained on control subset
  Estimated Uplift(x) = μ₁(x) - μ₀(x)

Validated against known ground-truth treatment effect from the experimental generator.
NOTE on Causal Validity: In real-world data, per-transaction true uplift is fundamentally
unobservable (fundamental problem of causal inference). Validating correlation on
randomized synthetic ground truth verifies the *methodology and estimation pipeline*
before deploying against real randomized holdouts.
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd
from scipy.stats import pearsonr
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.taxonomy import category_for
from agent.success_predictor import (
    FEATURE_COLUMNS_NUM,
    FEATURE_COLUMNS_CAT,
    _load_dataframe,
)

MODEL_STATE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uplift_model_state.pkl")


def _build_base_pipeline():
    preprocessor = ColumnTransformer([
        ("num", "passthrough", FEATURE_COLUMNS_NUM),
        ("cat", OneHotEncoder(handle_unknown="ignore"), FEATURE_COLUMNS_CAT),
    ])
    model = GradientBoostingClassifier(random_state=42, n_estimators=100, max_depth=3)
    return Pipeline([("prep", preprocessor), ("model", model)])


class TLearnerUpliftModel:
    """
    Two-Model T-Learner estimator for Individual Treatment Effect (ITE / Uplift).
    """

    def __init__(self):
        self.model_treated = _build_base_pipeline()
        self.model_control = _build_base_pipeline()
        self.is_fitted = False

    def fit(self, df: pd.DataFrame):
        """Fits μ₁ on treatment arm (treatment=1) and μ₀ on control arm (treatment=0)."""
        df = df.copy()
        if "category" not in df.columns:
            df["category"] = df["error_code"].apply(category_for)
        if "hour_of_day" not in df.columns:
            df["hour_of_day"] = pd.to_datetime(df["created_at"], unit="s").dt.hour

        df_treated = df[df["treatment"] == 1]
        df_control = df[df["treatment"] == 0]

        X_treated = df_treated[FEATURE_COLUMNS_NUM + FEATURE_COLUMNS_CAT]
        y_treated = df_treated["observed_outcome"]

        X_control = df_control[FEATURE_COLUMNS_NUM + FEATURE_COLUMNS_CAT]
        y_control = df_control["observed_outcome"]

        self.model_treated.fit(X_treated, y_treated)
        self.model_control.fit(X_control, y_control)
        self.is_fitted = True
        return self

    def predict_p1_p0(self, X: pd.DataFrame):
        """Returns (p_treated, p_control, estimated_uplift)."""
        p1 = self.model_treated.predict_proba(X)[:, 1]
        p0 = self.model_control.predict_proba(X)[:, 1]
        uplift = p1 - p0
        return p1, p0, uplift

    def predict_uplift(self, X: pd.DataFrame) -> np.ndarray:
        """Returns estimated uplift (p1 - p0) per record."""
        p1, p0, uplift = self.predict_p1_p0(X)
        return uplift

    def save(self, path=MODEL_STATE_PATH):
        joblib.dump(self, path)

    @classmethod
    def load(cls, path=MODEL_STATE_PATH):
        if os.path.exists(path):
            return joblib.load(path)
        return None


def train_and_validate_uplift(data_path: str):
    df = _load_dataframe(data_path)

    # Train / Test split
    df_train, df_test = train_test_split(df, test_size=0.25, random_state=42, stratify=df["_category"])
    
    t_learner = TLearnerUpliftModel()
    t_learner.fit(df_train)

    X_test = df_test[FEATURE_COLUMNS_NUM + FEATURE_COLUMNS_CAT]
    p1_pred, p0_pred, uplift_pred = t_learner.predict_p1_p0(X_test)

    # Calculate ground truth true uplift for test set
    # True uplift = true intervention prob - true self-recovery prob
    # From generate_data.py simulation functions
    from data.generate_data import BASE_SUCCESS_PROB, BASE_SELF_RECOVERY_PROB
    
    true_p1_list = []
    true_p0_list = []
    for _, row in df_test.iterrows():
        cat = row["_category"]
        amt = row["amount"]
        rc = row["retry_count"]
        hr = row["hour_of_day"]
        
        # Ground truth p1
        p1_val = BASE_SUCCESS_PROB[cat]
        if amt > 50000: p1_val -= 0.10
        if rc >= 2: p1_val -= 0.15
        if hr < 6 or hr > 23: p1_val -= 0.05
        p1_val = max(0.02, min(0.95, p1_val))
        
        # Ground truth p0
        p0_val = row.get("p0_self_recovery", BASE_SELF_RECOVERY_PROB[cat])
        
        true_p1_list.append(p1_val)
        true_p0_list.append(p0_val)

    true_p1 = np.array(true_p1_list)
    true_p0 = np.array(true_p0_list)
    true_uplift = true_p1 - true_p0

    corr, p_value = pearsonr(uplift_pred, true_uplift)

    # Category-level breakdown
    df_eval = df_test.copy()
    df_eval["uplift_pred"] = uplift_pred
    df_eval["true_uplift"] = true_uplift
    df_eval["p1_pred"] = p1_pred
    df_eval["p0_pred"] = p0_pred

    cat_summary = df_eval.groupby("_category").agg(
        n=("id", "count"),
        mean_pred_uplift=("uplift_pred", "mean"),
        mean_true_uplift=("true_uplift", "mean"),
        mean_p0_self_recovery=("p0_pred", "mean"),
        mean_p1_recovery=("p1_pred", "mean"),
    ).reset_index()

    # Save fitted model for runtime use by orchestrator / server
    t_learner.save(MODEL_STATE_PATH)

    return {
        "model": t_learner,
        "pearson_correlation": float(corr),
        "p_value": float(p_value),
        "test_size": len(df_test),
        "category_summary": cat_summary.to_dict(orient="records"),
        "overall_mean_pred_uplift": float(np.mean(uplift_pred)),
        "overall_mean_true_uplift": float(np.mean(true_uplift)),
    }


if __name__ == "__main__":
    data_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJECT_ROOT, "data", "synthetic_failed_payments.json")
    print(f"Training T-Learner Uplift Model on {data_path}...")
    res = train_and_validate_uplift(data_path)

    print("\n=== T-Learner Uplift Model Validation (Held-out Test Split) ===")
    print(f"Test size: {res['test_size']} transactions")
    print(f"Pearson Correlation (Estimated vs True Uplift): {res['pearson_correlation']:.4f} (p={res['p_value']:.2e})")
    print(f"Overall Mean Estimated Uplift: +{res['overall_mean_pred_uplift']:.2%}")
    print(f"Overall Mean True Uplift:      +{res['overall_mean_true_uplift']:.2%}")

    print("\n--- Per-Category Uplift Breakdown ---")
    print(f"{'Category':<16} {'Count':<6} {'Pred Uplift':<12} {'True Uplift':<12} {'P0 (Self-Rec)':<14} {'P1 (Treated)':<12}")
    for row in res["category_summary"]:
        print(
            f"{row['_category']:<16} {row['n']:<6} "
            f"{row['mean_pred_uplift']:>10.2%}  {row['mean_true_uplift']:>10.2%}  "
            f"{row['mean_p0_self_recovery']:>12.2%}  {row['mean_p1_recovery']:>10.2%}"
        )
    print(f"\nModel state persisted to {MODEL_STATE_PATH}")
