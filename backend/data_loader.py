"""Loads and parses the mock .txt data files.

Per the project contract, this is the ONLY module that reads the data
files directly. Everything else consumes the parsed structures below.
"""

from models.customer import Customer, Transaction
from utils.constants import CUSTOMER_FILE, FEATURES_FILE, RECORD_SEPARATOR, TRANSACTIONS_FILE


def _yes_no_to_bool(value: str) -> bool:
    return value.strip().lower() == "yes"


def _parse_customer_block(block: str) -> Customer | None:
    fields: dict[str, str] = {}
    for line in block.strip().splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip()

    if "Customer Name" not in fields:
        return None

    return Customer(
        name=fields.get("Customer Name", ""),
        age=int(fields.get("Age", 0) or 0),
        preferred_language=fields.get("Preferred Language", ""),
        occupation=fields.get("Occupation", ""),
        salary_account=_yes_no_to_bool(fields.get("Salary Account", "No")),
        upi_enabled=_yes_no_to_bool(fields.get("UPI Enabled", "No")),
        autopay_enabled=_yes_no_to_bool(fields.get("AutoPay Enabled", "No")),
        sip_active=_yes_no_to_bool(fields.get("SIP Active", "No")),
        insurance_autopay=_yes_no_to_bool(fields.get("Insurance AutoPay", "No")),
        upi_autopay_enabled=_yes_no_to_bool(fields.get("UPI AutoPay", "No")),
    )


def load_customers() -> list[Customer]:
    """Parse data/customer.txt into a list of Customer objects."""
    with open(CUSTOMER_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = [b for b in content.split(RECORD_SEPARATOR) if b.strip()]
    customers = []
    for block in blocks:
        customer = _parse_customer_block(block)
        if customer:
            customers.append(customer)
    return customers


def get_customer_by_name(name: str) -> Customer | None:
    """Convenience lookup for a single customer by (case-insensitive) name."""
    for customer in load_customers():
        if customer.name.lower() == name.lower():
            return customer
    return None


def _bool_to_yes_no(value: bool) -> str:
    return "Yes" if value else "No"


def _serialize_customer_block(customer: Customer) -> str:
    """Render a Customer back into the same field format used in customer.txt."""
    return (
        f"Customer Name: {customer.name}\n"
        f"Age: {customer.age}\n"
        f"Preferred Language: {customer.preferred_language}\n"
        f"Occupation: {customer.occupation}\n"
        f"Salary Account: {_bool_to_yes_no(customer.salary_account)}\n"
        f"UPI Enabled: {_bool_to_yes_no(customer.upi_enabled)}\n"
        f"AutoPay Enabled: {_bool_to_yes_no(customer.autopay_enabled)}\n"
        f"SIP Active: {_bool_to_yes_no(customer.sip_active)}\n"
        f"Insurance AutoPay: {_bool_to_yes_no(customer.insurance_autopay)}\n"
        f"UPI AutoPay: {_bool_to_yes_no(customer.upi_autopay_enabled)}"
    )


def save_customers(customers: list[Customer]) -> None:
    """Write a full list of Customer objects back to data/customer.txt.

    Per the project contract, this (alongside load_customers) is the
    only place that writes the customer data file directly.
    """
    blocks = [_serialize_customer_block(c) for c in customers]
    content = f"\n\n{RECORD_SEPARATOR}\n\n".join(blocks) + "\n"
    with open(CUSTOMER_FILE, "w", encoding="utf-8") as f:
        f.write(content)


def update_customer_feature_flag(name: str, field: str, value: bool) -> bool:
    """Set one boolean feature field on a customer and persist it to disk.

    Returns True if the customer was found and updated, False otherwise.
    This is how a successful activation (see backend.activation) gets
    reflected back into data/customer.txt, so subsequent reads (e.g. the
    Gradio context box, or a future trigger-engine check) see the change.
    """
    customers = load_customers()
    updated = False
    for customer in customers:
        if customer.name.lower() == name.lower():
            setattr(customer, field, value)
            updated = True
            break

    if updated:
        save_customers(customers)
    return updated


def load_transactions() -> dict[str, list[Transaction]]:
    """Parse data/transactions.txt into {customer_name: [Transaction, ...]}."""
    with open(TRANSACTIONS_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = [b for b in content.split(RECORD_SEPARATOR) if b.strip()]
    result: dict[str, list[Transaction]] = {}

    for block in blocks:
        lines = [line.strip() for line in block.strip().splitlines() if line.strip()]
        if not lines:
            continue

        customer_name = None
        transactions: list[Transaction] = []
        current: dict[str, str] = {}

        for line in lines:
            if line.startswith("Customer Name:"):
                customer_name = line.split(":", 1)[1].strip()
                continue
            if ":" not in line:
                continue
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip()
            current[key] = value

            if key == "PAYMENT_METHOD":
                transactions.append(
                    Transaction(
                        date=current.get("DATE", ""),
                        description=current.get("DESCRIPTION", ""),
                        amount=float(current.get("AMOUNT", 0) or 0),
                        payment_method=current.get("PAYMENT_METHOD", ""),
                    )
                )
                current = {}

        if customer_name:
            result[customer_name] = transactions

    return result


def get_transactions_for_customer(name: str) -> list[Transaction]:
    """Convenience lookup for one customer's transactions by name."""
    all_transactions = load_transactions()
    for customer_name, transactions in all_transactions.items():
        if customer_name.lower() == name.lower():
            return transactions
    return []


def load_feature_knowledge_base() -> dict[str, dict[str, str]]:
    """Parse data/banking_features.txt into {feature_name: {field: text}}."""
    with open(FEATURES_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = [b for b in content.split(RECORD_SEPARATOR) if b.strip()]
    features: dict[str, dict[str, str]] = {}

    for block in blocks:
        block = block.strip()
        if not block.startswith("Feature:"):
            continue

        lines = block.splitlines()
        feature_name = lines[0].split(":", 1)[1].strip()

        rest = "\n".join(lines[1:]).strip()
        sections: dict[str, str] = {}
        current_key = None
        current_lines: list[str] = []

        known_headers = [
            "Simple Explanation",
            "Benefits",
            "Eligibility",
            "Activation Requirement",
        ]

        for line in rest.splitlines():
            stripped = line.strip()
            matched_header = next(
                (h for h in known_headers if stripped.startswith(f"{h}:")), None
            )
            if matched_header:
                if current_key:
                    sections[current_key] = "\n".join(current_lines).strip()
                current_key = matched_header
                current_lines = [stripped.split(":", 1)[1].strip()]
            elif current_key:
                current_lines.append(stripped)

        if current_key:
            sections[current_key] = "\n".join(current_lines).strip()

        features[feature_name] = sections

    return features
