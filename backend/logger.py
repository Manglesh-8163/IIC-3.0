"""Simple event logging for demo/debug purposes."""

import datetime


def log_event(event_type: str, details: str) -> None:
    """Print a timestamped event line to stdout.

    Kept intentionally simple for the MVP -- no external logging
    infra, just readable console output during the demo.
    """
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {event_type}: {details}")
