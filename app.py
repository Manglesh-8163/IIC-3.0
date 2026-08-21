from dotenv import load_dotenv

from gradio_ui.interface import launch_interface

load_dotenv()


def main() -> None:
    """Launch the Adoption Copilot application."""
    launch_interface(share=True)


if __name__ == "__main__":
    main()
