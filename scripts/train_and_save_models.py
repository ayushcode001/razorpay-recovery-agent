"""
Build-time Model Training and Serialization Script.
Trains the Success Predictor and Causal T-Learner Uplift models on baseline dataset
and serializes artifacts to the models/ directory for fast runtime inference.
"""

import os
import sys
import joblib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.success_predictor import train_and_eval
from agent.uplift_model import train_and_validate_uplift

DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "synthetic_failed_payments.json")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")


def train_and_save_all():
    os.makedirs(MODELS_DIR, exist_ok=True)

    print("==================================================")
    print("[Model Serialization] Training models for production deployment...")
    print(f"[Model Serialization] Training dataset: {DATASET_PATH}")
    print(f"[Model Serialization] Target directory: {MODELS_DIR}")
    print("==================================================")

    # 1. Train Success Predictor
    print("\n[1/2] Training Success Predictor Pipeline...")
    predictor_pipeline, predictor_metrics = train_and_eval(DATASET_PATH)
    predictor_path = os.path.join(MODELS_DIR, "success_predictor.joblib")
    joblib.dump(predictor_pipeline, predictor_path)
    acc = predictor_metrics["classification_report"]["accuracy"]
    print(f"  -> Saved to {predictor_path}")
    print(f"  -> Model Accuracy: {acc:.1%}")

    # 2. Train T-Learner Uplift Model
    print("\n[2/2] Training T-Learner Causal Uplift Model...")
    uplift_res = train_and_validate_uplift(DATASET_PATH)
    uplift_path = os.path.join(MODELS_DIR, "uplift_model.joblib")
    joblib.dump(uplift_res["model"], uplift_path)
    print(f"  -> Saved to {uplift_path}")
    print(f"  -> Pearson Correlation: {uplift_res['pearson_correlation']:.4f}")
    print(f"  -> Mean Estimated Uplift: +{uplift_res['overall_mean_pred_uplift']:.2%}")

    print("\n==================================================")
    print("[Model Serialization] All models trained and saved successfully!")
    print("==================================================")


if __name__ == "__main__":
    train_and_save_all()
