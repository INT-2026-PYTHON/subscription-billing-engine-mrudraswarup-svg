"""
PercentageDiscount — e.g., 20% off the subtotal.

Examples:
    PercentageDiscount(Decimal("0.20")).apply(Money(1000, "INR"), ctx)  ->  Money(200, "INR")
    PercentageDiscount(Decimal("1.00")).apply(Money(500, "INR"), ctx)   ->  Money(500, "INR")  # 100% off
"""

from decimal import Decimal

from billing_engine.money import Money
from billing_engine.discounts.base import Discount, DiscountContext


class PercentageDiscount(Discount):
    def __init__(self, percentage: Decimal) -> None:
        if not isinstance(percentage, Decimal):
            raise TypeError(f"Expected Decimal, got {type(percentage).__name__}")
        if percentage < 0 or percentage > 1:
            raise ValueError(f"Percentage must be between 0 and 1, got {percentage}")
        self.percentage = percentage

    def apply(self, subtotal: Money, context: DiscountContext) -> Money:
        discount_amount = subtotal * self.percentage
        # Cap at subtotal (though it shouldn't exceed by design)
        if discount_amount > subtotal:
            return subtotal
        return discount_amount.rounded()
