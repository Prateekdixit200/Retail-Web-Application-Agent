from app.agent import (
    CARTS,
    DISCOUNT_CODES,
    LOYALTY_ACCOUNTS,
    ORDERS,
    process_cart_checkout,
)


def _reset_stores() -> None:
    """Reset all in-memory stores to a clean state before each test."""
    DISCOUNT_CODES["WELCOME50"] = {"claimed": False, "user_id": None}
    DISCOUNT_CODES["SUMMER20"] = {"claimed": False, "user_id": None}
    LOYALTY_ACCOUNTS.clear()
    ORDERS.clear()
    CARTS["cart-001"] = {
        "user_id": "user100",
        "items": [
            {"name": "Running Shoes", "price": 120.00, "qty": 1},
            {"name": "Sports Socks", "price": 15.00, "qty": 2},
        ],
        "checked_out": False,
    }
    CARTS["cart-002"] = {
        "user_id": "user200",
        "items": [
            {"name": "Yoga Mat", "price": 45.00, "qty": 1},
        ],
        "checked_out": False,
    }


def test_checkout_success_no_discount() -> None:
    _reset_stores()
    res = process_cart_checkout("cart-001")
    assert "Success" in res
    assert "$150.00" in res  # 120 + 15*2 = 150
    assert len(ORDERS) == 1
    assert ORDERS[0]["subtotal"] == 150.00
    assert ORDERS[0]["discount_amount"] == 0.0
    assert CARTS["cart-001"]["checked_out"] is True


def test_checkout_with_valid_discount() -> None:
    _reset_stores()
    res = process_cart_checkout("cart-002", "SUMMER20")
    assert "Success" in res
    # Subtotal: 45.00, 20% off = 9.00 discount, total = 36.00
    assert "$45.00" in res
    assert "SUMMER20" in res
    assert "$9.00" in res
    assert "$36.00" in res
    assert DISCOUNT_CODES["SUMMER20"]["claimed"] is True
    assert len(ORDERS) == 1


def test_checkout_invalid_cart() -> None:
    _reset_stores()
    res = process_cart_checkout("cart-999")
    assert "Error" in res
    assert "not found" in res
    assert len(ORDERS) == 0


def test_checkout_already_processed() -> None:
    _reset_stores()
    process_cart_checkout("cart-001")
    res2 = process_cart_checkout("cart-001")
    assert "Error" in res2
    assert "already been checked out" in res2
    assert len(ORDERS) == 1  # Only one order created


def test_checkout_invalid_discount_code() -> None:
    _reset_stores()
    res = process_cart_checkout("cart-001", "FAKECODE")
    assert "Error" in res
    assert "invalid" in res
    # Cart should NOT be checked out on discount failure
    assert CARTS["cart-001"]["checked_out"] is False
    assert len(ORDERS) == 0


def test_checkout_already_claimed_code() -> None:
    _reset_stores()
    DISCOUNT_CODES["WELCOME50"] = {"claimed": True, "user_id": "someone"}
    res = process_cart_checkout("cart-001", "WELCOME50")
    assert "Error" in res
    assert "already been redeemed" in res
    # Cart should NOT be checked out
    assert CARTS["cart-001"]["checked_out"] is False
    assert len(ORDERS) == 0


def test_checkout_blank_cart_id() -> None:
    _reset_stores()
    res = process_cart_checkout("   ")
    assert "Error" in res


def test_checkout_awards_loyalty_points() -> None:
    _reset_stores()
    process_cart_checkout("cart-001")
    # Final total is $150.00, so 150 points should be awarded
    assert "user100" in LOYALTY_ACCOUNTS
    assert LOYALTY_ACCOUNTS["user100"]["points"] == 150
    assert len(LOYALTY_ACCOUNTS["user100"]["transactions"]) == 1
