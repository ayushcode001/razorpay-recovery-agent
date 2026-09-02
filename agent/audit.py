"""
Audit Trail — Persistent Decision Log & Financial Accounting.
Every decision the agent makes gets recorded here: timestamped, explainable,
and stored in PostgreSQL (with JSON fallback for local offline scripts).
"""

import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_AUDIT_PATH = os.path.join(PROJECT_ROOT, "audit_logs", "audit_trail.json")

from agent.db import is_db_configured, get_db_session
from agent.db_models import AuditTrailEntry


class AuditTrail:
    def __init__(self, merchant_id: int = 1):
        self.merchant_id = merchant_id
        self.entries: List[Dict[str, Any]] = []

    def log(self, record: dict, decision: dict, outcome: dict | None = None) -> dict:
        timestamp_str = datetime.now(timezone.utc).isoformat()
        outcome_succeeded = None
        if outcome and isinstance(outcome, dict):
            outcome_succeeded = outcome.get("succeeded")

        entry = {
            "timestamp": timestamp_str,
            "payment_id": record["id"],
            "amount": record["amount"],
            "error_code": record["error_code"],
            "category": decision["category"],
            "action": decision["action"],
            "attempted": decision["attempted"],
            "predicted_success_prob": round(float(decision["predicted_success_prob"]), 3),
            "estimated_uplift": round(float(decision["estimated_uplift"]), 3) if decision.get("estimated_uplift") is not None else None,
            "reason": decision["reason"],
            "outcome": outcome,
        }
        self.entries.append(entry)

        # Write to PostgreSQL if configured
        if is_db_configured():
            try:
                with get_db_session() as session:
                    db_entry = AuditTrailEntry(
                        merchant_id=self.merchant_id,
                        timestamp=timestamp_str,
                        payment_id=record["id"],
                        amount=float(record["amount"]),
                        error_code=str(record["error_code"]),
                        category=str(decision["category"]),
                        action=str(decision["action"]),
                        attempted=bool(decision["attempted"]),
                        predicted_success_prob=float(decision["predicted_success_prob"]),
                        estimated_uplift=float(decision["estimated_uplift"]) if decision.get("estimated_uplift") is not None else None,
                        reason=str(decision["reason"]),
                        outcome_succeeded=outcome_succeeded,
                    )
                    session.add(db_entry)
            except Exception as e:
                print(f"[AuditTrail] DB write warning: {e}")

        return entry

    def save(self, path=None):
        """Optional JSON persistence fallback."""
        out_path = path or DEFAULT_AUDIT_PATH
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(self.entries, f, indent=2)

    def get_recent(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Returns the most recent audit entries (from DB if available, else memory)."""
        if is_db_configured():
            try:
                with get_db_session() as session:
                    rows = (
                        session.query(AuditTrailEntry)
                        .filter_by(merchant_id=self.merchant_id)
                        .order_by(AuditTrailEntry.id.desc())
                        .limit(limit)
                        .all()
                    )
                    return [r.to_dict() for r in rows]
            except Exception as e:
                print(f"[AuditTrail] DB read warning: {e}")

        return list(reversed(self.entries[-limit:]))

    def summary(self) -> Dict[str, Any]:
        """Calculates aggregate metrics from DB if connected, else from in-memory entries."""
        if is_db_configured():
            try:
                with get_db_session() as session:
                    rows = session.query(AuditTrailEntry).filter_by(merchant_id=self.merchant_id).all()
                    entries = [r.to_dict() for r in rows]
                    return self._compute_metrics(entries)
            except Exception as e:
                print(f"[AuditTrail] DB summary warning: {e}")

        return self._compute_metrics(self.entries)

    @staticmethod
    def _compute_metrics(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(entries)
        attempted = sum(1 for e in entries if e.get("attempted"))
        skipped_low_uplift = sum(1 for e in entries if e.get("action") == "skipped_low_uplift")
        escalated = sum(1 for e in entries if not e.get("attempted") and e.get("action") != "skipped_low_uplift")
        recovered_amount = sum(
            e["amount"] for e in entries
            if e.get("attempted") and isinstance(e.get("outcome"), dict) and e["outcome"].get("succeeded") is True
        )
        wasted_attempt_amount = sum(
            e["amount"] for e in entries
            if e.get("attempted") and isinstance(e.get("outcome"), dict) and e["outcome"].get("succeeded") is False
        )
        at_risk_amount = sum(e.get("amount", 0) for e in entries)
        attempted_amount = sum(e.get("amount", 0) for e in entries if e.get("attempted"))

        return {
            "total_records": total,
            "attempted": attempted,
            "skipped_low_uplift": skipped_low_uplift,
            "escalated_to_human": escalated,
            "amount_at_risk": at_risk_amount,
            "amount_recovered": recovered_amount,
            "amount_wasted_on_failed_attempts": wasted_attempt_amount,
            "recovery_rate_overall": round(recovered_amount / at_risk_amount, 4) if at_risk_amount else 0,
            "recovery_rate_of_attempted": round(recovered_amount / attempted_amount, 4) if attempted_amount else 0,
        }
