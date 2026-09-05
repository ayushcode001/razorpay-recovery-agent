import hmac
import hashlib
import json
import time
import urllib.request
import os
from dotenv import load_dotenv

load_dotenv()

secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "Ayush@123")
targets = [
    "http://localhost:5000",
    "https://razorpay-recovery-agent-rnq8.onrender.com",
]

test_cases = [
    {
        "id": f"pay_demo_{int(time.time())}_1",
        "amount": 149900,
        "method": "upi",
        "error_code": "bank_technical_error",
        "email": "priya.sharma@example.com",
        "contact": "+919876500001",
    },
    {
        "id": f"pay_demo_{int(time.time())}_2",
        "amount": 499900,
        "method": "card",
        "error_code": "insufficient_funds",
        "email": "rahul.verma@example.com",
        "contact": "+919876500002",
    },
    {
        "id": f"pay_demo_{int(time.time())}_3",
        "amount": 85000,
        "method": "card",
        "error_code": "card_expired",
        "email": "ananya.deshmukh@example.com",
        "contact": "+919876500003",
    },
    {
        "id": f"pay_demo_{int(time.time())}_4",
        "amount": 1500000,
        "method": "netbanking",
        "error_code": "payment_risk_check_failed",
        "email": "vikram.mehta@example.com",
        "contact": "+919876500004",
    },
    {
        "id": f"pay_demo_{int(time.time())}_5",
        "amount": 320000,
        "method": "upi",
        "error_code": "incorrect_otp",
        "email": "sneha.patel@example.com",
        "contact": "+919876500005",
    },
]

for base_url in targets:
    webhook_url = f"{base_url}/webhook/razorpay"
    print(f"\n--- Sending 5 test payments to {base_url} ---")
    for idx, tc in enumerate(test_cases, 1):
        payload = {
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": tc["id"],
                        "amount": tc["amount"],
                        "currency": "INR",
                        "method": tc["method"],
                        "error_code": tc["error_code"],
                        "error_reason": tc["error_code"],
                        "error_source": "gateway",
                        "error_step": "payment_processing",
                        "created_at": int(time.time()),
                        "email": tc["email"],
                        "contact": tc["contact"],
                    }
                }
            },
        }
        body = json.dumps(payload).encode("utf-8")
        sig = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        try:
            req = urllib.request.Request(
                webhook_url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    "X-Razorpay-Signature": sig,
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                print(f"  [{idx}/5] Success: {tc['id']} -> Action: {res.get('action')}, Category: {res.get('category')}")
        except Exception as e:
            print(f"  [{idx}/5] Skipped/Error: {tc['id']} ({e})")
        time.sleep(0.5)

    # Trigger drift check to generate policy proposal
    drift_url = f"{base_url}/api/v1/trigger-drift-check"
    try:
        drift_req = urllib.request.Request(
            drift_url,
            data=b"{}",
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(drift_req, timeout=15) as resp:
            d_res = json.loads(resp.read().decode("utf-8"))
            prop_id = d_res.get("proposal", {}).get("proposal_id")
            print(f"  Policy Proposal Created on {base_url}: {prop_id}")
    except Exception as e:
        print(f"  Drift trigger notice on {base_url}: {e}")

print("\nAll demo payments and policy proposals populated successfully.")
