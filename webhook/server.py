"""
Live Razorpay Webhook Receiver & Autonomous Recovery Agent Server.

Endpoints:
  POST /webhook/razorpay    - Receives real payment.failed webhooks from Razorpay
  GET  /checkout            - Interactive test checkout to trigger real test-mode failures
  POST /create-test-order   - Creates Razorpay order for Checkout.js modal
  GET  /                    - Live Dashboard showing real-time decisions & audit trail
  GET  /api/audit-trail     - JSON API for live audit events
"""

import os
import sys
import time
import json
from datetime import datetime, timezone
import pandas as pd
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from dotenv import load_dotenv

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from agent.taxonomy import category_for
from agent.policy_engine import decide_action
from agent.audit import AuditTrail
from agent.success_predictor import train_and_eval, FEATURE_COLUMNS_NUM, FEATURE_COLUMNS_CAT
from webhook.razorpay_client import (
    RAZORPAY_KEY_ID,
    create_order,
    create_payment_link,
    verify_webhook_signature,
)
from webhook.notifier import send_recovery_notification

load_dotenv()

app = Flask(__name__)

# Initialize Global Audit Trail & Model Pipeline
AUDIT_LOG_PATH = os.path.join(PROJECT_ROOT, "audit_logs", "audit_trail.json")
audit_trail = AuditTrail()
if os.path.exists(AUDIT_LOG_PATH):
    try:
        with open(AUDIT_LOG_PATH, "r") as f:
            audit_trail.entries = json.load(f)
    except Exception:
        pass

# Train success predictor model once at server startup
DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "synthetic_failed_payments.json")
print("[Agent Server] Training success predictor pipeline...")
ml_pipeline, ml_metrics = train_and_eval(DATASET_PATH)
print(f"[Agent Server] Success Predictor ready (accuracy: {ml_metrics['classification_report']['accuracy']:.1%})")


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


@app.route("/", methods=["GET"])
def dashboard():
    """Live audit trail dashboard for demo monitoring."""
    summary = audit_trail.summary()
    recent_entries = list(reversed(audit_trail.entries[-25:]))
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
                margin-bottom: 28px;
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
                    <div class="metric-label">Escalated to Human Review</div>
                    <div class="metric-val amber">{{ summary.escalated_to_human }} ({{ "{:.1%}".format(summary.escalated_to_human / (summary.total_records or 1)) }})</div>
                </div>
            </div>

            <div class="table-container">
                <div class="table-header">
                    <h2>Live Audit Trail (Most Recent)</h2>
                    <span style="font-size: 12px; color: var(--text-muted);">Auto-refreshes on incoming webhooks</span>
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
                            <td style="color: var(--text-muted);">{{ entry.timestamp[11:19] }}</td>
                            <td><strong>{{ entry.payment_id }}</strong></td>
                            <td>₹{{ "{:,.2f}".format(entry.amount) }}</td>
                            <td><code>{{ entry.error_code }}</code></td>
                            <td>{{ entry.category }}</td>
                            <td><strong>{{ "{:.1%}".format(entry.predicted_success_prob) }}</strong></td>
                            <td>
                                {% if 'escalate' in entry.action %}
                                    <span class="pill pill-escalate">Escalate</span>
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
    </body>
    </html>
    """
    return render_template_string(html, summary=summary, recent_entries=recent_entries)


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
                        body: JSON.stringify({ amount: 129900 }) // ₹1,299.00
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
    amount = req_data.get("amount", 129900)  # Default: ₹1299 (in paise)
    order = create_order(amount_in_paise=amount)
    return jsonify({
        "order_id": order.get("id"),
        "amount": amount,
        "key_id": RAZORPAY_KEY_ID or "rzp_test_mockKey",
    })


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
        # Acknowledge other events gracefully
        return jsonify({"status": "ignored", "event": event_type}), 200

    # 2. Extract payment entity
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    if not payment_entity:
        return jsonify({"status": "error", "message": "Missing payment entity"}), 400

    # Adapt Razorpay webhook schema to Agent schema
    # In Razorpay webhooks: error_reason contains granular failure code (e.g. insufficient_funds)
    # error_code contains high-level category (e.g. BAD_REQUEST_ERROR)
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
        "retry_count": 0,  # Fresh webhook failure
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
            # Create a recovery payment link
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
            # Create payment link and send customer notification
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

    # 6. Log to Audit Trail
    audit_trail.log(
        record=record,
        decision=decision,
        outcome={"execution": execution_result} if execution_result else None,
    )
    audit_trail.save(AUDIT_LOG_PATH)

    return jsonify({
        "status": "processed",
        "payment_id": payment_id,
        "action": decision["action"],
        "category": decision["category"],
        "predicted_success_prob": round(prob, 3),
        "execution": execution_result,
    }), 200


@app.route("/api/audit-trail", methods=["GET"])
def api_audit_trail():
    """Returns JSON list of audit entries and summary metrics."""
    return jsonify({
        "summary": audit_trail.summary(),
        "entries": audit_trail.entries,
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    print(f"\n=======================================================")
    print(f"[*] Razorpay Recovery Agent Server running on port {port}")
    print(f"   Dashboard: http://localhost:{port}/")
    print(f"   Test Checkout: http://localhost:{port}/checkout")
    print(f"   Webhook URL: http://localhost:{port}/webhook/razorpay")
    print(f"=======================================================\n")

    app.run(host="0.0.0.0", port=port, debug=False)

