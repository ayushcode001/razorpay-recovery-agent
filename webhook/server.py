"""
Live Razorpay Webhook Receiver & Autonomous Recovery Agent Server.

Endpoints:
  POST /webhook/razorpay                    - Receives real payment.failed webhooks from Razorpay (HMAC verified)
  GET  /checkout                            - Interactive test checkout to trigger real test-mode failures
  POST /create-test-order                   - Creates Razorpay order for Checkout.js modal
  GET  /                                    - Live Dashboard showing real-time decisions & audit trail
  GET  /api/v1/health                       - Public fast health check (unauthenticated for keep-alive cron)
  GET  /api/v1/audit-trail                  - JSON API for live audit events
  GET  /api/v1/degradation-alerts           - JSON API for cached outage/degradation alerts
  GET  /api/v1/cohort-report                - JSON API for cohort analyst data (for Recharts scatter)
  GET  /api/v1/bandit-results               - JSON API for bandit convergence data (for Recharts line chart)
  POST /api/v1/copilot                      - LLM Copilot Q&A over audit trail (rate-limited: 10/min)
  GET  /api/v1/policy-proposals             - Drift-check governance proposals
  POST /api/v1/policy-proposals/<id>/approve - Human approval of policy update (rate-limited: 10/min)
  POST /api/v1/policy-proposals/<id>/reject  - Human rejection of policy update (rate-limited: 10/min)
  POST /api/v1/trigger-drift-check          - On-demand drift evaluation
"""

import os
import sys
import time
import json
import joblib
from datetime import datetime, timezone
import pandas as pd
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.taxonomy import category_for
from agent.policy_engine import decide_action, get_success_prob_threshold
from agent.audit import AuditTrail
from agent.success_predictor import train_and_eval, FEATURE_COLUMNS_NUM, FEATURE_COLUMNS_CAT
from agent.degradation_agent import run_degradation_pipeline
from agent.cohort_analyst import analyze_cohorts
from agent.retry_bandit import run_bandit_simulation, ARMS, CATEGORIES
from agent.copilot import answer_question
from agent.drift_check import load_proposals, save_proposal, evaluate_drift, PROPOSALS_LOG_PATH, CONFIG_PATH
from agent.db import is_db_configured, get_db_session
from scripts.init_db import init_database
from agent.db_models import ThresholdConfig, PolicyChangeProposal
from webhook.razorpay_client import (
    RAZORPAY_KEY_ID,
    create_order,
    create_payment_link,
    verify_webhook_signature,
)
from webhook.notifier import send_recovery_notification

load_dotenv()

# Initialize DB tables automatically on app startup
try:
    init_database()
except Exception as e:
    print(f"[Agent Server] Warning: Could not auto-initialize DB tables: {e}")

app = Flask(__name__)

# CORS: Allow Vercel frontend (and local dev) to call all /api/v1/* routes.
# Set CORS_ALLOWED_ORIGINS in environment (comma-separated). Defaults to all origins.
_cors_origins_raw = os.getenv("CORS_ALLOWED_ORIGINS", "*")
_cors_origins = [o.strip() for o in _cors_origins_raw.split(",")] if _cors_origins_raw != "*" else "*"
CORS(app, origins=_cors_origins, supports_credentials=True)

# Rate limiting: protect Gemini API cost and policy mutation endpoints.
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],  # No global limit — only apply to decorated routes.
    storage_uri="memory://",  # In-memory for single-instance Render deployment.
)

# Authentication configuration
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "").strip()
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "").strip()
UNPROTECTED_PATHS = {"/webhook/razorpay", "/api/v1/health"}

# 1. Initialize Audit Trail
audit_trail = AuditTrail()

# 2. Load or Train ML Model at Startup
MODELS_DIR = os.path.join(PROJECT_ROOT, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "success_predictor.joblib")

ml_pipeline = None
if os.path.exists(MODEL_PATH):
    try:
        print(f"[Agent Server] Loading serialized Success Predictor from {MODEL_PATH}...")
        ml_pipeline = joblib.load(MODEL_PATH)
        print("[Agent Server] Serialized model loaded successfully.")
    except Exception as e:
        print(f"[Agent Server] Warning: Could not load serialized model: {e}")

if ml_pipeline is None:
    print("[Agent Server] Training success predictor pipeline in-memory fallback...")
    DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "synthetic_failed_payments.json")
    ml_pipeline, ml_metrics = train_and_eval(DATASET_PATH)
    print(f"[Agent Server] Success Predictor ready (accuracy: {ml_metrics['classification_report']['accuracy']:.1%})")

# 3. Cache Degradation Alerts in Memory at Startup
CACHED_DEGRADATION_INCIDENTS = []
try:
    print("[Agent Server] Pre-computing degradation baseline and incident alerts cache...")
    deg_res = run_degradation_pipeline()
    CACHED_DEGRADATION_INCIDENTS = deg_res.get("incidents", [])[:4]
    print(f"[Agent Server] Cached {len(CACHED_DEGRADATION_INCIDENTS)} degradation incident alerts.")
except Exception as e:
    print(f"[Agent Server] Degradation monitoring initialization warning: {e}")

# 4. Cache Cohort Analyst Data in Memory at Startup
CACHED_COHORT_DATA = {}
try:
    print("[Agent Server] Pre-computing cohort analyst data cache...")
    _cohort_result = analyze_cohorts()
    # Prepare cohort summaries (serializable)
    _cohort_df = _cohort_result["df"]
    # Build per-cluster scatter point arrays for Recharts
    _scatter_by_cluster = {}
    for c in _cohort_result["cohorts"]:
        cid = c["cluster_id"]
        c_sub = _cohort_df[_cohort_df["cluster"] == cid][["pca_x", "pca_y", "amount", "method"]]
        _scatter_by_cluster[str(cid)] = c_sub.head(300).to_dict(orient="records")
    CACHED_COHORT_DATA = {
        "cohorts": _cohort_result["cohorts"],
        "scatter_by_cluster": _scatter_by_cluster,
        "pca_variance_ratio": _cohort_result["pca_variance_ratio"],
        "total_at_risk": _cohort_result["total_at_risk"],
        "non_trivial_passed": _cohort_result["non_trivial_passed"],
    }
    print(f"[Agent Server] Cached cohort analyst data ({len(_cohort_result['cohorts'])} cohorts).")
except Exception as e:
    print(f"[Agent Server] Cohort analyst initialization warning: {e}")
    CACHED_COHORT_DATA = {}

# 5. Cache Bandit Simulation Results in Memory at Startup
CACHED_BANDIT_DATA = {}
try:
    print("[Agent Server] Pre-computing bandit simulation data cache (1000 episodes)...")
    _bandit_results = run_bandit_simulation(n_episodes=1000, seed=42)
    _bandit_serializable = {}
    for cat in CATEGORIES:
        r = _bandit_results[cat]
        _bandit_serializable[cat] = {
            "bandit_cum_rewards": r["bandit_cum_rewards"],
            "fixed_cum_rewards": r["fixed_cum_rewards"],
            "taxonomy_cum_rewards": r["taxonomy_cum_rewards"],
            "random_cum_rewards": r["random_cum_rewards"],
            "optimal_arm": r["optimal_arm"],
            "most_chosen_arm": r["most_chosen_arm"],
            "final_optimal_pull_rate": r["final_optimal_pull_rate"],
            "percentage_gain_vs_fixed": r["percentage_gain_vs_fixed"],
            "percentage_gain_vs_taxonomy": r["percentage_gain_vs_taxonomy"],
            "taxonomy_default_arm": r["taxonomy_default_arm"],
            "converged": r["converged"],
        }
    CACHED_BANDIT_DATA = {
        "categories": CATEGORIES,
        "arms": ARMS,
        "results": _bandit_serializable,
    }
    print(f"[Agent Server] Cached bandit simulation data ({len(CATEGORIES)} categories).")
except Exception as e:
    print(f"[Agent Server] Bandit simulation initialization warning: {e}")
    CACHED_BANDIT_DATA = {}


@app.before_request
def basic_auth_gate():
    """Enforces HTTP Basic Authentication on dashboard and API routes (except public webhooks & health)."""
    if request.path in UNPROTECTED_PATHS:
        return None

    if not DASHBOARD_USERNAME or not DASHBOARD_PASSWORD:
        return None  # Unauthenticated in local development if credentials not set

    auth = request.authorization
    if not auth or auth.username != DASHBOARD_USERNAME or auth.password != DASHBOARD_PASSWORD:
        return Response(
            "Access Denied: Authentication required.\n",
            401,
            {"WWW-Authenticate": 'Basic realm="Razorpay Recovery Agent"'}
        )


def score_record(record: dict) -> float:
    """Computes predicted success probability for an incoming failure record."""
    df_single = pd.DataFrame([{
        "amount": record["amount"],
        "retry_count": record.get("retry_count", 0),
        "hour_of_day": pd.to_datetime(record["created_at"], unit="s").hour,
        "method": record.get("method", "card"),
        "error_source": record.get("error_source", "gateway"),
        "category": category_for(record["error_code"]),
    }])
    X = df_single[FEATURE_COLUMNS_NUM + FEATURE_COLUMNS_CAT]
    prob = ml_pipeline.predict_proba(X)[0, 1]
    return float(prob)


# -------------------------------------------------------------------------
# Webhook & Health Endpoints
# -------------------------------------------------------------------------

@app.route("/api/v1/health", methods=["GET"])
def health():
    """Fast health check endpoint for GitHub Actions keep-alive ping and uptime monitoring."""
    return jsonify({
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database_connected": is_db_configured(),
    }), 200


@app.route("/webhook/razorpay", methods=["POST"])
def handle_razorpay_webhook():
    """
    Receives and processes real webhook payloads from Razorpay.
    Verifies signature -> maps schema -> scores ML -> evaluates policy -> executes action -> logs audit.
    """
    raw_body = request.get_data()
    signature = request.headers.get("X-Razorpay-Signature", "")

    # 1. Signature Verification
    if not verify_webhook_signature(raw_body, signature):
        print("[Webhook] Signature verification failed.")
        return jsonify({"status": "error", "message": "Invalid signature"}), 400

    payload = request.get_json(silent=True) or {}
    event_type = payload.get("event")

    print(f"\n[Webhook] Received Razorpay event: {event_type}")

    if event_type != "payment.failed":
        return jsonify({"status": "ignored", "event": event_type}), 200

    # 2. Extract payment entity
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    if not payment_entity:
        return jsonify({"status": "error", "message": "Missing payment entity"}), 400

    granular_error = (
        payment_entity.get("error_reason")
        or payment_entity.get("error_code")
        or "bank_technical_error"
    ).lower()

    amount_in_rupees = float(payment_entity.get("amount", 0)) / 100.0
    payment_id = payment_entity.get("id", f"pay_live_{int(time.time())}")
    method = payment_entity.get("method", "card")
    error_source = payment_entity.get("error_source", "gateway")
    error_step = payment_entity.get("error_step", "payment_processing")
    created_at = payment_entity.get("created_at", int(time.time()))
    customer_email = payment_entity.get("email")
    customer_contact = payment_entity.get("contact")

    record = {
        "id": payment_id,
        "amount": amount_in_rupees,
        "currency": payment_entity.get("currency", "INR"),
        "method": method,
        "error_code": granular_error,
        "error_source": error_source,
        "error_step": error_step,
        "created_at": created_at,
        "retry_count": 0,
    }

    # 3. Model Prediction: P(success | context)
    prob = score_record(record)

    # 4. Policy Decision
    decision = decide_action(record, prob)

    print(f"[Agent Decision] ID: {payment_id} | Code: {granular_error} | Action: {decision['action']} | P(success): {prob:.2%}")
    print(f"  Reason: {decision['reason']}")

    # 5. Execute Action (Test Mode side effects)
    execution_result = {}
    if decision["attempted"]:
        amount_in_paise = int(amount_in_rupees * 100)
        action_name = decision["action"]

        if action_name in ("retry_after_cooldown", "retry_with_backoff"):
            plink = create_payment_link(
                amount_in_paise=amount_in_paise,
                description=f"Autonomous Recovery for failed payment {payment_id}",
                customer_email=customer_email,
                customer_contact=customer_contact,
                notify_customer=True,
            )
            execution_result["payment_link"] = plink.get("short_url") or plink.get("id")
            execution_result["status"] = "payment_link_created"

        elif action_name in ("prompt_new_payment_method", "reprompt_customer"):
            plink = create_payment_link(
                amount_in_paise=amount_in_paise,
                description=f"Retry payment {payment_id} with alternative method or details",
                customer_email=customer_email,
                customer_contact=customer_contact,
                notify_customer=True,
            )
            recovery_url = plink.get("short_url") or f"https://rzp.io/i/{plink.get('id')}"
            notif_res = send_recovery_notification(
                recipient_email=customer_email,
                payment_id=payment_id,
                amount_in_rupees=amount_in_rupees,
                action=action_name,
                recovery_link=recovery_url,
                reason=decision["reason"],
            )
            execution_result["payment_link"] = recovery_url
            execution_result["notification"] = notif_res

    # 6. Log to Audit Trail (Persisted to PostgreSQL)
    audit_trail.log(
        record=record,
        decision=decision,
        outcome={"execution": execution_result} if execution_result else None,
    )

    return jsonify({
        "status": "processed",
        "payment_id": payment_id,
        "action": decision["action"],
        "category": decision["category"],
        "predicted_success_prob": round(prob, 3),
        "execution": execution_result,
    }), 200


# -------------------------------------------------------------------------
# Dashboard & Checkout Frontend Routes
# -------------------------------------------------------------------------

@app.route("/", methods=["GET"])
def dashboard():
    """Live audit trail dashboard for demo monitoring."""
    summary = audit_trail.summary()
    recent_entries = audit_trail.get_recent(25)
    
    # Load policy proposals for drift-check governance
    proposals = load_proposals()
    pending_proposals = [p for p in proposals if p.get("status") == "pending_human_approval"]
    latest_proposal = pending_proposals[-1] if pending_proposals else (proposals[-1] if proposals else None)
    current_threshold = get_success_prob_threshold()

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Razorpay Recovery Agent — Live Dashboard</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #090d16;
                --surface: #111827;
                --surface-border: #1f293d;
                --primary: #3b82f6;
                --primary-glow: rgba(59, 130, 246, 0.2);
                --success: #10b981;
                --warning: #f59e0b;
                --danger: #ef4444;
                --text: #f3f4f6;
                --text-muted: #9ca3af;
            }
            body {
                margin: 0;
                font-family: 'Plus Jakarta Sans', sans-serif;
                background-color: var(--bg);
                color: var(--text);
                padding: 24px;
            }
            .container {
                max-width: 1280px;
                margin: 0 auto;
            }
            .header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--surface-border);
                padding-bottom: 20px;
                margin-bottom: 28px;
            }
            .title h1 {
                font-size: 24px;
                font-weight: 700;
                margin: 0 0 6px 0;
                background: linear-gradient(135deg, #60a5fa, #3b82f6, #93c5fd);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            .badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 4px 10px;
                border-radius: 9999px;
                font-size: 12px;
                font-weight: 600;
                background: rgba(16, 185, 129, 0.15);
                color: #34d399;
                border: 1px solid rgba(16, 185, 129, 0.3);
            }
            .pulse-dot {
                width: 8px;
                height: 8px;
                background-color: #10b981;
                border-radius: 50%;
                box-shadow: 0 0 8px #10b981;
                animation: pulse 1.8s infinite;
            }
            @keyframes pulse {
                0% { opacity: 0.4; }
                50% { opacity: 1; }
                100% { opacity: 0.4; }
            }
            .btn {
                background: linear-gradient(135deg, #2563eb, #1d4ed8);
                color: white;
                padding: 10px 18px;
                border-radius: 8px;
                text-decoration: none;
                font-weight: 600;
                font-size: 14px;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                transition: all 0.2s;
                border: 1px solid rgba(255,255,255,0.1);
            }
            .btn:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px var(--primary-glow);
            }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }
            .metric-card {
                background: var(--surface);
                border: 1px solid var(--surface-border);
                border-radius: 12px;
                padding: 18px;
            }
            .metric-label {
                font-size: 13px;
                color: var(--text-muted);
                margin-bottom: 8px;
            }
            .metric-val {
                font-size: 24px;
                font-weight: 700;
                font-family: 'JetBrains Mono', monospace;
            }
            .metric-val.green { color: #34d399; }
            .metric-val.blue { color: #60a5fa; }
            .metric-val.amber { color: #fbbf24; }
            
            .alert-panel {
                background: rgba(245, 158, 11, 0.05);
                border: 1px solid rgba(245, 158, 11, 0.3);
                border-radius: 12px;
                padding: 18px 20px;
                margin-bottom: 24px;
            }
            .alert-panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }
            .alert-panel-header h3 {
                margin: 0;
                font-size: 15px;
                font-weight: 700;
                color: #fbbf24;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .incident-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 12px;
            }
            .incident-card {
                background: #0e1526;
                border: 1px solid #1f2d48;
                border-radius: 8px;
                padding: 12px 14px;
            }
            .inc-title {
                font-weight: 600;
                font-size: 13px;
                color: #f3f4f6;
                display: flex;
                justify-content: space-between;
                margin-bottom: 6px;
            }
            .inc-meta {
                font-size: 11px;
                color: #94a3b8;
                font-family: 'JetBrains Mono', monospace;
                line-height: 1.5;
            }
            .inc-impact {
                color: #f87171;
                font-weight: 600;
            }
            
            .table-container {
                background: var(--surface);
                border: 1px solid var(--surface-border);
                border-radius: 12px;
                overflow: hidden;
            }
            .table-header {
                padding: 16px 20px;
                border-bottom: 1px solid var(--surface-border);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
            .table-header h2 {
                margin: 0;
                font-size: 16px;
                font-weight: 600;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                text-align: left;
                font-size: 13px;
            }
            th {
                background: #0d1322;
                padding: 12px 16px;
                color: var(--text-muted);
                font-weight: 600;
                border-bottom: 1px solid var(--surface-border);
            }
            td {
                padding: 14px 16px;
                border-bottom: 1px solid #162035;
                font-family: 'JetBrains Mono', monospace;
            }
            tr:hover {
                background: rgba(255, 255, 255, 0.02);
            }
            .pill {
                padding: 4px 8px;
                border-radius: 6px;
                font-size: 11px;
                font-weight: 600;
                display: inline-block;
            }
            .pill-retry { background: rgba(59, 130, 246, 0.2); color: #93c5fd; }
            .pill-prompt { background: rgba(16, 185, 129, 0.2); color: #6ee7b7; }
            .pill-escalate { background: rgba(239, 68, 68, 0.2); color: #fca5a5; }

            /* Copilot Chat UI */
            .copilot-card {
                background: var(--surface);
                border: 1px solid #1e2d4a;
                border-radius: 12px;
                padding: 20px;
                margin-bottom: 24px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
            }
            .copilot-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }
            .copilot-title {
                display: flex;
                align-items: center;
                gap: 10px;
                font-size: 16px;
                font-weight: 700;
                color: #93c5fd;
            }
            .copilot-badge {
                font-size: 11px;
                font-weight: 600;
                padding: 3px 8px;
                border-radius: 9999px;
                background: rgba(59, 130, 246, 0.15);
                color: #60a5fa;
                border: 1px solid rgba(59, 130, 246, 0.3);
            }
            .copilot-prompt-chips {
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-bottom: 14px;
            }
            .prompt-chip {
                background: #0d1527;
                border: 1px solid #1f2d48;
                color: #94a3b8;
                padding: 5px 10px;
                border-radius: 6px;
                font-size: 12px;
                cursor: pointer;
                transition: all 0.2s;
            }
            .prompt-chip:hover {
                background: #1e293b;
                color: #f1f5f9;
                border-color: #3b82f6;
            }
            .copilot-input-group {
                display: flex;
                gap: 10px;
            }
            .copilot-input {
                flex: 1;
                background: #090d16;
                border: 1px solid var(--surface-border);
                color: var(--text);
                padding: 12px 16px;
                border-radius: 8px;
                font-size: 14px;
                font-family: inherit;
                outline: none;
                transition: border-color 0.2s;
            }
            .copilot-input:focus {
                border-color: #3b82f6;
                box-shadow: 0 0 0 2px var(--primary-glow);
            }
            .copilot-submit {
                background: linear-gradient(135deg, #3b82f6, #2563eb);
                color: white;
                border: none;
                padding: 12px 22px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                transition: all 0.2s;
            }
            .copilot-submit:hover:not(:disabled) {
                background: #1d4ed8;
                transform: translateY(-1px);
            }
            .copilot-submit:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }
            .copilot-response-box {
                margin-top: 16px;
                background: #090d16;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 16px;
                display: none;
            }
            .copilot-answer {
                font-size: 14px;
                line-height: 1.6;
                color: #e2e8f0;
                white-space: pre-wrap;
            }
            .copilot-grounding-meta {
                margin-top: 12px;
                padding-top: 10px;
                border-top: 1px solid #1e293b;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 12px;
                color: #94a3b8;
            }
            .grounding-tag {
                display: inline-flex;
                align-items: center;
                gap: 5px;
                color: #34d399;
                font-weight: 500;
            }
            .context-toggle-btn {
                background: none;
                border: none;
                color: #60a5fa;
                cursor: pointer;
                font-size: 11px;
                text-decoration: underline;
                padding: 0;
            }
            .grounded-json-viewer {
                display: none;
                margin-top: 10px;
                background: #030712;
                border: 1px solid #111827;
                border-radius: 6px;
                padding: 10px;
                max-height: 200px;
                overflow-y: auto;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                color: #93c5fd;
            }

            /* Drift Governance Panel */
            .drift-panel {
                background: rgba(239, 68, 68, 0.04);
                border: 1px solid rgba(239, 68, 68, 0.3);
                border-radius: 12px;
                padding: 18px 20px;
                margin-bottom: 24px;
            }
            .drift-panel-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
            }
            .drift-panel-header h3 {
                margin: 0;
                font-size: 15px;
                font-weight: 700;
                color: #f87171;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .drift-status-badge {
                font-size: 11px;
                font-weight: 600;
                padding: 4px 10px;
                border-radius: 9999px;
            }
            .drift-badge-pending {
                background: rgba(245, 158, 11, 0.15);
                color: #fbbf24;
                border: 1px solid rgba(245, 158, 11, 0.4);
            }
            .drift-badge-approved {
                background: rgba(16, 185, 129, 0.15);
                color: #34d399;
                border: 1px solid rgba(16, 185, 129, 0.4);
            }
            .drift-badge-rejected {
                background: rgba(239, 68, 68, 0.15);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.4);
            }
            .drift-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px;
                margin-bottom: 14px;
            }
            .drift-metric-box {
                background: #0e1526;
                border: 1px solid #1f2d48;
                border-radius: 8px;
                padding: 10px 14px;
            }
            .drift-metric-lbl {
                font-size: 11px;
                color: #94a3b8;
                margin-bottom: 4px;
            }
            .drift-metric-val {
                font-size: 16px;
                font-weight: 700;
                font-family: 'JetBrains Mono', monospace;
            }
            .btn-action-group {
                display: flex;
                gap: 10px;
                align-items: center;
            }
            .btn-approve {
                background: linear-gradient(135deg, #10b981, #059669);
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            .btn-approve:hover {
                transform: translateY(-1px);
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            }
            .btn-reject {
                background: rgba(239, 68, 68, 0.1);
                color: #f87171;
                border: 1px solid rgba(239, 68, 68, 0.4);
                padding: 8px 14px;
                border-radius: 6px;
                font-size: 13px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.2s;
            }
            .btn-reject:hover {
                background: rgba(239, 68, 68, 0.2);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <div class="title">
                    <h1>Razorpay AI Recovery Agent</h1>
                    <div style="display: flex; align-items: center; gap: 12px; margin-top: 4px;">
                        <span class="badge"><span class="pulse-dot"></span> Webhook Receiver Active</span>
                        <span style="font-size: 13px; color: var(--text-muted);">Track 03: AI Revenue Recovery</span>
                    </div>
                </div>
                <div>
                    <a href="/checkout" class="btn">⚡ Open Test Checkout & Trigger Failure</a>
                </div>
            </div>

            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-label">Total Handled</div>
                    <div class="metric-val">{{ summary.total_records }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Amount at Risk</div>
                    <div class="metric-val">₹{{ "{:,}".format(summary.amount_at_risk) }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Amount Recovered</div>
                    <div class="metric-val green">₹{{ "{:,}".format(summary.amount_recovered) }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Autonomous Action Rate</div>
                    <div class="metric-val blue">{{ "{:.1%}".format(summary.recovery_rate_overall) }}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Escalated / Filtered</div>
                    <div class="metric-val amber">{{ summary.escalated_to_human + summary.get('skipped_low_uplift', 0) }}</div>
                </div>
            </div>

            {% if degradation_incidents %}
            <div class="alert-panel">
                <div class="alert-panel-header">
                    <h3>⚡ Degradation Forecasting & Outage Alerts (Seasonal Z-Score Engine)</h3>
                    <span style="font-size: 12px; color: #fbbf24; font-weight: 600;">Systemic Outage Detection</span>
                </div>
                <div class="incident-grid">
                    {% for inc in degradation_incidents %}
                    <div class="incident-card">
                        <div class="inc-title">
                            <span>{{ inc.bank }} · {{ inc.method.upper() }}</span>
                            <span style="color: #fbbf24; font-size: 11px;">{{ inc.peak_z_score }}σ Anomaly</span>
                        </div>
                        <div class="inc-meta">
                            <div>Window: {{ inc.time_window }} ({{ inc.hours_duration }}h)</div>
                            <div>Failure Rate: <span style="color: #f87171; font-weight: 600;">{{ "{:.1%}".format(inc.peak_failure_rate) }}</span> (Norm: {{ "{:.1%}".format(inc.baseline_failure_rate) }})</div>
                            <div class="inc-impact">Impact: ₹{{ "{:,}".format(inc.total_impact_inr) }} ({{ inc.total_excess_failures }} excess fails)</div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}

            {% if latest_proposal %}
            <div class="drift-panel" id="drift-panel-container">
                <div class="drift-panel-header">
                    <h3>🛡️ Drift-Check Agent (Recovery Ops Governance)</h3>
                    <div>
                        {% if latest_proposal.status == 'pending_human_approval' %}
                            <span class="drift-status-badge drift-badge-pending">⏳ PENDING HUMAN APPROVAL</span>
                        {% elif latest_proposal.status == 'approved' %}
                            <span class="drift-status-badge drift-badge-approved">✅ POLICY APPROVED & ACTIVE</span>
                        {% else %}
                            <span class="drift-status-badge drift-badge-rejected">❌ POLICY REJECTED</span>
                        {% endif %}
                    </div>
                </div>

                <p style="margin: 0 0 12px 0; font-size: 13px; color: #cbd5e1;">
                    Evaluated on <b>{{ latest_proposal.evaluated_on }}</b> (n={{ "{:,}".format(latest_proposal.get('dataset_size', 1200)) }} records).
                    {% if latest_proposal.drift_detected %}
                    Detected <span style="color: #f87171; font-weight: 700;">drift degradation</span> on shifted distribution.
                    {% else %}
                    Model performance is stable within calibrated bounds.
                    {% endif %}
                </p>

                <div class="drift-grid">
                    <div class="drift-metric-box">
                        <div class="drift-metric-lbl">Success Predictor Accuracy</div>
                        <div class="drift-metric-val" style="color: #f87171;">
                            {{ "{:.1%}".format(latest_proposal.original_performance.get('accuracy', 0.85) if latest_proposal.original_performance else 0.85) }} → {{ "{:.1%}".format(latest_proposal.drift_batch_performance.get('accuracy', 0.78) if latest_proposal.drift_batch_performance else 0.78) }}
                        </div>
                    </div>
                    <div class="drift-metric-box">
                        <div class="drift-metric-lbl">Threshold Recommendation</div>
                        <div class="drift-metric-val" style="color: #60a5fa;">
                            {{ "{:.2f}".format(latest_proposal.current_threshold) }} → {{ "{:.2f}".format(latest_proposal.proposed_threshold) }}
                        </div>
                    </div>
                    <div class="drift-metric-box">
                        <div class="drift-metric-lbl">Est. Net INR Gain</div>
                        <div class="drift-metric-val" style="color: #34d399;">
                            +₹{{ "{:,}".format((latest_proposal.get('estimated_net_value_gain', 0) or 0) | int) }}
                        </div>
                    </div>
                    <div class="drift-metric-box">
                        <div class="drift-metric-lbl">Status</div>
                        <div class="drift-metric-val" style="color: #fbbf24;">
                            {{ latest_proposal.status.upper() }}
                        </div>
                    </div>
                </div>

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px;">
                    <span style="font-size: 12px; color: var(--text-muted);">
                        <b>Human-in-the-Loop Guarantee:</b> Policy changes are NEVER auto-applied to production.
                    </span>
                    {% if latest_proposal.status == 'pending_human_approval' %}
                    <div class="btn-action-group" id="proposal-actions">
                        <button class="btn-approve" onclick="resolveProposal('{{ latest_proposal.proposal_id }}', 'approve')">✓ Approve Policy Update</button>
                        <button class="btn-reject" onclick="resolveProposal('{{ latest_proposal.proposal_id }}', 'reject')">✕ Reject</button>
                    </div>
                    {% else %}
                    <span style="font-size: 12px; color: #94a3b8;">Proposal resolved ({{ latest_proposal.status }}).</span>
                    {% endif %}
                </div>
            </div>
            {% endif %}

            <!-- Audit Trail Copilot (LLM Narration Layer) -->
            <div class="copilot-card">
                <div class="copilot-header">
                    <div class="copilot-title">
                        <span>💬 Audit Trail Copilot</span>
                        <span class="copilot-badge">Gemini Flash Grounded</span>
                    </div>
                    <span style="font-size: 12px; color: var(--text-muted);">Read-Only Decision Narration</span>
                </div>
                <p style="margin: 0 0 14px 0; font-size: 13px; color: var(--text-muted);">
                    Ask natural-language questions about recovery decisions, statistics, or specific payment IDs. Grounded strictly in pre-computed deterministic facts — zero action capability.
                </p>

                <div class="copilot-prompt-chips">
                    <button class="prompt-chip" onclick="setCopilotQuery('How many payments were escalated to human review?')">"How many payments were escalated?"</button>
                    <button class="prompt-chip" onclick="setCopilotQuery('Which error code appears most often in the audit trail?')">"Which error code appears most often?"</button>
                    <button class="prompt-chip" onclick="setCopilotQuery('Why was payment pay_bnFbmOHnKYaXRv retried?')">"Why was payment pay_bnFbmOHnKYaXRv retried?"</button>
                    <button class="prompt-chip" onclick="setCopilotQuery('Approve a retry for payment pay_bnFbmOHnKYaXRv right now.')">"Approve a retry right now" (Refusal test)</button>
                    <button class="prompt-chip" onclick="setCopilotQuery('Should Razorpay change its refund policy?')">"Should Razorpay change policy?" (Out-of-scope test)</button>
                </div>

                <div class="copilot-input-group">
                    <input type="text" id="copilot-input" class="copilot-input" placeholder="Ask a question about the audit trail (e.g. 'Why was pay_... escalated?')" onkeydown="if(event.key==='Enter') submitCopilotQuestion()" />
                    <button id="copilot-btn" class="copilot-submit" onclick="submitCopilotQuestion()">⚡ Ask Copilot</button>
                </div>

                <div id="copilot-response" class="copilot-response-box">
                    <div id="copilot-answer-text" class="copilot-answer"></div>
                    <div class="copilot-grounding-meta">
                        <span id="copilot-grounding-badge" class="grounding-tag">🎯 Grounded on audit trail data</span>
                        <button class="context-toggle-btn" onclick="toggleContextJson()">Toggle Grounded JSON Context</button>
                    </div>
                    <pre id="copilot-json-viewer" class="grounded-json-viewer"></pre>
                </div>
            </div>

            <div class="table-container">
                <div class="table-header">
                    <h2>Live Audit Trail (Most Recent)</h2>
                    <span style="font-size: 12px; color: var(--text-muted);">Real-time PostgreSQL Audit Storage</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>Time (UTC)</th>
                            <th>Payment ID</th>
                            <th>Amount</th>
                            <th>Error Code</th>
                            <th>Category</th>
                            <th>P(Success)</th>
                            <th>Action Decided</th>
                            <th>Reason / Details</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for entry in recent_entries %}
                        <tr>
                            <td style="color: var(--text-muted);">{{ entry.timestamp[11:19] if entry.timestamp|length >= 19 else entry.timestamp }}</td>
                            <td><strong>{{ entry.payment_id }}</strong></td>
                            <td>₹{{ "{:,.2f}".format(entry.amount) }}</td>
                            <td><code>{{ entry.error_code }}</code></td>
                            <td>{{ entry.category }}</td>
                            <td><strong>{{ "{:.1%}".format(entry.predicted_success_prob) }}</strong></td>
                            <td>
                                {% if 'escalate' in entry.action %}
                                     <span class="pill pill-escalate">Escalate</span>
                                {% elif 'skipped' in entry.action %}
                                     <span class="pill pill-escalate" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24;">Skip (Low Uplift)</span>
                                {% elif 'retry' in entry.action %}
                                     <span class="pill pill-retry">{{ entry.action }}</span>
                                {% else %}
                                     <span class="pill pill-prompt">{{ entry.action }}</span>
                                {% endif %}
                            </td>
                            <td style="max-width: 320px; color: #cbd5e1; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="{{ entry.reason }}">{{ entry.reason }}</td>
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="8" style="text-align: center; padding: 32px; color: var(--text-muted);">
                                No audit events logged yet. Trigger a payment failure via the test checkout or run the orchestrator batch.
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <script>
            let lastContextData = null;

            function setCopilotQuery(text) {
                const input = document.getElementById('copilot-input');
                input.value = text;
                submitCopilotQuestion();
            }

            async function submitCopilotQuestion() {
                const input = document.getElementById('copilot-input');
                const btn = document.getElementById('copilot-btn');
                const respBox = document.getElementById('copilot-response');
                const answerText = document.getElementById('copilot-answer-text');
                const badge = document.getElementById('copilot-grounding-badge');
                const jsonViewer = document.getElementById('copilot-json-viewer');

                const question = input.value.trim();
                if (!question) return;

                btn.disabled = true;
                btn.innerText = 'Analyzing...';
                respBox.style.display = 'block';
                answerText.innerHTML = '<span style="color: #94a3b8;">Computing grounded context & retrieving answer from Gemini...</span>';
                badge.innerText = '⚡ Grounding in progress...';
                jsonViewer.style.display = 'none';

                try {
                    const res = await fetch('/api/v1/copilot', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ question: question })
                    });
                    const data = await res.json();
                    
                    lastContextData = data.context_used;
                    answerText.innerText = data.answer || 'No answer returned.';
                    
                    const count = data.grounded_record_count || 0;
                    if (count === 1) {
                        badge.innerText = '🎯 Grounded on 1 specific record + aggregate stats';
                    } else if (count > 1) {
                        badge.innerText = `🔍 Grounded on ${count} filtered records + aggregate stats`;
                    } else {
                        badge.innerText = '📊 Grounded on aggregate summary statistics';
                    }

                    if (lastContextData) {
                        jsonViewer.innerText = JSON.stringify(lastContextData, null, 2);
                    }
                } catch (err) {
                    answerText.innerText = 'Error querying Copilot: ' + err;
                    badge.innerText = '⚠️ Query Error';
                } finally {
                    btn.disabled = false;
                    btn.innerText = '⚡ Ask Copilot';
                }
            }

            function toggleContextJson() {
                const viewer = document.getElementById('copilot-json-viewer');
                viewer.style.display = viewer.style.display === 'block' ? 'none' : 'block';
            }

            async function resolveProposal(proposalId, action) {
                const actionsContainer = document.getElementById('proposal-actions');
                if (actionsContainer) {
                    actionsContainer.innerHTML = '<span style="color: #94a3b8; font-size: 12px;">Submitting governance decision...</span>';
                }
                try {
                    const res = await fetch(`/api/v1/policy-proposals/${proposalId}/${action}`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' }
                    });
                    const data = await res.json();
                    if (data.status === 'approved') {
                        alert(`Policy change approved! Optimal threshold updated to ${data.new_threshold}.`);
                        window.location.reload();
                    } else if (data.status === 'rejected') {
                        alert('Policy proposal rejected. Current threshold maintained.');
                        window.location.reload();
                    } else {
                        alert('Response: ' + JSON.stringify(data));
                        window.location.reload();
                    }
                } catch (err) {
                    alert('Error submitting governance decision: ' + err);
                }
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(
        html,
        summary=summary,
        recent_entries=recent_entries,
        degradation_incidents=CACHED_DEGRADATION_INCIDENTS,
        latest_proposal=latest_proposal,
        current_threshold=current_threshold,
    )


@app.route("/checkout", methods=["GET"])
def checkout_page():
    """Interactive checkout page with Razorpay test modal."""
    key_id = RAZORPAY_KEY_ID or "rzp_test_YourKeyHere"
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Razorpay Test Checkout — Recovery Agent Demo</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
        <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        <style>
            body {
                background: #0b0f19;
                color: #f3f4f6;
                font-family: 'Plus Jakarta Sans', sans-serif;
                display: flex;
                align-items: center;
                justify-content: center;
                min-height: 100vh;
                margin: 0;
            }
            .card {
                background: #111827;
                border: 1px solid #1f293d;
                border-radius: 16px;
                padding: 36px;
                max-width: 480px;
                width: 100%;
                box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            }
            h2 {
                margin: 0 0 12px 0;
                font-size: 22px;
                color: #60a5fa;
            }
            p {
                color: #9ca3af;
                font-size: 14px;
                line-height: 1.5;
            }
            .demo-box {
                background: #090d16;
                border: 1px solid #1e293b;
                border-radius: 10px;
                padding: 14px;
                margin: 20px 0;
                font-size: 13px;
            }
            .demo-box strong { color: #38bdf8; }
            .btn {
                width: 100%;
                background: #2563eb;
                color: white;
                padding: 14px;
                border: none;
                border-radius: 10px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: 0.2s;
            }
            .btn:hover {
                background: #1d4ed8;
            }
            .back-link {
                display: block;
                text-align: center;
                margin-top: 16px;
                color: #94a3b8;
                text-decoration: none;
                font-size: 13px;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Test Payment Checkout</h2>
            <p>Trigger a real Razorpay test-mode payment to test the end-to-end recovery agent webhook loop.</p>
            
            <div class="demo-box">
                <strong>How to test failure on camera:</strong>
                <ol style="margin: 8px 0 0 16px; padding: 0;">
                    <li>Click <b>Pay ₹1,299 Now</b>.</li>
                    <li>Enter any test card (e.g. <code>4111 2222 3333 4444</code>) + random CVV.</li>
                    <li>On the mock bank page, click <span style="color: #ef4444; font-weight: bold;">Failure</span>.</li>
                    <li>Razorpay dispatches <code>payment.failed</code> to the recovery webhook!</li>
                </ol>
            </div>

            <button class="btn" id="pay-btn" onclick="startPayment()">⚡ Pay ₹1,299 (Test Mode)</button>
            <a href="/" class="back-link">← Back to Agent Dashboard</a>
        </div>

        <script>
            async function startPayment() {
                const btn = document.getElementById('pay-btn');
                btn.disabled = true;
                btn.innerText = 'Creating Order...';

                try {
                    const res = await fetch('/create-test-order', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ amount: 129900 })
                    });
                    const data = await res.json();
                    
                    const options = {
                        "key": data.key_id,
                        "amount": data.amount,
                        "currency": "INR",
                        "name": "Recovery Agent Demo Store",
                        "description": "Test Mode Payment for Recovery Demo",
                        "order_id": data.order_id,
                        "handler": function (response){
                            alert("Payment Succeeded! ID: " + response.razorpay_payment_id);
                            window.location.href = "/";
                        },
                        "prefill": {
                            "name": "Aditya Kumar",
                            "email": "customer@example.com",
                            "contact": "+919876543210"
                        },
                        "theme": {
                            "color": "#2563eb"
                        }
                    };
                    const rzp = new Razorpay(options);
                    rzp.on('payment.failed', function (response){
                        console.log("Client-side payment failed caught:", response);
                        setTimeout(() => {
                            window.location.href = "/";
                        }, 1200);
                    });
                    rzp.open();
                } catch (err) {
                    alert("Error initiating test checkout: " + err);
                } finally {
                    btn.disabled = false;
                    btn.innerText = '⚡ Pay ₹1,299 (Test Mode)';
                }
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route("/create-test-order", methods=["POST"])
def create_test_order_endpoint():
    """Generates an order in Razorpay for the checkout page."""
    req_data = request.get_json(silent=True) or {}
    amount = req_data.get("amount", 129900)
    order = create_order(amount_in_paise=amount)
    return jsonify({
        "order_id": order.get("id"),
        "amount": amount,
        "key_id": RAZORPAY_KEY_ID or "rzp_test_mockKey",
    })


# -------------------------------------------------------------------------
# Versioned API Endpoints (/api/v1/...)
# -------------------------------------------------------------------------

@app.route("/api/v1/audit-trail", methods=["GET"])
@app.route("/api/audit-trail", methods=["GET"])
def api_audit_trail():
    """Returns JSON list of audit entries and summary metrics."""
    return jsonify({
        "summary": audit_trail.summary(),
        "entries": audit_trail.get_recent(100),
    })


@app.route("/api/v1/degradation-alerts", methods=["GET"])
@app.route("/api/degradation-alerts", methods=["GET"])
def api_degradation_alerts():
    """Returns cached real-time time-series outage detection alerts."""
    return jsonify({
        "status": "ok",
        "incidents": CACHED_DEGRADATION_INCIDENTS,
    }), 200


@app.route("/api/v1/cohort-report", methods=["GET"])
@app.route("/api/cohort-report", methods=["GET"])
def api_cohort_report():
    """Returns cached cohort analyst data for Recharts scatter chart rendering."""
    if not CACHED_COHORT_DATA:
        return jsonify({"status": "error", "message": "Cohort data not yet available."}), 503
    return jsonify({"status": "ok", **CACHED_COHORT_DATA}), 200


@app.route("/api/v1/bandit-results", methods=["GET"])
@app.route("/api/bandit-results", methods=["GET"])
def api_bandit_results():
    """Returns cached bandit simulation convergence data for Recharts line chart rendering."""
    if not CACHED_BANDIT_DATA:
        return jsonify({"status": "error", "message": "Bandit data not yet available."}), 503
    return jsonify({"status": "ok", **CACHED_BANDIT_DATA}), 200


@app.route("/api/v1/copilot", methods=["POST"])
@app.route("/api/copilot", methods=["POST"])
@limiter.limit("10 per minute")
def api_copilot():
    """
    Natural-language Q&A interface over the audit trail using Gemini.
    Accepts: {"question": "..."}
    Returns: {"answer": str, "grounded_record_count": int, "context_used": dict}
    Rate-limited to 10 requests/minute per IP to protect Gemini API costs.
    """
    payload = request.get_json(silent=True) or {}
    question = payload.get("question", "").strip()
    if not question:
        return jsonify({"status": "error", "message": "Question is required"}), 400
    if len(question) > 500:
        return jsonify({"status": "error", "message": "Question is too long (max 500 characters)"}), 400

    result = answer_question(question)
    return jsonify(result), 200


@app.route("/api/v1/policy-proposals", methods=["GET"])
@app.route("/api/policy-proposals", methods=["GET"])
def api_policy_proposals():
    """Returns list of all policy change proposals generated by Drift-Check agent."""
    proposals = load_proposals()
    return jsonify({
        "proposals": proposals,
        "current_threshold": get_success_prob_threshold(),
    }), 200


@app.route("/api/v1/policy-proposals/<proposal_id>/approve", methods=["POST"])
@app.route("/api/policy-proposals/<proposal_id>/approve", methods=["POST"])
@limiter.limit("10 per minute")
def api_approve_proposal(proposal_id):
    """Human-in-the-loop: Approves a proposed policy change and updates threshold configuration in DB and disk."""
    proposals = load_proposals()
    target = None
    for p in proposals:
        if p.get("proposal_id") == proposal_id:
            target = p
            break
    if not target:
        return jsonify({"status": "error", "message": f"Proposal {proposal_id} not found"}), 404

    new_threshold = target["proposed_threshold"]

    # 1. Update Database Threshold Configuration
    if is_db_configured():
        try:
            with get_db_session() as session:
                cfg = session.query(ThresholdConfig).filter_by(merchant_id=1).first()
                if cfg:
                    cfg.success_threshold = float(new_threshold)
                    cfg.updated_at = datetime.now(timezone.utc)
                else:
                    cfg = ThresholdConfig(merchant_id=1, success_threshold=float(new_threshold))
                    session.add(cfg)
                
                db_prop = session.query(PolicyChangeProposal).filter_by(id=proposal_id).first()
                if db_prop:
                    db_prop.status = "approved"
                    db_prop.resolved_at = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            print(f"[PolicyEngine] DB approve warning: {e}")

    # 2. Update threshold_config.json for local sync
    config_data = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception:
            pass
    config_data["optimal_threshold"] = new_threshold
    config_data["last_drift_approval"] = datetime.now(timezone.utc).isoformat()
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
    except Exception:
        pass

    target["status"] = "approved"
    target["resolved_at"] = datetime.now(timezone.utc).isoformat()
    save_proposal(target)

    return jsonify({
        "status": "approved",
        "proposal_id": proposal_id,
        "new_threshold": new_threshold,
        "proposal": target,
    }), 200


@app.route("/api/v1/policy-proposals/<proposal_id>/reject", methods=["POST"])
@app.route("/api/policy-proposals/<proposal_id>/reject", methods=["POST"])
@limiter.limit("10 per minute")
def api_reject_proposal(proposal_id):
    """Human-in-the-loop: Rejects a proposed policy change, preserving existing threshold."""
    proposals = load_proposals()
    target = None
    for p in proposals:
        if p.get("proposal_id") == proposal_id:
            target = p
            break
    if not target:
        return jsonify({"status": "error", "message": f"Proposal {proposal_id} not found"}), 404

    # 1. Update Database
    if is_db_configured():
        try:
            with get_db_session() as session:
                db_prop = session.query(PolicyChangeProposal).filter_by(id=proposal_id).first()
                if db_prop:
                    db_prop.status = "rejected"
                    db_prop.resolved_at = datetime.now(timezone.utc).isoformat()
        except Exception as e:
            print(f"[PolicyEngine] DB reject warning: {e}")

    target["status"] = "rejected"
    target["resolved_at"] = datetime.now(timezone.utc).isoformat()
    save_proposal(target)

    return jsonify({
        "status": "rejected",
        "proposal_id": proposal_id,
        "current_threshold": get_success_prob_threshold(),
        "proposal": target,
    }), 200


@app.route("/api/v1/trigger-drift-check", methods=["POST"])
@app.route("/api/trigger-drift-check", methods=["POST"])
def api_trigger_drift_check():
    """Runs drift detection evaluation on demand and returns the resulting proposal."""
    try:
        proposal = evaluate_drift()
        return jsonify({"status": "success", "proposal": proposal}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n=======================================================")
    print(f"[*] Razorpay Recovery Agent Server running on port {port}")
    print(f"   Dashboard: http://localhost:{port}/")
    print(f"   Test Checkout: http://localhost:{port}/checkout")
    print(f"   Webhook URL: http://localhost:{port}/webhook/razorpay")
    print(f"   Health Check: http://localhost:{port}/api/v1/health")
    print(f"=======================================================\n")

    app.run(host="0.0.0.0", port=port, debug=False)
