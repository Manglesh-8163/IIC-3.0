"""
app.py

Entry point for the Adoption Copilot prototype.

Responsibilities:
- Import the Gradio interface.
- Launch the application.

This file intentionally contains no business logic, AI logic,
tool definitions, or data processing.
"""

from gradio_ui.interface import launch_interface


def main() -> None:
    """Launch the Adoption Copilot application."""
    launch_interface()


if __name__ == "__main__":
    main()