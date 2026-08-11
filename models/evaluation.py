"""Pydantic model for structured evaluator LLM output."""

from pydantic import BaseModel, Field


class Evaluation(BaseModel):
    """Structured verdict from the evaluator LLM on one assistant turn."""

    factually_consistent: bool = Field(
        description="Response does not contradict known customer data."
    )
    relevant_recommendation: bool = Field(
        description="Any feature recommended is actually relevant to this customer."
    )
    simple_language: bool = Field(
        description="Response avoids financial jargon and is easy to understand."
    )
    consent_respected: bool = Field(
        description="No activation happened without explicit customer consent."
    )
    correct_tool_use: bool = Field(
        description="Tools were called correctly and only when appropriate."
    )
    no_hallucination: bool = Field(
        description="Response does not invent customer facts or features."
    )
    professional_tone: bool = Field(
        description="Response is professional, trustworthy, and non-pushy."
    )
    passed: bool = Field(description="Overall pass/fail verdict.")
    feedback: str = Field(
        default="", description="Short note on what to fix if passed is False."
    )
