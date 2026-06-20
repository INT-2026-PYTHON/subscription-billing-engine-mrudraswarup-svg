"""
Proration — calculate credits and charges for mid-cycle plan upgrades.

When a customer upgrades mid-cycle, we:
1. Credit them for unused days on the old plan.
2. Charge them for the remaining days on the new plan.
3. Recalculate taxes on both legs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum
from typing import Optional
from billing_engine.money import Money
from billing_engine.taxes import TaxCalculator, TaxContext


@dataclass(frozen=True)
class ProrationResult:
    """Result of a proration calculation."""
    credit_amount: Money
    charge_amount: Money
    credit_tax: Money
    charge_tax: Money


def compute_proration(
    old_plan_price: Money,
    new_plan_price: Money,
    period_start: date,
    period_end: date,
    switch_date: date,
    tax_calc: TaxCalculator,
    tax_context: TaxContext,
) -> ProrationResult:
    """Compute proration for mid-cycle plan changes."""
    if old_plan_price.currency != new_plan_price.currency:
        raise ValueError(f"Currency mismatch: {old_plan_price.currency} vs {new_plan_price.currency}")
    
    if not (period_start <= switch_date <= period_end):
        raise ValueError(f"Switch date {switch_date} must be in [{period_start}, {period_end}]")
    
    total_days = (period_end - period_start).days
    remaining_days = (period_end - switch_date).days
    
    if remaining_days == 0:
        zero = Money("0", old_plan_price.currency)
        return ProrationResult(zero, zero, zero, zero)
    
    # Use Decimal division to avoid float issues
    ratio = Decimal(remaining_days) / Decimal(total_days)
    
    # Calculate unrounded base amounts for tax calculation
    credit_base_unrounded = old_plan_price * ratio
    charge_base_unrounded = new_plan_price * ratio
    
    # Calculate taxes on unrounded bases to get proper precision
    credit_breakdown = tax_calc.apply(credit_base_unrounded, tax_context)
    charge_breakdown = tax_calc.apply(charge_base_unrounded, tax_context)
    
    # Round the base amounts for the return values
    credit_base = credit_base_unrounded.rounded()
    charge_base = charge_base_unrounded.rounded()
    
    return ProrationResult(
        credit_base,
        charge_base,
        credit_breakdown.total,
        charge_breakdown.total,
    )


# Day 4 stretch: implement upgrade_subscription() with compute_proration()
