"""Owns all retry logic for the agent+evaluator loop.

Per the project contract, retry logic lives only here.
"""

from openai import OpenAI

from agent.chat import generate_agent_response
from agent.evaluator import evaluate_response
from backend.logger import log_event
from utils.constants import MAX_RETRIES


def _summarize_history(chat_history: list[dict]) -> str:
    lines = []
    for msg in chat_history:
        role = msg.get("role", "")
        if role in ("user", "assistant") and msg.get("content"):
            lines.append(f"{role.upper()}: {msg['content']}")
    return "\n".join(lines[-10:])  # last few turns is enough context


def run_agent_turn_with_evaluation(
    client: OpenAI,
    chat_history: list[dict],
    customer_context: str,
) -> tuple[list[dict], str]:
    """Generate an agent response, evaluate it, and retry on failure.

    Returns (updated_history, final_text_to_show_user). If all retries
    fail evaluation, the last generated response is still returned
    (fails open to the user, but every attempt is logged) so the demo
    never dead-ends.
    """
    attempt = 0
    last_history = chat_history
    last_text = ""

    while attempt <= MAX_RETRIES:
        updated_history, response_text = generate_agent_response(client, last_history)

        evaluation = evaluate_response(
            client=client,
            customer_context=customer_context,
            conversation_summary=_summarize_history(updated_history),
            assistant_response=response_text,
        )

        log_event(
            "EVALUATION",
            f"attempt={attempt} passed={evaluation.passed} feedback={evaluation.feedback}",
        )

        if evaluation.passed:
            return updated_history, response_text

        # Failed: strip the bad assistant turn and retry with feedback
        # injected as a system-style nudge for the next attempt.
        last_history = chat_history + [
            {
                "role": "system",
                "content": (
                    "Your previous draft response failed an internal review: "
                    f"{evaluation.feedback}. Please revise your next response "
                    "to fix this."
                ),
            }
        ]
        last_text = response_text
        attempt += 1

    log_event("EVALUATION", "Max retries reached; returning last attempt as-is.")
    return last_history, last_text
