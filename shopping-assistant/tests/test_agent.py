# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest
from app.agent import DISCOUNT_CODES, redeem_discount_code

def test_security_redeem_discount_boundaries() -> None:
    """
    Security verification tests for the redeem_discount_code tool.
    Validates boundary conditions, input validation, single-use constraints,
    and information disclosure guardrails.
    """
    # Reset in-memory state before testing
    DISCOUNT_CODES["WELCOME50"] = {"claimed": False, "user_id": None}
    DISCOUNT_CODES["SUMMER20"] = {"claimed": False, "user_id": None}

    # 1. Identity Verification / Spoofing Boundary (Empty/whitespace user ID must be rejected)
    res_empty = redeem_discount_code("", "WELCOME50")
    assert "Error: A registered user ID is required" in res_empty

    res_whitespace = redeem_discount_code("   ", "WELCOME50")
    assert "Error: A registered user ID is required" in res_whitespace

    # 2. Input Sanitization / Tampering Boundary (Invalid codes must be rejected)
    res_invalid = redeem_discount_code("user123", "INVALIDCODE")
    assert "Error: Discount code 'INVALIDCODE' is invalid" in res_invalid

    # Standard clean input trim and uppercase validation
    res_trim = redeem_discount_code("user123", "  summer20  ")
    assert "Success" in res_trim
    assert DISCOUNT_CODES["SUMMER20"]["claimed"] is True
    assert DISCOUNT_CODES["SUMMER20"]["user_id"] == "user123"

    # 3. Double Redemption / Single-use Constraint (Idempotency and tampering check)
    res_first = redeem_discount_code("user123", "WELCOME50")
    assert "Success" in res_first

    # Attempting to claim already redeemed code for a different user must be rejected
    res_second = redeem_discount_code("user456", "WELCOME50")
    assert "Error: Discount code 'WELCOME50' has already been redeemed" in res_second

    # 4. Information Disclosure Guardrail (Ensure redeemer's user ID is not leaked to subsequent callers)
    assert "user123" not in res_second
