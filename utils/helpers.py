"""Small shared helper functions."""

import json


def parse_json_safely(text: str) -> dict | None:
    """Try to parse a JSON object out of raw LLM/tool text.

    Strips markdown code fences if present. Returns None on failure
    rather than raising, so callers can decide how to handle bad output.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return None


def format_currency(amount: float) -> str:
    """Format a rupee amount for display, e.g. 1450 -> '₹1,450'."""
    return f"\u20b9{amount:,.0f}"
