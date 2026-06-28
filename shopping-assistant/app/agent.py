# ruff: noqa
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

import datetime
import uuid
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, ValidationError, field_validator

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.genai import types

import os
import google.auth

try:
    _, project_id = google.auth.default()
    if project_id:
        os.environ["GOOGLE_CLOUD_PROJECT"] = project_id
except Exception:
    pass

os.environ["GOOGLE_CLOUD_LOCATION"] = "global"

if os.environ.get("GEMINI_API_KEY"):
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "False"
else:
    os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "True"


# In-memory store for single-use discount codes
# Maps code (uppercase) -> dict containing status and redeemer's user ID
DISCOUNT_CODES = {
    "WELCOME50": {"claimed": False, "user_id": None},
    "SUMMER20": {"claimed": False, "user_id": None},
}

# Discount percentages for known codes
DISCOUNT_PERCENTAGES = {
    "WELCOME50": 50,  # 50% off
    "SUMMER20": 20,  # 20% off
}

# In-memory loyalty points ledger
# Maps user_id -> { "points": int, "transactions": list[dict] }
LOYALTY_ACCOUNTS: dict[str, dict] = {}

# In-memory carts store
# Maps cart_id -> { "user_id": str, "items": list[dict], "checked_out": bool }
CARTS = {
    "cart-001": {
        "user_id": "user100",
        "items": [
            {"name": "Running Shoes", "price": 120.00, "qty": 1},
            {"name": "Sports Socks", "price": 15.00, "qty": 2},
        ],
        "checked_out": False,
    },
    "cart-002": {
        "user_id": "user200",
        "items": [
            {"name": "Yoga Mat", "price": 45.00, "qty": 1},
        ],
        "checked_out": False,
    },
}

# Completed orders ledger
ORDERS: list[dict] = []


class AwardPointsRequest(BaseModel):
    """Pydantic schema for award_loyalty_points tool inputs."""

    user_id: str = Field(..., min_length=1, description="Registered user ID")
    purchase_amount: float = Field(..., gt=0, description="Purchase amount in dollars")
    transaction_id: str = Field(
        ..., min_length=1, description="Unique purchase transaction ID"
    )

    @field_validator("user_id", "transaction_id")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank or whitespace-only")
        return v.strip()


class CheckoutRequest(BaseModel):
    """Pydantic schema for process_cart_checkout tool inputs."""

    cart_id: str = Field(..., min_length=1, description="The cart ID to check out")
    discount_code: str = Field(
        default="", description="Optional discount code to apply"
    )

    @field_validator("cart_id")
    @classmethod
    def cart_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("cart_id must not be blank")
        return v.strip()


def redeem_discount_code(user_id: str, code: str) -> str:
    """Redeems a single-use discount code for a registered user.

    Args:
        user_id: The registered user ID of the customer (required).
        code: The discount code to redeem (e.g., WELCOME50, SUMMER20).

    Returns:
        A message indicating the result of the redemption process.
    """
    if not user_id or not user_id.strip():
        return "Error: A registered user ID is required to redeem a discount code."

    code_clean = code.strip().upper()
    if code_clean not in DISCOUNT_CODES:
        return f"Error: Discount code '{code}' is invalid."

    code_info = DISCOUNT_CODES[code_clean]
    if code_info["claimed"]:
        return f"Error: Discount code '{code_clean}' has already been redeemed."

    code_info["claimed"] = True
    code_info["user_id"] = user_id
    return f"Success: Discount code '{code_clean}' has been successfully redeemed for user '{user_id}'!"


def award_loyalty_points(
    user_id: str, purchase_amount: float, transaction_id: str
) -> str:
    """Awards loyalty points to a user's account after a successful purchase.

    Args:
        user_id: The registered user ID (required).
        purchase_amount: The purchase total in dollars (must be > 0).
        transaction_id: A unique transaction ID for the purchase (required).

    Returns:
        A message confirming the points awarded or describing an error.
    """
    # Validate via Pydantic schema
    try:
        req = AwardPointsRequest(
            user_id=user_id,
            purchase_amount=purchase_amount,
            transaction_id=transaction_id,
        )
    except ValidationError as e:
        return f"Error: Invalid input — {e}"

    # Calculate points: 1 point per dollar spent, capped at 500 per transaction
    MAX_POINTS_PER_TXN = 500
    points = min(int(req.purchase_amount), MAX_POINTS_PER_TXN)

    # Check for duplicate transaction (idempotency guard)
    account = LOYALTY_ACCOUNTS.setdefault(
        req.user_id, {"points": 0, "transactions": []}
    )
    if any(t["transaction_id"] == req.transaction_id for t in account["transactions"]):
        return f"Error: Transaction '{req.transaction_id}' has already been processed."

    # Award points and log the transaction
    account["points"] += points
    account["transactions"].append(
        {
            "transaction_id": req.transaction_id,
            "purchase_amount": req.purchase_amount,
            "points_awarded": points,
        }
    )

    return (
        f"Success: Awarded {points} loyalty points to user '{req.user_id}'. "
        f"New balance: {account['points']} points."
    )


def process_cart_checkout(cart_id: str, discount_code: str = "") -> str:
    """Processes a cart checkout, optionally applying a discount code.

    Args:
        cart_id: The ID of the cart to check out (required).
        discount_code: An optional discount code to apply at checkout.

    Returns:
        A message with the order summary or an error description.
    """
    # Validate via Pydantic schema
    try:
        req = CheckoutRequest(cart_id=cart_id, discount_code=discount_code)
    except ValidationError as e:
        return f"Error: Invalid input \u2014 {e}"

    # Look up the cart
    if req.cart_id not in CARTS:
        return f"Error: Cart '{req.cart_id}' not found."

    cart = CARTS[req.cart_id]

    # Prevent double-checkout (idempotency)
    if cart["checked_out"]:
        return f"Error: Cart '{req.cart_id}' has already been checked out."

    # Calculate subtotal
    subtotal = sum(item["price"] * item["qty"] for item in cart["items"])  # type: ignore

    # Apply discount if provided
    discount_amount = 0.0
    applied_code = None
    if req.discount_code:
        code_upper = req.discount_code.strip().upper()
        if code_upper not in DISCOUNT_CODES:
            return f"Error: Discount code '{req.discount_code}' is invalid."
        code_info = DISCOUNT_CODES[code_upper]
        if code_info["claimed"]:
            return f"Error: Discount code '{code_upper}' has already been redeemed."
        # Consume the discount code
        percentage = DISCOUNT_PERCENTAGES.get(code_upper, 0)
        discount_amount = round(subtotal * percentage / 100, 2)
        code_info["claimed"] = True
        code_info["user_id"] = cart["user_id"]
        applied_code = code_upper

    final_total = round(subtotal - discount_amount, 2)

    # Create order record
    order_id = f"order-{uuid.uuid4().hex[:8]}"
    order = {
        "order_id": order_id,
        "cart_id": req.cart_id,
        "user_id": cart["user_id"],
        "items": cart["items"],
        "subtotal": subtotal,
        "discount_code": applied_code,
        "discount_amount": discount_amount,
        "final_total": final_total,
        "timestamp": datetime.datetime.now(ZoneInfo("UTC")).isoformat(),
    }
    ORDERS.append(order)

    # Mark cart as checked out
    cart["checked_out"] = True

    # Auto-award loyalty points
    award_loyalty_points(cart["user_id"], final_total, order_id)

    # Build summary
    summary = (
        f"Success: Order '{order_id}' processed for user '{cart['user_id']}'. "
        f"Subtotal: ${subtotal:.2f}"
    )
    if applied_code:
        summary += f", Discount ({applied_code}): -${discount_amount:.2f}"
    summary += f", Total: ${final_total:.2f}."

    return summary


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-2.5-flash",
        retry_options=types.HttpRetryOptions(attempts=3),
        api_key=os.environ.get("GEMINI_API_KEY", "AIzaSyD-mock-key-value-12345"),  # type: ignore
    ),
    instruction=(
        "You are a helpful AI shopping assistant for a retail store. You help customers with "
        "their shopping queries, redeem discount codes, award loyalty points, and process cart "
        "checkouts. To process a checkout, ask for the cart ID and optionally a discount code."
    ),
    tools=[redeem_discount_code, award_loyalty_points, process_cart_checkout],
)

app = App(
    root_agent=root_agent,
    name="app",
)
