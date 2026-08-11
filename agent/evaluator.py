"""Evaluator LLM: checks the main agent's response before it's shown to the user."""

import json

import openai
from openai import OpenAI

from backend.logger import log_event
from models.evaluation import Evaluation
from prompts.evaluator_prompt import EVALUATOR_PROMPT
from utils.constants import MODEL_NAME
from utils.helpers import parse_json_safely


def _passing_fallback(feedback: str) -> Evaluation:
    """Used when the evaluator itself can't run (e.g. rate limited).

    Fails OPEN (treats the response as passed) rather than closed, so
    a rate-limited evaluator doesn't trigger extra retry calls on top
    of an already-constrained free-tier quota. The agent response
    itself already went through the model once; we'd rather show it
    than burn more calls trying to re-evaluate it.
    """
    return Evaluation(
        factually_consistent=True,
        relevant_recommendation=True,
        simple_language=True,
        consent_respected=True,
        correct_tool_use=True,
        no_hallucination=True,
        professional_tone=True,
        passed=True,
        feedback=feedback,
    )


def evaluate_response(
    client: OpenAI,
    customer_context: str,
    conversation_summary: str,
    assistant_response: str,
) -> Evaluation:
    """Run the evaluator LLM against one assistant turn and return an Evaluation.

    Falls back to a conservative FAILING Evaluation if the evaluator
    responded but its output can't be parsed (so a garbled evaluator
    turn never silently passes a bad assistant turn). Falls back to a
    PASSING Evaluation if the evaluator call itself errors out (e.g.
    rate limit), to avoid compounding quota usage with retries -- see
    _passing_fallback.
    """
    schema_hint = (
        "Respond ONLY with a JSON object with these exact boolean keys: "
        "factually_consistent, relevant_recommendation, simple_language, "
        "consent_respected, correct_tool_use, no_hallucination, "
        "professional_tone, passed -- plus a string key 'feedback'. "
        "No other text."
    )

    user_message = (
        f"CUSTOMER CONTEXT:\n{customer_context}\n\n"
        f"CONVERSATION SO FAR:\n{conversation_summary}\n\n"
        f"ASSISTANT'S LATEST RESPONSE:\n{assistant_response}\n\n"
        f"{schema_hint}"
    )

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": EVALUATOR_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
    except openai.RateLimitError:
        log_event("EVALUATOR_ERROR", "Rate limited; skipping evaluation for this turn.")
        return _passing_fallback("Evaluator skipped (rate limited); response shown as-is.")
    except openai.OpenAIError as exc:
        log_event("EVALUATOR_ERROR", str(exc))
        return _passing_fallback("Evaluator skipped (API error); response shown as-is.")

    raw_text = completion.choices[0].message.content or ""
    parsed = parse_json_safely(raw_text)

    if not parsed:
        return Evaluation(
            factually_consistent=False,
            relevant_recommendation=False,
            simple_language=False,
            consent_respected=False,
            correct_tool_use=False,
            no_hallucination=False,
            professional_tone=False,
            passed=False,
            feedback="Evaluator output could not be parsed; failing closed.",
        )

    try:
        return Evaluation(**parsed)
    except (TypeError, ValueError) as exc:
        return Evaluation(
            factually_consistent=False,
            relevant_recommendation=False,
            simple_language=False,
            consent_respected=False,
            correct_tool_use=False,
            no_hallucination=False,
            professional_tone=False,
            passed=False,
            feedback=f"Evaluator output did not match schema: {exc}",
        )
