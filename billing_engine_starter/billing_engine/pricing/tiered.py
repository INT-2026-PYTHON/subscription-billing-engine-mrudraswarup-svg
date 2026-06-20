"""
TieredPricing — different price per unit depending on the tier the quantity falls into.

This is the "cumulative" / "stacked" tier model, NOT the "volume" model:
    Tiers: [(0, 1000, ₹2.00), (1000, 5000, ₹1.50), (5000, None, ₹1.00)]
    Quantity = 6000:
        First 1000 units  @ ₹2.00 = ₹2000
        Next  4000 units  @ ₹1.50 = ₹6000
        Last  1000 units  @ ₹1.00 = ₹1000
        ------------------------------------
        Total                     = ₹9000

A tier with `to_units = None` is the open-ended top tier.

Tier boundaries are HALF-OPEN on the right: a tier (from, to, price)
covers units strictly less than `to` (i.e. [from, to)).
"""

from dataclasses import dataclass
from typing import Optional

from billing_engine.money import Money
from billing_engine.pricing.base import PricingStrategy


@dataclass(frozen=True)
class Tier:
    from_units: int
    to_units: Optional[int]   # None means "unlimited" / open-ended
    unit_price: Money


class TieredPricing(PricingStrategy):
    """Charges across multiple price tiers based on cumulative quantity."""

    def __init__(self, tiers: list[Tier]) -> None:
        # Validate tiers is not empty
        if not tiers:
            raise ValueError("TieredPricing requires at least one tier")
        
        # Validate contiguity: each tier's to_units should match next tier's from_units
        for i in range(len(tiers) - 1):
            if tiers[i].to_units != tiers[i + 1].from_units:
                raise ValueError(
                    f"Tiers must be contiguous: tier {i} ends at {tiers[i].to_units} "
                    f"but tier {i + 1} starts at {tiers[i + 1].from_units}"
                )
        
        # Validate only the last tier has to_units as None
        for i in range(len(tiers) - 1):
            if tiers[i].to_units is None:
                raise ValueError(
                    f"Only the last tier can have to_units = None, "
                    f"but tier {i} does"
                )
        
        if tiers[-1].to_units is not None:
            raise ValueError("The last tier must have to_units = None (open-ended)")
        
        # Validate all unit_prices have the same currency
        first_currency = tiers[0].unit_price.currency
        for i, tier in enumerate(tiers):
            if tier.unit_price.currency != first_currency:
                raise ValueError(
                    f"All tier prices must have the same currency, "
                    f"but tier {i} has {tier.unit_price.currency} "
                    f"instead of {first_currency}"
                )
        
        self.tiers = tiers

    def calculate(self, quantity: int) -> Money:
        if quantity < 0:
            raise ValueError(f"Quantity cannot be negative, got {quantity}")
        
        currency = self.tiers[0].unit_price.currency
        total = Money.zero(currency)
        
        for tier in self.tiers:
            if quantity <= tier.from_units:
                # No units fall into this tier or any above
                break
            
            # Calculate how many units of this tier to charge for
            if tier.to_units is None:
                # Open-ended tier: all remaining units from from_units to quantity
                tier_end = quantity
            else:
                # Bounded tier: from from_units to to_units (or less if quantity < to_units)
                tier_end = min(quantity, tier.to_units)
            
            units_in_tier = tier_end - tier.from_units
            if units_in_tier > 0:
                tier_charge = tier.unit_price * units_in_tier
                total = total + tier_charge
        
        return total
