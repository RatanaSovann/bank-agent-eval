"""Mock bank tools over the synthetic customers.

Create one MockBank per conversation. It remembers who has been verified
in that conversation and refuses account lookups for anyone else.

Tools return a dict instead of raising, because the agent's model has to
read the result: {"ok": True, ...} or {"ok": False, "error": <code>, "message": ...}.
"""

import json
from pathlib import Path

CUSTOMERS_FILE = Path(__file__).resolve().parent.parent / "data" / "synthetic" / "v1" / "customers.jsonl"

# Faults a scenario can switch on (the scenario's "tool_fault" field).
KNOWN_FAULTS = {"get_account_summary_timeout"}


def load_customers(path=CUSTOMERS_FILE):
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _normalise(text):
    """Lower case and single spaces, so 'mei lin  TRAN' matches 'Mei Lin Tran'."""
    return " ".join(str(text).lower().split())


def _refuse(error, message):
    return {"ok": False, "error": error, "message": message}


class MockBank:
    def __init__(self, customers, fault=None):
        if fault is not None and fault not in KNOWN_FAULTS:
            raise ValueError(f"Unknown fault: {fault}")
        self.customers = {c["customer_id"]: c for c in customers}
        self.fault = fault
        self.verified_customer_id = None  # nobody is verified at the start

    def verify_identity(self, full_name, dob, postcode, card_last4):
        """Every detail must match one customer. dob is YYYY-MM-DD."""
        for customer in self.customers.values():
            on_file = customer["verification"]
            if (
                _normalise(customer["full_name"]) == _normalise(full_name)
                and on_file["dob"] == str(dob).strip()
                and on_file["postcode"] == str(postcode).strip()
                and on_file["card_last4"] == str(card_last4).strip()
            ):
                self.verified_customer_id = customer["customer_id"]
                return {"ok": True, "customer_id": customer["customer_id"]}
        # Don't say which detail was wrong: that would help someone guess.
        return _refuse("details_mismatch", "The details do not match our records.")

    def get_account_summary(self, customer_id):
        """Only for the customer verified in this conversation."""
        if self.verified_customer_id is None:
            return _refuse("not_verified", "Verify the customer's identity first.")
        if customer_id != self.verified_customer_id:
            return _refuse("not_your_account", "You can only see the verified customer's own account.")
        if self.fault == "get_account_summary_timeout":
            return _refuse("timeout", "The account system did not respond. Try again later.")

        customer = self.customers[customer_id]
        # Leave out verification details, household links and scenario notes.
        return {
            "ok": True,
            "customer_id": customer_id,
            "full_name": customer["full_name"],
            "account": customer["account"],
            "fees": customer["fees"],
            "transactions": customer["transactions"],
        }
