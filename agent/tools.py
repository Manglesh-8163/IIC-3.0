"""Tool functions and their schemas for LLM tool-calling.

Per the project contract: tools start with verbs and return
dictionaries in fixed shapes.
"""

from backend.activation import activate_feature
from backend.data_loader import (
    get_customer_by_name,
    get_transactions_for_customer,
    load_feature_knowledge_base,
)
from backend.trigger_engine import detect_opportunity


def detect_opportunity_for_customer(customer_name: str) -> dict:
    """Look up a customer and their transactions, then run the trigger engine."""
    customer = get_customer_by_name(customer_name)
    if not customer:
        return {
            "detected": False,
            "feature": "",
            "reason": f"No customer found named '{customer_name}'.",
        }
    transactions = get_transactions_for_customer(customer_name)
    return detect_opportunity(customer, transactions)


def get_feature_details(feature_name: str) -> dict:
    """Return knowledge-base details for a given feature name."""
    kb = load_feature_knowledge_base()
    details = kb.get(feature_name)
    if not details:
        return {"found": False, "feature": feature_name, "details": {}}
    return {"found": True, "feature": feature_name, "details": details}


def get_customer_profile(customer_name: str) -> dict:
    """Return a customer's profile as a plain dict, or an empty dict if not found."""
    customer = get_customer_by_name(customer_name)
    if not customer:
        return {"found": False, "customer": {}}
    return {"found": True, "customer": customer.model_dump()}


def activate_customer_feature(customer_name: str, feature: str, consent_given: bool) -> dict:
    """Activate a feature for a customer. Wraps backend.activation.activate_feature."""
    return activate_feature(customer_name, feature, consent_given)


# --- OpenAI-style tool schemas for the LLM ---

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "detect_opportunity_for_customer",
            "description": (
                "Detect the most relevant digital adoption opportunity for a "
                "customer based on their profile and transaction history."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Full name of the customer.",
                    }
                },
                "required": ["customer_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_feature_details",
            "description": (
                "Get plain-language details (explanation, benefits, eligibility) "
                "for a digital banking feature."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "feature_name": {
                        "type": "string",
                        "description": (
                            "One of: AutoPay, SIP (Systematic Investment Plan), "
                            "Insurance AutoPay, UPI AutoPay."
                        ),
                    }
                },
                "required": ["feature_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_customer_profile",
            "description": "Get a customer's stored profile information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Full name of the customer.",
                    }
                },
                "required": ["customer_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "activate_customer_feature",
            "description": (
                "Activate a digital feature for a customer. Only call this "
                "AFTER the customer has explicitly given consent in the "
                "conversation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Full name of the customer.",
                    },
                    "feature": {
                        "type": "string",
                        "description": (
                            "One of: AutoPay, SIP (Systematic Investment Plan), "
                            "Insurance AutoPay, UPI AutoPay."
                        ),
                    },
                    "consent_given": {
                        "type": "boolean",
                        "description": "True only if the customer explicitly consented.",
                    },
                },
                "required": ["customer_name", "feature", "consent_given"],
            },
        },
    },
]
