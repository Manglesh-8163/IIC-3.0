"""Dispatches LLM tool_calls to the actual Python functions in tools.py."""

import json

from agent.tools import (
    activate_customer_feature,
    detect_opportunity_for_customer,
    get_customer_profile,
    get_feature_details,
)
from backend.logger import log_event

TOOL_REGISTRY = {
    "detect_opportunity_for_customer": detect_opportunity_for_customer,
    "get_feature_details": get_feature_details,
    "get_customer_profile": get_customer_profile,
    "activate_customer_feature": activate_customer_feature,
}


def handle_tool_call(tool_call) -> dict:
    """Execute a single tool call object (OpenAI SDK shape) and return its result dict."""
    function_name = tool_call.function.name
    try:
        arguments = json.loads(tool_call.function.arguments or "{}")
    except json.JSONDecodeError:
        arguments = {}

    log_event("TOOL_CALL", f"{function_name}({arguments})")

    handler = TOOL_REGISTRY.get(function_name)
    if not handler:
        result = {"error": f"Unknown tool '{function_name}'."}
    else:
        try:
            result = handler(**arguments)
        except TypeError as exc:
            result = {"error": f"Bad arguments for '{function_name}': {exc}"}

    log_event("TOOL_RESULT", f"{function_name} -> {result}")
    return result
