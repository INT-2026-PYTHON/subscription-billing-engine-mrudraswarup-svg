"""
Proration helper used by BillingCycle upgrades.

Computes the credit and charge for leaving one plan mid-period and
switching to another plan for the remaining days in the current billing
cycle. Taxes are calculated separately for the credit and charge legs.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext


@dataclass(frozen=True)
class ProrationResult:
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
    if switch_date < period_start or switch_date > period_end:
        raise ValueError("switch_date must be within the billing period")
    if old_plan_price.currency != new_plan_price.currency:
        raise ValueError("Currency mismatch between old and new plan prices")

    total_days = (period_end - period_start).days
    if total_days <= 0:
        raise ValueError("Invalid billing period")

    remaining_days = (period_end - switch_date).days
    ratio = Decimal(remaining_days) / Decimal(total_days)

    credit_amount = Money(old_plan_price.amount * ratio, old_plan_price.currency).rounded()
    charge_amount = Money(new_plan_price.amount * ratio, new_plan_price.currency).rounded()

    credit_tax = tax_calc.apply(credit_amount, tax_context).total
    charge_tax = tax_calc.apply(charge_amount, tax_context).total

    return ProrationResult(
        credit_amount=credit_amount,
        charge_amount=charge_amount,
        credit_tax=credit_tax,
        charge_tax=charge_tax,
    )
