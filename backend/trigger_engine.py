"""Rules-based trigger engine.

Detects moments where a customer would benefit from activating a
digital feature, based on their profile and transaction history.
Returns dicts of the locked shape:
    {"detected": bool, "feature": str, "reason": str}
"""

from models.customer import Customer, Transaction
from utils.constants import (
    FEATURE_AUTOPAY,
    FEATURE_INSURANCE_AUTOPAY,
    FEATURE_SIP,
)

# Minimum repeated manual occurrences of a description to count as a pattern.
REPEAT_THRESHOLD = 3


def _count_manual_matches(transactions: list[Transaction], keyword: str) -> int:
    count = 0
    for txn in transactions:
        if keyword.lower() in txn.description.lower() and txn.payment_method.lower() == "manual":
            count += 1
    return count


def _has_recurring_salary(transactions: list[Transaction]) -> bool:
    salary_credits = [
        txn for txn in transactions if "salary" in txn.description.lower()
        and txn.payment_method.lower() == "bank credit"
    ]
    return len(salary_credits) >= REPEAT_THRESHOLD


def detect_opportunity(customer: Customer, transactions: list[Transaction]) -> dict:
    """Detect the single most relevant digital-adoption opportunity, if any.

    Checks features in a fixed priority order and returns the first match.
    If nothing is detected, returns {"detected": False, "feature": "", "reason": "..."}.
    """
    # AutoPay: repeated manual bill payments, feature not yet enabled.
    if not customer.autopay_enabled:
        bill_count = _count_manual_matches(transactions, "bill")
        if bill_count >= REPEAT_THRESHOLD:
            return {
                "detected": True,
                "feature": FEATURE_AUTOPAY,
                "reason": (
                    f"{customer.name} has paid recurring bills manually "
                    f"{bill_count} times in the last few months."
                ),
            }

    # Insurance AutoPay: repeated manual insurance premium payments.
    if not customer.insurance_autopay:
        premium_count = _count_manual_matches(transactions, "insurance")
        if premium_count >= REPEAT_THRESHOLD:
            return {
                "detected": True,
                "feature": FEATURE_INSURANCE_AUTOPAY,
                "reason": (
                    f"{customer.name} has manually paid insurance premiums "
                    f"{premium_count} times recently."
                ),
            }

    # SIP: recurring salary credits with no active SIP.
    if not customer.sip_active and _has_recurring_salary(transactions):
        return {
            "detected": True,
            "feature": FEATURE_SIP,
            "reason": (
                f"{customer.name} receives regular salary credits but has "
                "no active SIP for long-term savings."
            ),
        }

    return {
        "detected": False,
        "feature": "",
        "reason": "No clear digital adoption opportunity detected at this time.",
    }
