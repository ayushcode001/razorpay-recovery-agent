"""
Every decision the agent makes gets appended here. This is what you show
live in the pitch video -- a real, timestamped record of why the agent did
(or deliberately did not) act on money.
"""

import os
import json
from datetime import datetime, timezone

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_AUDIT_PATH = os.path.join(PROJECT_ROOT, "audit_logs", "audit_trail.json")


class AuditTrail:
    def __init__(self):
        self.entries = []

    def log(self, record: dict, decision: dict, outcome: dict | None = None):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "payment_id": record["id"],
            "amount": record["amount"],
            "error_code": record["error_code"],
            "category": decision["category"],
            "action": decision["action"],
            "attempted": decision["attempted"],
            "predicted_success_prob": round(decision["predicted_success_prob"], 3),
            "reason": decision["reason"],
            "outcome": outcome,  # filled in after the (simulated/real) attempt resolves
        }
        self.entries.append(entry)
        return entry

    def save(self, path=None):
        out_path = path or DEFAULT_AUDIT_PATH
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w") as f:
            json.dump(self.entries, f, indent=2)


    def summary(self):
        total = len(self.entries)
        attempted = sum(1 for e in self.entries if e["attempted"])
        escalated = total - attempted
        recovered_amount = sum(
            e["amount"] for e in self.entries
            if e["attempted"] and isinstance(e.get("outcome"), dict) and e["outcome"].get("succeeded") is True
        )
        wasted_attempt_amount = sum(
            e["amount"] for e in self.entries
            if e["attempted"] and isinstance(e.get("outcome"), dict) and e["outcome"].get("succeeded") is False
        )
        at_risk_amount = sum(e["amount"] for e in self.entries)

        return {
            "total_records": total,
            "attempted": attempted,
            "escalated_to_human": escalated,
            "amount_at_risk": at_risk_amount,
            "amount_recovered": recovered_amount,
            "amount_wasted_on_failed_attempts": wasted_attempt_amount,
            "recovery_rate_overall": round(recovered_amount / at_risk_amount, 4) if at_risk_amount else 0,
            "recovery_rate_of_attempted": round(
                recovered_amount / sum(e["amount"] for e in self.entries if e["attempted"]), 4
            ) if attempted else 0,
        }
