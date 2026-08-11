"""Gradio UI for the Adoption Copilot demo."""

import gradio as gr

from agent.rerun import run_agent_turn_with_evaluation
from backend.data_loader import get_customer_by_name, load_customers
from utils.llm import get_llm_client

CUSTOM_CSS = """
.adoption-header { text-align: center; margin-bottom: 0.5rem; }
.adoption-sub { text-align: center; color: #6b7280; margin-bottom: 1rem; }
"""


def _build_customer_context(customer_name: str) -> str:
    customer = get_customer_by_name(customer_name)
    if not customer:
        return "No customer selected."
    return (
        f"Name: {customer.name}\n"
        f"Age: {customer.age}\n"
        f"Preferred Language: {customer.preferred_language}\n"
        f"Occupation: {customer.occupation}\n"
        f"Salary Account: {'Yes' if customer.salary_account else 'No'}\n"
        f"UPI Enabled: {'Yes' if customer.upi_enabled else 'No'}\n"
        f"AutoPay Enabled: {'Yes' if customer.autopay_enabled else 'No'}\n"
        f"SIP Active: {'Yes' if customer.sip_active else 'No'}\n"
        f"Insurance AutoPay: {'Yes' if customer.insurance_autopay else 'No'}\n"
    )


def _kickoff_greeting(customer_name: str) -> list[dict]:
    """Seed the chat with a customer-selection system note so the agent has context."""
    return [
        {
            "role": "user",
            "content": (
                f"[System note: You are now speaking with {customer_name}. "
                "Greet them by name, briefly and warmly, in your own words."
            ),
        }
    ]


def start_session(customer_name: str):
    """Called when a customer is picked from the dropdown."""
    client = get_llm_client()
    seed_history = _kickoff_greeting(customer_name)
    context = _build_customer_context(customer_name)

    updated_history, response_text = run_agent_turn_with_evaluation(
        client=client,
        chat_history=seed_history,
        customer_context=context,
    )

    display_history = [{"role": "assistant", "content": response_text}]
    return display_history, updated_history, context


def send_message(user_message: str, display_history, full_history, customer_name):
    """Called when the customer sends a chat message."""
    if not customer_name:
        display_history = display_history or []
        display_history.append(
            {"role": "assistant", "content": "Please select a customer to begin."}
        )
        return "", display_history, full_history, _build_customer_context(customer_name)

    client = get_llm_client()
    full_history = (full_history or []) + [{"role": "user", "content": user_message}]
    context = _build_customer_context(customer_name)

    updated_history, response_text = run_agent_turn_with_evaluation(
        client=client,
        chat_history=full_history,
        customer_context=context,
    )

    display_history = (display_history or []) + [
        {"role": "user", "content": user_message},
        {"role": "assistant", "content": response_text},
    ]

    # Rebuild context AFTER the turn: if the agent just activated a
    # feature (e.g. SIP), data_loader now reads the updated
    # customer.txt, so this reflects it immediately in the sidebar.
    refreshed_context = _build_customer_context(customer_name)
    return "", display_history, updated_history, refreshed_context


def launch_interface() -> None:
    """Build and launch the Gradio app. Contains no business logic itself."""
    customer_names = [c.name for c in load_customers()]

    with gr.Blocks(title="Adoption Copilot") as demo:
        gr.Markdown("## 🏦 Adoption Copilot", elem_classes=["adoption-header"])
        gr.Markdown(
            "Agentic AI for context-aware, hyper-personalized digital banking adoption.",
            elem_classes=["adoption-sub"],
        )

        full_history_state = gr.State([])

        with gr.Row():
            with gr.Column(scale=1):
                customer_dropdown = gr.Dropdown(
                    choices=customer_names,
                    label="Select a customer",
                    value=None,
                )
                context_box = gr.Textbox(
                    label="Customer Context (read-only)",
                    lines=10,
                    interactive=False,
                )

            with gr.Column(scale=2):
                chatbot = gr.Chatbot(label="Adoption Copilot", height=450)
                msg_box = gr.Textbox(
                    label="Your message",
                    placeholder="Type your reply and press Enter...",
                )

        customer_dropdown.change(
            fn=start_session,
            inputs=[customer_dropdown],
            outputs=[chatbot, full_history_state, context_box],
        )

        msg_box.submit(
            fn=send_message,
            inputs=[msg_box, chatbot, full_history_state, customer_dropdown],
            outputs=[msg_box, chatbot, full_history_state, context_box],
        )

    demo.launch()
