"""Mock activation functions.

Simulates activating a digital banking feature for a customer. No real
backend exists in this prototype -- these functions just validate
inputs and return a structured result of the locked shape:
    {"status": "success", "feature": "...", "message": "..."}
"""

from backend.data_loader import update_customer_feature_flag
from utils.constants import FEATURE_FIELD_MAP, KNOWN_FEATURES


def activate_feature(customer_name: str, feature: str, consent_given: bool) -> dict:
    """Activate a feature for a customer, but only with explicit consent.

    Never activates without consent_given=True -- this mirrors the
    system prompt's hard rule against assumed consent.

    On success, persists the change to data/customer.txt (via
    backend.data_loader.update_customer_feature_flag) so the activation
    is reflected the next time the customer's profile is read -- e.g.
    by the Gradio context box or a future trigger-engine check.
    """
    if feature not in KNOWN_FEATURES:
        return {
            "status": "error",
            "feature": feature,
            "message": f"Unknown feature '{feature}'. Cannot activate.",
        }

    if not consent_given:
        return {
            "status": "error",
            "feature": feature,
            "message": "Activation requires explicit customer consent, which was not given.",
        }

    field = FEATURE_FIELD_MAP.get(feature)
    if field:
        updated = update_customer_feature_flag(customer_name, field, True)
        if not updated:
            return {
                "status": "error",
                "feature": feature,
                "message": (
                    f"Could not find customer '{customer_name}' to activate "
                    f"{feature}."
                ),
            }

    return {
        "status": "success",
        "feature": feature,
        "message": f"{feature} has been activated for {customer_name}.",
    }
