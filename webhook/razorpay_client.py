"""
Razorpay API Client helper for test-mode checkout orders, payment links, and signature verification.
"""

import os
import hmac
import hashlib
import time
from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")

_client = None


def get_razorpay_client():
    """Initializes and returns the Razorpay SDK client if keys are present."""
    global _client
    if _client is not None:
        return _client
    if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET:
        return None
    try:
        import razorpay
        _client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
        _client.enable_retry(True)
        return _client
    except Exception as e:
        print(f"[RazorpayClient] Warning: Could not initialize razorpay client: {e}")
        return None


def create_order(amount_in_paise: int, currency: str = "INR", receipt: str = None) -> dict:
    """
    Creates an order in Razorpay (Test Mode) for Checkout.js.
    Amount must be in currency subunits (e.g. 50000 = ₹500.00).
    """
    client = get_razorpay_client()
    if not client:
        return {
            "id": f"order_mock_{int(time.time())}",
            "amount": amount_in_paise,
            "currency": currency,
            "status": "created",
            "mock": True,
        }
    order_data = {
        "amount": amount_in_paise,
        "currency": currency,
        "receipt": receipt or f"rcpt_{int(time.time())}",
        "payment_capture": 1,
    }
    return client.order.create(data=order_data)


def create_payment_link(
    amount_in_paise: int,
    description: str,
    customer_email: str = None,
    customer_contact: str = None,
    notify_customer: bool = True,
) -> dict:
    """
    Generates a new Razorpay Payment Link for autonomous recovery retry.
    This creates an active link where the customer can complete their transaction.
    """
    client = get_razorpay_client()
    if not client:
        mock_id = f"plink_mock_{int(time.time())}"
        return {
            "id": mock_id,
            "short_url": f"https://rzp.io/i/mock_{mock_id}",
            "amount": amount_in_paise,
            "status": "created",
            "mock": True,
        }

    link_data = {
        "amount": amount_in_paise,
        "currency": "INR",
        "accept_partial": False,
        "description": description[:250],
        "customer": {},
        "notify": {
            "sms": notify_customer,
            "email": notify_customer,
        },
        "reminder_enable": True,
    }
    if customer_email:
        link_data["customer"]["email"] = customer_email
    if customer_contact:
        link_data["customer"]["contact"] = customer_contact

    return client.payment_link.create(link_data)


def verify_webhook_signature(raw_body: bytes, signature: str, secret: str = None) -> bool:
    """
    Verifies that incoming webhook requests genuinely originate from Razorpay.
    """
    webhook_secret = secret or RAZORPAY_WEBHOOK_SECRET
    if not webhook_secret:
        # If no secret is configured in development, log warning and allow through
        return True

    expected_signature = hmac.new(
        key=webhook_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(expected_signature, signature or "")
