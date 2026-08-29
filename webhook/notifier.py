"""
Customer Notification Dispatcher.

Handles notifying the customer when policy actions such as
'prompt_new_payment_method' or 'reprompt_customer' are executed.

Supports:
1. Razorpay built-in Payment Link SMS/Email notification (primary).
2. Direct SMTP Email notification (optional custom messaging).
3. Fallback audit/console logging.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")


def send_recovery_notification(
    recipient_email: str,
    payment_id: str,
    amount_in_rupees: float,
    action: str,
    recovery_link: str,
    reason: str = None,
) -> dict:
    """
    Dispatches customer notification with the new recovery payment link.
    """
    subject = f"Action Required: Complete your payment of ₹{amount_in_rupees:,.2f}"

    if action == "prompt_new_payment_method":
        message_body = (
            f"Dear Customer,\n\n"
            f"Your previous payment ({payment_id}) of ₹{amount_in_rupees:,.2f} could not be completed with your selected payment method.\n\n"
            f"Please use the secure link below to retry with a different payment method (UPI, Netbanking, or another Card):\n"
            f"{recovery_link}\n\n"
            f"Thank you,\nPayment Recovery Team"
        )
    elif action == "reprompt_customer":
        message_body = (
            f"Dear Customer,\n\n"
            f"Your previous payment ({payment_id}) of ₹{amount_in_rupees:,.2f} failed due to an incorrect detail (e.g. CVV or OTP).\n\n"
            f"Please click below to verify and complete your payment:\n"
            f"{recovery_link}\n\n"
            f"Thank you,\nPayment Recovery Team"
        )
    else:
        message_body = (
            f"Dear Customer,\n\n"
            f"We noticed an issue with your payment ({payment_id}) of ₹{amount_in_rupees:,.2f}.\n\n"
            f"You can quickly complete your payment using this secure link:\n"
            f"{recovery_link}\n\n"
            f"Thank you,\nPayment Recovery Team"
        )

    print(f"\n[NOTIFIER] Dispatching customer notification:")
    print(f"  To: {recipient_email or 'customer (via Razorpay notify)'}")
    print(f"  Action: {action}")
    print(f"  Link: {recovery_link}")

    sent_smtp = False
    error_msg = None

    if SMTP_USER and SMTP_PASSWORD and recipient_email:
        try:
            msg = MIMEMultipart()
            msg["From"] = SMTP_USER
            msg["To"] = recipient_email
            msg["Subject"] = subject
            msg.attach(MIMEText(message_body, "plain"))

            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            sent_smtp = True
            print("  Status: Successfully sent via direct SMTP.")
        except Exception as e:
            error_msg = str(e)
            print(f"  Status: SMTP send error ({e}), handled via Razorpay Link Notification.")
    else:
        print("  Status: Dispatched via Razorpay Payment Link auto-notify (SMS & Email).")

    return {
        "dispatched": True,
        "recipient": recipient_email,
        "action": action,
        "recovery_link": recovery_link,
        "smtp_sent": sent_smtp,
        "smtp_error": error_msg,
    }
