"""Main agent conversation loop with tool calling.

Given the current chat history, calls the LLM, executes any tool
calls it requests, feeds results back, and repeats until the model
produces a plain-text response.
"""

import time

import openai
from openai import OpenAI

from agent.tool_handler import handle_tool_call
from agent.tools import TOOL_SCHEMAS
from backend.logger import log_event
from prompts.system_prompt import SYSTEM_PROMPT
from utils.constants import MODEL_NAME

MAX_TOOL_ITERATIONS = 5
LLM_CALL_RETRIES = 3
LLM_CALL_BACKOFF_SECONDS = 3


def _call_llm_with_retry(client: OpenAI, messages: list[dict], tools: list[dict]):
    """Call the chat completion endpoint, retrying on transient errors.

    Rate limits (429) and momentary server/connection errors are common
    on free-tier model pools. Retries with a short backoff before
    giving up, rather than crashing the whole conversation turn.
    """
    last_error = None
    for attempt in range(1, LLM_CALL_RETRIES + 1):
        try:
            return client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                tools=tools,
            )
        except (openai.RateLimitError, openai.APIConnectionError, openai.InternalServerError) as exc:
            last_error = exc
            log_event(
                "LLM_RETRY",
                f"attempt={attempt} error={type(exc).__name__}: {exc}",
            )
            if attempt < LLM_CALL_RETRIES:
                time.sleep(LLM_CALL_BACKOFF_SECONDS * attempt)
    raise last_error


def _to_message_dict(message) -> dict:
    """Convert an OpenAI SDK message object into a plain dict for the next call.

    Gemini 3.x "thinking" models attach a `thought_signature` to each tool
    call (returned in a non-standard `extra_content.google.thought_signature`
    field alongside `id`/`type`/`function`). Gemini requires that signature
    to be echoed back verbatim on the next turn -- if it's dropped, the API
    rejects the request with a 400 "missing thought_signature" error. So we
    must round-trip `extra_content` here, not just the standard OpenAI
    fields.
    """
    msg: dict = {"role": message.role, "content": message.content or ""}
    if getattr(message, "tool_calls", None):
        tool_calls = []
        for tc in message.tool_calls:
            tc_dict = {
                "id": tc.id,
                "type": tc.type,
                "function": {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                },
            }
            extra_content = getattr(tc, "extra_content", None)
            if extra_content is None:
                # Some openai SDK versions surface unrecognized fields via
                # model_extra instead of as a direct attribute.
                extra_content = (getattr(tc, "model_extra", None) or {}).get(
                    "extra_content"
                )
            if extra_content is not None:
                tc_dict["extra_content"] = (
                    extra_content.model_dump()
                    if hasattr(extra_content, "model_dump")
                    else extra_content
                )
            tool_calls.append(tc_dict)
        msg["tool_calls"] = tool_calls
    return msg


def generate_agent_response(client: OpenAI, chat_history: list[dict]) -> tuple[list[dict], str]:
    """Run one full agent turn (including any tool-call round-trips).

    chat_history is a list of {"role": ..., "content": ...} dicts NOT
    including the system prompt. Returns (updated_history, final_text)
    where updated_history includes any tool-call messages generated,
    and final_text is the assistant's plain-text reply to show the user.

    If the LLM is unreachable/rate-limited even after retries, returns
    a friendly in-chat error message instead of raising, so the Gradio
    UI never crashes mid-demo.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history

    for _ in range(MAX_TOOL_ITERATIONS):
        try:
            completion = _call_llm_with_retry(client, messages, TOOL_SCHEMAS)
        except openai.RateLimitError:
            error_text = (
                "The AI model is temporarily rate-limited (free tier is busy "
                "right now). Please wait a moment and try again."
            )
            messages.append({"role": "assistant", "content": error_text})
            return messages[1:], error_text
        except openai.OpenAIError as exc:
            log_event("LLM_ERROR", f"{type(exc).__name__}: {exc}")
            error_text = (
                "I couldn't reach the AI model just now. Please try again "
                "in a moment."
            )
            messages.append({"role": "assistant", "content": error_text})
            return messages[1:], error_text

        message = completion.choices[0].message

        if message.tool_calls:
            messages.append(_to_message_dict(message))
            for tool_call in message.tool_calls:
                result = handle_tool_call(tool_call)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_call.function.name,
                        "content": str(result),
                    }
                )
            continue

        final_text = message.content or ""
        messages.append({"role": "assistant", "content": final_text})
        # Return history minus the leading system prompt.
        return messages[1:], final_text

    # Safety valve: too many tool iterations without a final answer.
    fallback_text = (
        "I'm having trouble completing that request right now. "
        "Could you try rephrasing?"
    )
    messages.append({"role": "assistant", "content": fallback_text})
    return messages[1:], fallback_text

