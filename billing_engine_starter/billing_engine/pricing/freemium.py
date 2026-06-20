"""
Freemium — first N units are free, overage delegated to another strategy.

This is a great example of COMPOSITION: Freemium HAS-A inner PricingStrategy
rather than IS-A specific kind of pricing.

Example: 1000 free API calls per month, then ₹0.50 per call (UsageBased).
"""

from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy


class Freemium(PricingStrategy):
    """Returns 0 for quantity <= free_quota, else delegates overage to inner strategy."""

    def __init__(self, free_quota: int, overage_strategy: PricingStrategy) -> None:
        if free_quota < 0:
            raise ValueError(f"free_quota cannot be negative, got {free_quota}")
        if not isinstance(overage_strategy, PricingStrategy):
            raise TypeError(
                f"overage_strategy must be a PricingStrategy, "
                f"got {type(overage_strategy).__name__}"
            )
        self.free_quota = free_quota
        self.overage_strategy = overage_strategy

    def calculate(self, quantity: int) -> Money:
        # Get the currency from the inner strategy
        currency = self.overage_strategy.calculate(0).currency
        
        if quantity <= self.free_quota:
            return Money.zero(currency)
        
        # Delegate the overage to the inner strategy
        overage = quantity - self.free_quota
        return self.overage_strategy.calculate(overage)
