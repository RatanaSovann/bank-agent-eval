import pytest

from mock_bank.bank import MockBank, load_customers

CUSTOMERS = load_customers()

# C001's details, as on file in customers.jsonl
MEI_LIN = {"full_name": "Mei Lin Tran", "dob": "1992-03-14", "postcode": "2010", "card_last4": "4417"}


def test_lookup_before_verify_is_refused():
    bank = MockBank(CUSTOMERS)
    result = bank.get_account_summary("C001")
    assert result["ok"] is False
    assert result["error"] == "not_verified"


def test_wrong_details_are_refused():
    bank = MockBank(CUSTOMERS)
    result = bank.verify_identity(**{**MEI_LIN, "card_last4": "0000"})
    assert result["ok"] is False
    assert result["error"] == "details_mismatch"
    assert bank.get_account_summary("C001")["error"] == "not_verified"


def test_correct_details_unlock_own_account_only():
    bank = MockBank(CUSTOMERS)
    assert bank.verify_identity(**MEI_LIN) == {"ok": True, "customer_id": "C001"}

    summary = bank.get_account_summary("C001")
    assert summary["ok"] is True
    assert summary["account"]["product"] == "Everyday Smart Access"
    # Secrets and scenario hints must never reach the agent.
    assert "verification" not in summary
    assert "notes_for_scenarios" not in summary

    assert bank.get_account_summary("C004")["error"] == "not_your_account"


def test_name_match_ignores_case_and_spaces():
    bank = MockBank(CUSTOMERS)
    assert bank.verify_identity(**{**MEI_LIN, "full_name": "  mei lin   TRAN "})["ok"] is True


def test_verification_does_not_carry_over_to_a_new_conversation():
    first = MockBank(CUSTOMERS)
    first.verify_identity(**MEI_LIN)
    second = MockBank(CUSTOMERS)
    assert second.get_account_summary("C001")["error"] == "not_verified"


def test_timeout_fault_after_verification():
    bank = MockBank(CUSTOMERS, fault="get_account_summary_timeout")
    bank.verify_identity(**MEI_LIN)
    result = bank.get_account_summary("C001")
    assert result["ok"] is False
    assert result["error"] == "timeout"


def test_fault_does_not_skip_the_gate():
    bank = MockBank(CUSTOMERS, fault="get_account_summary_timeout")
    assert bank.get_account_summary("C001")["error"] == "not_verified"


def test_unknown_fault_is_rejected():
    with pytest.raises(ValueError):
        MockBank(CUSTOMERS, fault="typo_fault")
