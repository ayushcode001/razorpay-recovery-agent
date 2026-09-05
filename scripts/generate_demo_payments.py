import hmac
import hashlib
import json
import time
import urllib.request
import os
from dotenv import load_dotenv

load_dotenv()

secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "Ayush@123")
url = "https://razorpay-recovery-agent-rnq8.onrender.com/webhook/razorpay"

test_cases = [
    {
        "id": f"pay_live_{int(time.time())}_1",
        "amount": 149900,
        "method": "upi",
        "error_code": "bank_technical_error",
        "email": "priya.sharma@example.com",
        "contact": "+919876500001",
    },
    {
        "id": f"pay_live_{int(time.time())}_2",
        "amount": 499900,
        "method": "card",
        "error_code": "insufficient_funds",
        "email": "rahul.verma@example.com",
        "contact": "+919876500002",
    },
    {
        "id": f"pay_live_{int(time.time())}_3",
        "amount": 85000,
        "method": "card",
        "error_code": "card_expired",
        "email": "ananya.deshmukh@example.com",
        "contact": "+919876500003",
    },
    {
        "id": f"pay_live_{int(time.time())}_4",
        "amount": 1500000,
        "method": "netbanking",
        "error_code": "payment_risk_check_failed",
        "email": "vikram.mehta@example.com",
        "contact": "+919876500004",
    },
    {
        "id": f"pay_live_{int(time.time())}_5",
        "amount": 320000,
        "method": "upi",
        "error_code": "incorrect_otp",
        "email": "sneha.patel@example.com",
        "contact": "+919876500005",
    },
]

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
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
        },
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"[{idx}/5] Success: {tc['id']} -> Action: {res.get('action')}, Category: {res.get('category')}")
    time.sleep(1)

print("All 5 test payments generated and processed successfully.")
