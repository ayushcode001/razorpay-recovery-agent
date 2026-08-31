"""
Audit Trail Copilot — LLM Narration Layer.

Calls Google Gemini API (gemini-2.5-flash) using strictly grounded,
pre-computed deterministic context from copilot_context.py.
"""

import os
import sys
import json
import requests
from typing import Optional, Dict, Any
import pandas as pd
from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

load_dotenv()

from agent.copilot_context import build_context, load_audit_trail

CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    "gemini-flash-latest",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]

SYSTEM_PROMPT = """You explain decisions made by an autonomous payment recovery agent, using ONLY the JSON context provided below. Never state a number, count, or fact that isn't present in the context. If the question asks about something not covered by the context, say so plainly rather than guessing. You cannot take any action — you can only explain past decisions. If asked to perform an action (approve, retry, refund, change a setting), decline and explain that you're a read-only explanation layer. Always respond in English only, regardless of the language of the question or any names, terms, or values in the data."""


def answer_question(question: str, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
    """
    Answers a natural-language query regarding the audit trail using grounded context + Gemini.
    Returns:
      {
        "answer": str,
        "grounded_record_count": int,
        "context_used": dict
      }
    """
    clean_question = question.strip()
    if not clean_question:
        return {
            "answer": "Please provide a valid question regarding the audit trail or a specific payment ID.",
            "grounded_record_count": 0,
            "context_used": {},
        }

    # 1. Deterministic retrieval
    context = build_context(clean_question, df)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "answer": "Error: GEMINI_API_KEY environment variable is not configured. Please add your key to .env.",
            "grounded_record_count": context.get("grounded_record_count", 0),
            "context_used": context,
        }

    # 2. Build LLM prompt with strict isolation
    prompt_text = (
        f"{SYSTEM_PROMPT}\n\n"
        f"--- GROUNDED AUDIT CONTEXT (JSON) ---\n"
        f"{json.dumps(context, indent=2, default=str)}\n"
        f"--- END CONTEXT ---\n\n"
        f"USER QUESTION: {clean_question}\n\n"
        f"EXPLANATION (concise, factual, strictly grounded in the JSON context):"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": 2048,
            "temperature": 0.1,
        }
    }

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key,
    }

    last_error = ""
    for model_name in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            if response.status_code == 200:
                res_data = response.json()
                candidates = res_data.get("candidates", [])
                if candidates and "content" in candidates[0] and "parts" in candidates[0]["content"]:
                    generated_text = candidates[0]["content"]["parts"][0].get("text", "").strip()
                    return {
                        "answer": generated_text,
                        "grounded_record_count": context.get("grounded_record_count", 0),
                        "context_used": context,
                        "model_used": model_name,
                    }
            elif response.status_code in (429, 503, 404):
                last_error = f"Model {model_name} returned status {response.status_code}"
                continue
            else:
                last_error = f"Gemini API returned status code {response.status_code}: {response.text}"
        except Exception as e:
            last_error = str(e)
            continue

    return {
        "answer": f"Error contacting explanation engine ({last_error}).",
        "grounded_record_count": context.get("grounded_record_count", 0),
        "context_used": context,
    }


if __name__ == "__main__":
    import sys
    test_q = sys.argv[1] if len(sys.argv) > 1 else "How many payments were escalated to human review?"
    print(f"Question: {test_q}")
    res = answer_question(test_q)
    print(f"\nAnswer:\n{res['answer']}")
    print(f"\nGrounded Records: {res['grounded_record_count']}")
