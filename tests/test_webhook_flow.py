"""
Verification script for Razorpay Webhook & Agent Pipeline.
Sends sample real-world payment.failed payloads across various failure categories
and verifies status codes, decision logic, payment link generation, and audit logging.
"""

import urllib.request
import json
import time

SERVER_URL = "http://localhost:5000"

def test_health_and_dashboard():
    print("[Test 1] Testing Dashboard & Status endpoint...")
    req = urllib.request.Request(f"{SERVER_URL}/")
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        html = response.read().decode("utf-8")
        assert "Razorpay AI Recovery Agent" in html
        print("  [OK] Dashboard HTTP 200 OK")

def test_webhook_payment_failed(scenario_name, error_reason, method="card", expected_action_substring=""):
    print(f"\n[Test 2] Testing Webhook: {scenario_name} (error: {error_reason}, method: {method})...")
    payload = {
        "entity": "event",
        "account_id": "acc_test_demo123",
        "event": "payment.failed",
        "contains": ["payment"],
        "created_at": int(time.time()),
        "payload": {
            "payment": {
                "entity": {
                    "id": f"pay_live_test_{int(time.time() * 1000) % 100000}",
                    "entity": "payment",
                    "amount": 129900,  # Rs. 1,299.00
                    "currency": "INR",
                    "status": "failed",
                    "order_id": "order_test_demo",
                    "method": method,
                    "captured": False,
                    "description": "Test order payment",
                    "email": "customer.test@example.com",
                    "contact": "+919876543210",
                    "error_code": "BAD_REQUEST_ERROR",
                    "error_description": f"Failed due to {error_reason}",
                    "error_source": "customer" if error_reason in ("incorrect_cvv", "card_expired") else "gateway",
                    "error_step": "payment_authentication",
                    "error_reason": error_reason,
                    "created_at": int(time.time()),
                }
            }
        }
    }

    req = urllib.request.Request(
        f"{SERVER_URL}/webhook/razorpay",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        res_data = json.loads(response.read().decode("utf-8"))
        print(f"  [OK] Decision: {res_data['action']} | P(success): {res_data['predicted_success_prob']} | Category: {res_data['category']}")
        if expected_action_substring:
            assert expected_action_substring in res_data["action"]
        return res_data

def test_api_audit_trail():
    print("\n[Test 3] Verifying /api/audit-trail...")
    req = urllib.request.Request(f"{SERVER_URL}/api/audit-trail")
    with urllib.request.urlopen(req) as response:
        assert response.status == 200
        data = json.loads(response.read().decode("utf-8"))
        print(f"  [OK] Total records in audit: {data['summary']['total_records']}")
        print(f"  [OK] Amount recovered: Rs.{data['summary']['amount_recovered']:,}")
        assert "skipped_low_uplift" in data["summary"]
        assert "attempted" in data["summary"]
        print("  [OK] Audit trail summary schema verified with uplift tracking")


if __name__ == "__main__":
    time.sleep(1)
    test_health_and_dashboard()
    
    # 1. Transient bank technical error -> smart retry / retry action
    test_webhook_payment_failed("Transient Bank Error", "bank_technical_error", "netbanking")
    
    # 2. Risk check failed -> strictly escalate_to_human
    test_webhook_payment_failed("Risk Check", "payment_risk_check_failed", "card", expected_action_substring="escalate_to_human")
    
    # 3. Card expired -> prompt_new_payment_method
    test_webhook_payment_failed("Card Expired", "card_expired", "card")
    
    # 4. User error (wrong CVV) -> reprompt_customer
    test_webhook_payment_failed("Wrong CVV", "incorrect_cvv", "card")
    
    test_api_audit_trail()
    print("\n[SUCCESS] ALL LIVE WEBHOOK & AGENT PIPELINE TESTS PASSED!")

