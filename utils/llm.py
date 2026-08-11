"""LLM client initialization.

Per the project contract, the LLM client is initialized only here.
We use Google AI Studio as the provider, via its OpenAI-compatible
endpoint (so we can keep using the `openai` SDK unchanged), calling
gemini-3.5-flash-lite.
"""

import os

from openai import OpenAI

from utils.constants import GOOGLE_AI_STUDIO_BASE_URL, MODEL_NAME


def get_llm_client() -> OpenAI:
    """Return an OpenAI-compatible client configured for Google AI Studio."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to your .env file."
        )
    return OpenAI(base_url=GOOGLE_AI_STUDIO_BASE_URL, api_key=api_key)


def call_llm(client: OpenAI, messages: list[dict], tools: list[dict] | None = None):
    """Call the configured LLM with chat messages and optional tool schemas."""
    kwargs = {"model": MODEL_NAME, "messages": messages}
    if tools:
        kwargs["tools"] = tools
    return client.chat.completions.create(**kwargs)
