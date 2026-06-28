from app.agent import DISCOUNT_CODES, redeem_discount_code


def test_redeem_discount_code_validation() -> None:
    # Reset in-memory state before testing
    DISCOUNT_CODES["WELCOME50"] = {"claimed": False, "user_id": None}
    DISCOUNT_CODES["SUMMER20"] = {"claimed": False, "user_id": None}

    # Test missing/empty user ID
    res = redeem_discount_code("", "WELCOME50")
    assert "Error: A registered user ID is required" in res

    # Test invalid code
    res = redeem_discount_code("user123", "INVALIDCODE")
    assert "Error: Discount code 'INVALIDCODE' is invalid" in res

    # Test successful redemption
    res = redeem_discount_code("user123", "WELCOME50")
    assert (
        "Success: Discount code 'WELCOME50' has been successfully redeemed for user 'user123'"
        in res
    )
    assert DISCOUNT_CODES["WELCOME50"]["claimed"] is True
    assert DISCOUNT_CODES["WELCOME50"]["user_id"] == "user123"

    # Test double redemption (single-use constraint)
    res2 = redeem_discount_code("user456", "WELCOME50")
    assert "Error: Discount code 'WELCOME50' has already been redeemed" in res2
