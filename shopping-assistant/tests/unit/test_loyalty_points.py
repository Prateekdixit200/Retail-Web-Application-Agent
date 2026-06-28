from app.agent import LOYALTY_ACCOUNTS, award_loyalty_points


def _reset_loyalty_accounts() -> None:
    """Clear the in-memory loyalty ledger before each test."""
    LOYALTY_ACCOUNTS.clear()


def test_award_points_success() -> None:
    _reset_loyalty_accounts()
    res = award_loyalty_points("user100", 75.0, "txn-001")
    assert "Success" in res
    assert "75 loyalty points" in res
    assert LOYALTY_ACCOUNTS["user100"]["points"] == 75
    assert len(LOYALTY_ACCOUNTS["user100"]["transactions"]) == 1


def test_award_points_capped() -> None:
    _reset_loyalty_accounts()
    res = award_loyalty_points("user200", 9999.99, "txn-002")
    assert "Success" in res
    assert "500 loyalty points" in res
    assert LOYALTY_ACCOUNTS["user200"]["points"] == 500


def test_award_points_duplicate_txn() -> None:
    _reset_loyalty_accounts()
    award_loyalty_points("user300", 50.0, "txn-003")
    res2 = award_loyalty_points("user300", 50.0, "txn-003")
    assert "Error" in res2
    assert "already been processed" in res2
    # Balance should still be 50 (not 100)
    assert LOYALTY_ACCOUNTS["user300"]["points"] == 50


def test_award_points_blank_user_id() -> None:
    _reset_loyalty_accounts()
    res = award_loyalty_points("   ", 10.0, "txn-004")
    assert "Error" in res


def test_award_points_negative_amount() -> None:
    _reset_loyalty_accounts()
    res = award_loyalty_points("user400", -50.0, "txn-005")
    assert "Error" in res


def test_award_points_blank_transaction_id() -> None:
    _reset_loyalty_accounts()
    res = award_loyalty_points("user500", 20.0, "   ")
    assert "Error" in res


def test_award_points_accumulation() -> None:
    _reset_loyalty_accounts()
    award_loyalty_points("user600", 100.0, "txn-a")
    award_loyalty_points("user600", 200.0, "txn-b")
    award_loyalty_points("user600", 50.0, "txn-c")
    assert LOYALTY_ACCOUNTS["user600"]["points"] == 350
    assert len(LOYALTY_ACCOUNTS["user600"]["transactions"]) == 3
