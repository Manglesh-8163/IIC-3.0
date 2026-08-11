"""Global constants for the Adoption Copilot project."""

# --- Model / API ---
# Google AI Studio exposes an OpenAI-compatible endpoint, so we keep
# using the `openai` SDK -- just pointed at Google instead of OpenRouter.
GOOGLE_AI_STUDIO_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
MODEL_NAME = "gemini-3.5-flash-lite"

# --- Retry / evaluation loop ---
MAX_RETRIES = 2

# --- File paths ---
DATA_DIR = "data"
CUSTOMER_FILE = f"{DATA_DIR}/customer.txt"
TRANSACTIONS_FILE = f"{DATA_DIR}/transactions.txt"
FEATURES_FILE = f"{DATA_DIR}/banking_features.txt"

# --- Record separator used in all .txt data files ---
RECORD_SEPARATOR = "==="

# --- Supported digital features (must match banking_features.txt) ---
FEATURE_AUTOPAY = "AutoPay"
FEATURE_SIP = "SIP (Systematic Investment Plan)"
FEATURE_INSURANCE_AUTOPAY = "Insurance AutoPay"
FEATURE_UPI_AUTOPAY = "UPI AutoPay"

KNOWN_FEATURES = [
    FEATURE_AUTOPAY,
    FEATURE_SIP,
    FEATURE_INSURANCE_AUTOPAY,
    FEATURE_UPI_AUTOPAY,
]

# --- Maps a feature name to the Customer boolean field it toggles on ---
# Used by backend.activation to persist a successful activation back to
# data/customer.txt via backend.data_loader.
FEATURE_FIELD_MAP = {
    FEATURE_AUTOPAY: "autopay_enabled",
    FEATURE_SIP: "sip_active",
    FEATURE_INSURANCE_AUTOPAY: "insurance_autopay",
    FEATURE_UPI_AUTOPAY: "upi_autopay_enabled",
}
