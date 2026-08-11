"""Typed representation of a customer record."""

from pydantic import BaseModel


class Customer(BaseModel):
    """A customer profile as parsed from data/customer.txt."""

    name: str
    age: int
    preferred_language: str
    occupation: str
    salary_account: bool
    upi_enabled: bool
    autopay_enabled: bool
    sip_active: bool
    insurance_autopay: bool
    upi_autopay_enabled: bool = False


class Transaction(BaseModel):
    """A single transaction line as parsed from data/transactions.txt."""

    date: str
    description: str
    amount: float
    payment_method: str
