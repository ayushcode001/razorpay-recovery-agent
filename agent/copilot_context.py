"""
Deterministic retrieval layer for the Audit Trail Copilot.

Pure Python/pandas retrieval:
  - Bounded context construction
  - Exact payment ID lookup
  - Vocabulary-constrained keyword filtering (no free-text leaking)
  - Grounded summary statistics reusing AuditTrail logic
"""

import os
import re
import json
import pandas as pd
from typing import Optional, Dict, Any, List

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_AUDIT_PATH = os.path.join(PROJECT_ROOT, "audit_logs", "audit_trail.json")

from agent.taxonomy import ERROR_CODE_TAXONOMY, CATEGORY_POLICY
from agent.audit import AuditTrail

# Build the closed known vocabulary for filtering
KNOWN_ERROR_CODES = set(ERROR_CODE_TAXONOMY.keys())
KNOWN_CATEGORIES = set(CATEGORY_POLICY.keys())
KNOWN_ACTIONS = {p["action"] for p in CATEGORY_POLICY.values()} | {"skipped_low_uplift", "escalate_to_human"}
KNOWN_VOCABULARY = KNOWN_ERROR_CODES | KNOWN_CATEGORIES | KNOWN_ACTIONS


def load_audit_trail(path: Optional[str] = None) -> pd.DataFrame:
    """Loads audit trail from JSON file into a pandas DataFrame."""
    audit_path = path or DEFAULT_AUDIT_PATH
    if not os.path.exists(audit_path):
        return pd.DataFrame()
    with open(audit_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    if not records:
        return pd.DataFrame()
    return pd.DataFrame(records)


def compute_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Computes grounded aggregate metrics from audit trail DataFrame,
    extending AuditTrail.summary() logic without duplicating business rules.
    """
    if df.empty:
        return {
            "total_records": 0,
            "attempted": 0,
            "skipped_low_uplift": 0,
            "escalated_to_human": 0,
            "amount_at_risk": 0,
            "amount_recovered": 0,
            "amount_wasted_on_failed_attempts": 0,
            "net_value": 0,
            "recovery_rate_overall": 0.0,
            "recovery_rate_of_attempted": 0.0,
            "counts_by_category": {},
            "counts_by_action": {},
            "counts_by_error_code": {},
        }

    # Convert records back to dict list to feed into AuditTrail.summary()
    audit = AuditTrail()
    audit.entries = df.to_dict(orient="records")
    base_summary = audit.summary()

    # Calculate net value & distribution breakdowns
    net_value = base_summary["amount_recovered"] - base_summary["amount_wasted_on_failed_attempts"]
    base_summary["net_value"] = net_value

    if "category" in df.columns:
        base_summary["counts_by_category"] = df["category"].value_counts().to_dict()
    else:
        base_summary["counts_by_category"] = {}

    if "action" in df.columns:
        base_summary["counts_by_action"] = df["action"].value_counts().to_dict()
    else:
        base_summary["counts_by_action"] = {}

    if "error_code" in df.columns:
        base_summary["counts_by_error_code"] = df["error_code"].value_counts().to_dict()
    else:
        base_summary["counts_by_error_code"] = {}

    return base_summary


def find_payment_by_id(df: pd.DataFrame, payment_id: str) -> Optional[Dict[str, Any]]:
    """Exact lookup for a payment ID (e.g. pay_XXXX). Returns single dict or None."""
    if df.empty or "payment_id" not in df.columns:
        return None
    matches = df[df["payment_id"] == payment_id]
    if matches.empty:
        return None
    # Return the first matching record as a clean dictionary
    return matches.iloc[0].to_dict()


def filter_by_keyword(df: pd.DataFrame, keyword: str, max_results: int = 20) -> List[Dict[str, Any]]:
    """
    Filters audit trail by a recognized domain term in KNOWN_VOCABULARY.
    Ensures bounded retrieval (max 20 records) and prevents arbitrary text injection.
    """
    clean_kw = keyword.strip().lower()
    if clean_kw not in KNOWN_VOCABULARY or df.empty:
        return []

    conditions = []
    if "error_code" in df.columns and clean_kw in KNOWN_ERROR_CODES:
        conditions.append(df["error_code"] == clean_kw)
    if "category" in df.columns and clean_kw in KNOWN_CATEGORIES:
        conditions.append(df["category"] == clean_kw)
    if "action" in df.columns and clean_kw in KNOWN_ACTIONS:
        conditions.append(df["action"] == clean_kw)

    if not conditions:
        return []

    combined_filter = conditions[0]
    for cond in conditions[1:]:
        combined_filter = combined_filter | cond

    matched_df = df[combined_filter].head(max_results)
    return matched_df.to_dict(orient="records")


def extract_payment_ids(text: str) -> List[str]:
    """Extracts all pay_ patterns from user query."""
    return re.findall(r"\bpay_[A-Za-z0-9_]+\b", text)


def extract_matched_keywords(text: str) -> List[str]:
    """Finds words or tokens in query that match the closed domain vocabulary."""
    text_lower = text.lower()
    found = []
    # Check multi-word or single-word known terms
    for term in sorted(KNOWN_VOCABULARY, key=len, reverse=True):
        # Match as word boundary or exact token
        pattern = r"(?:\b|_)" + re.escape(term) + r"(?:\b|_)"
        if re.search(pattern, text_lower) or term in text_lower:
            found.append(term)
    return found


def build_context(question: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Orchestrates deterministic retrieval for a given question:
      - Computes aggregate summary statistics
      - Extracts specific payment ID record if mentioned
      - Extracts filtered subset of records (capped at 20) for recognized domain terms
    Returns a bounded dictionary to be fed directly to the LLM prompt.
    """
    if df is None:
        df = load_audit_trail()

    summary = compute_summary_stats(df)
    
    # 1. Payment ID exact match
    payment_ids = extract_payment_ids(question)
    payment_record = None
    if payment_ids:
        payment_record = find_payment_by_id(df, payment_ids[0])

    # 2. Domain keyword matching
    keywords = extract_matched_keywords(question)
    filtered_records = []
    if keywords and not payment_record:
        # Fetch bounded records for the most specific recognized keyword
        filtered_records = filter_by_keyword(df, keywords[0], max_results=20)

    grounded_count = 0
    if payment_record:
        grounded_count = 1
    elif filtered_records:
        grounded_count = len(filtered_records)

    context = {
        "summary_statistics": summary,
        "matched_payment_id": payment_ids[0] if payment_ids else None,
        "payment_record": payment_record,
        "matched_keywords": keywords,
        "filtered_records": filtered_records,
        "grounded_record_count": grounded_count,
    }
    return context
